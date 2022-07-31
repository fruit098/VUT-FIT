from tools.databaseCache import DatabaseCache, RedisDataset
import matplotlib.pyplot as plt
import torchvision.models as models
from torchvision import transforms
from PIL import Image
import torch
import numpy as np
import redis
import random
from mpl_toolkits.axes_grid1 import ImageGrid
from model.featureExtractor import FeatureExtractor
import os
from src import config
import csv
import signal
import sys

def signal_handler(sig, frame):
    torch.save(feature_extractor.state_dict(), config.MODEL_STORE_PATH)
    print("EXITING AND SAVED STATE OF MODEL")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

BATCH_SIZE = 64

db_cache = DatabaseCache(dataset_type="TRAIN")
anchor_dataset = RedisDataset(dataset_type="TRAIN", transform=preprocess, camera="c001")
anchor_loader = torch.utils.data.DataLoader(anchor_dataset, num_workers=0, batch_size=BATCH_SIZE, shuffle=True)


if db_cache.empty_storage():
    ## Redis storage is empty
    print("Emtpy storage")
    db_cache.store_images()

feature_extractor = FeatureExtractor(["avgpool"])

if os.path.exists(config.MODEL_STORE_PATH):
    print("Loading stored state of model")
    feature_extractor.load_state_dict(torch.load(config.MODEL_STORE_PATH))

triplet_l = torch.nn.TripletMarginWithDistanceLoss()
cross_l = torch.nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(feature_extractor.parameters(), lr=0.025)

losses = []
id_embeddings = []

for batch_idx, batch in enumerate(anchor_loader):
    anchors_id, anchors_batch = batch

    positives_batch = db_cache.id_random_by_tuple(anchors_id, preprocess)
    negatives_batch = db_cache.exclude_id_random_image(anchors_id, BATCH_SIZE, preprocess)

    result, anchors_embeddings = feature_extractor(anchors_batch)
    _, positives_embeddings = feature_extractor(positives_batch)
    _, negatives_embeddings = feature_extractor(negatives_batch)


    for idx, anchor_id in enumerate(anchors_id):
        id_embedding = (anchor_id, anchors_embeddings[idx].detach().numpy())
        id_embeddings.append(id_embedding)

    anchor_dataset.anchors_id = []

    gt = torch.zeros(result.shape[0])
    anchors_id = [int(anchor_id) for anchor_id in anchors_id]
    for i, j in enumerate(anchors_id):
        gt[i] = j

    triplet_loss = triplet_l(anchors_embeddings, positives_embeddings, negatives_embeddings)
    cross_loss = cross_l(result,gt.long())
    total_loss = 0.5 * (triplet_loss + cross_loss)

    if batch_idx % 30 == 0:
        losses.append((batch_idx, total_loss))
        print(f"{batch_idx}: {total_loss}")


    optimizer.zero_grad()
    triplet_loss.backward()
    optimizer.step()

with open('embedding.csv','w') as f:
    writer = csv.writer(f)
    writer.writerows(id_embeddings)



torch.save(feature_extractor.state_dict(), config.MODEL_STORE_PATH)
print("Model has been saved to .pt file")
