import torch
import os
import config

def load_model(model):
    if os.path.exists(config.MODEL_STORE_PATH):
        if config.device == torch.device('cpu'):
            model.load_state_dict(torch.load(config.MODEL_STORE_PATH, map_location=torch.device("cpu")))
        else:
            model.load_state_dict(torch.load(config.MODEL_STORE_PATH))
        
        print("Model loaded from file")

    return model

def save_model(model):
    torch.save(model.state_dict(), config.MODEL_STORE_PATH)
    print("Model has been saved to .pt file")