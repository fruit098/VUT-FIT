import torch
from torchvision import models
from sklearn.neighbors import NearestNeighbors

class FeatureExtractor(torch.nn.Module):
    def __init__(self, output_layers_names):
        super(FeatureExtractor, self).__init__()
        self.model = models.resnet18(pretrained=True)
        self.hooks = []
        self.features = {layer_name: torch.empty(0) for layer_name in output_layers_names}

        for layer_name in output_layers_names:
            if layer_name in self.model._modules.keys():
                layer = self.model._modules[layer_name]
                layer.register_forward_hook(self.extract_layer_output(layer_name))

    def extract_layer_output(self, layer_name):
        def hook(model, input, output):
            self.features[layer_name] = output

        return hook

    def forward(self, input):
        soft = torch.nn.Softmax(1)
        out = soft(self.model(input)).float()

        features = self.features["avgpool"]
        return out, features

    def create_embedding_space(embeddings, radius=3.5):
        classifier = NearestNeighbors(radius=radius)
        classifier.fit(embeddings)

        return classifier

