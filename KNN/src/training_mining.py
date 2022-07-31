
from torchvision import transforms
from config import device
from losses.batchprovider import BatchProvider
import tools.model_tools as tools
import torch
from model.featureExtractor import FeatureExtractor

from losses.batch_all_loss import BatchAllTripletLoss, HardNegativeMiningTripletLoss

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def train(model, batch_mining="batch_all"):
    model =  tools.load_model(model)
    model.to(device)
    model.train()       # Set model to training mode 
    batchProvider = BatchProvider(batch_size=30, preprocess=preprocess)
    batchLoader = torch.utils.data.DataLoader(batchProvider, num_workers=0)
    
    if batch_mining == "batch_all":
        triplet_loss = BatchAllTripletLoss(margin=1.0)
    elif batch_mining == "hard_negative":
        triplet_loss = HardNegativeMiningTripletLoss(margin=1.0)

    optimizer = torch.optim.Adam(model.parameters(), lr=0.025)

    losses = []
    batch = list(batchLoader)
    batch_index = 0

    while batch:
        labels = batchProvider.get_last_iter_labels()
        batch_tensor = batchProvider.create_batch_tensor(batch).to(device)

        _, embeddings = model(batch_tensor)
        loss = triplet_loss(labels, embeddings)

        if batch_index % 30 == 0:
            print(f"Loss[{batch_index}]: {loss}")
            tools.save_model(model)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        losses.append(loss)
        batch_index += 1

    tools.save_model(model)


if __name__ == "__main__":
    model = FeatureExtractor(["avgpool"])

    train(model, batch_mining="hard_negative")


    



