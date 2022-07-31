import numpy as np
import random
import torch
import os
from torchvision import transforms
from src import config
from config import device
from model.featureExtractor import FeatureExtractor
from tools.databaseCache import DatabaseCache, RedisDataset
from sklearn.neighbors import NearestNeighbors
import tools.model_tools as tools 

BATCH_SIZE = 16
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

db_cache = DatabaseCache(dataset_type="VALIDATE")

def create_triplet_loader(camera=None, id=None, dataset_type="TRAIN"):
    anchor_dataset = RedisDataset(dataset_type=dataset_type, transform=preprocess, camera=camera, id=id)
    anchor_loader = torch.utils.data.DataLoader(anchor_dataset, num_workers=0, batch_size=BATCH_SIZE, shuffle=True)

    return anchor_loader

def create_embedding_space(embeddings, radius=3.5):
    classifier = NearestNeighbors(radius=radius)
    classifier.fit(embeddings)

    return classifier

def create_query(anchor_id, query_size=16):
    positive_size = random.randint(1, query_size - 1) #due to negative_size = 0
    negative_size = query_size - positive_size
    positive_labels = torch.ones(positive_size)
    negative_labels = torch.zeros(negative_size)

    positive_batch = db_cache.id_random_image(anchor_id, positive_size, preprocess)
    negative_batch = db_cache.exclude_id_random_image([anchor_id], negative_size, preprocess)


    query = torch.cat((positive_batch, negative_batch))
    labels = torch.cat((positive_labels, negative_labels))
    print(f"Positives: {positive_size}, Negatives: {negative_size}")
    return query, labels

def get_query_prediction(model, anchor_embedding, anchor_id):
    query, labels = create_query(anchor_id)
    predicted_labels = np.zeros(labels.shape)

    # Create embeddings with given model for re-identification
    query = query.to(device)
    _, query_embeddings = model(query)
    query_embeddings = query_embeddings.cpu()
    anchor_embedding = anchor_embedding.cpu()
    query_embeddings = query_embeddings.detach().numpy().squeeze()
    anchor_embedding = anchor_embedding.detach().numpy()

    embedding_space = create_embedding_space(query_embeddings)
    distances, indexes = embedding_space.radius_neighbors(anchor_embedding.reshape(1,-1))

    # Set predicted logits
    predicted_labels[indexes[0]] = 1

    distances = np.minimum(1/distances[0], np.ones(distances[0].shape[0],np.float))

    final_distances = np.zeros(labels.shape)
    final_distances[indexes[0]] = distances

    return predicted_labels, labels.detach().numpy(), final_distances

def train(model, camera):
    ''' Train method for training given model '''
    model = tools.load_model(model)
    model.to(device)
    model.train()
    data_loader = create_triplet_loader(camera=camera)

    triplet_loss = torch.nn.TripletMarginLoss(margin=1.0)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.025)

    losses = []

    for batch_idx, batch in enumerate(data_loader):
        anchors_id = batch[0]
        anchor_batch =  torch.Tensor(batch[1]).to(device)

        positive_batch = torch.Tensor(db_cache.id_random_by_tuple(anchors_id, preprocess)).to(device)
        negative_batch = torch.Tensor(db_cache.exclude_id_random_image(anchors_id, BATCH_SIZE, preprocess)).to(device)

        _, anchor_embeddings = model(anchor_batch)
        _, positive_embeddings = model(positive_batch)
        _, negative_embeddings = model(negative_batch)

        loss = triplet_loss(anchor_embeddings, positive_embeddings, negative_embeddings)

        if batch_idx % 30 == 0:

            losses.append(loss)
            tools.save_model(model)

            ## Every 30th batch, create query and evaluate query for metrics in training
            index = random.randint(0, BATCH_SIZE-1)
            anchor_embedding = anchor_embeddings[index]
            anchor_id = anchors_id[index]

            pred_labels, gt_labels, distances = get_query_prediction(model, anchor_embedding, anchor_id)
            print(f"{batch_idx}: {loss}")

            model.train()

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    tools.save_model(model)


if __name__ == "__main__":
    feature_extractor = FeatureExtractor(["avgpool"])
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    train(feature_extractor, None)
