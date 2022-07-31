import redis
import random
from torch.utils import data
from torch.utils.data import IterableDataset, dataset
import cv2
import numpy as np
import torch
from torchvision import transforms
from PIL import Image

class BatchProvider(IterableDataset):
    """ Batch provider for online triplet mining loss functions implementation """
    def __init__(self, batch_size=16, preprocess=transforms.ToTensor(), K=4, dataset_type="TRAIN"):
        super(BatchProvider).__init__()
        self.ids_cursor = {}                # Dictionary for Redis cursor to each id_{number}
        # Batch size B = K*P, where 
        #           K is number of picture per ID
        #           P is number of different IDs inside batch       
        #           Set Batch size = x^2    
        self.batch_size = batch_size        # Sets number of images inside each batch
        self.K = K                          # Batch B = K*P 
        self.preprocess = preprocess        # Preprocess function for image preprocessing

        self._create_redis(dataset_type)    # Redis connection
        self._get_all_ids()                 # Gets all ids from stored dataset

    def __iter__(self):
        """ Used by pytorch data_loader for loading iterable dataset """
        if len(self.ids_cursor) < self.K:
            # No more possible triplets combinations
            # End of dataset, return empty iterator
            return iter([])
        
        P = int(self.batch_size / self.K)   # K is most of the time K = 4 
        batch, ids = self.get_batch(P)  
        self.labels = ids                   # Store lastly created batch ids 

        return iter(batch)
    
    def _create_redis(self, dataset_type):
        if dataset_type == "TRAIN":
            req_db = 0
        elif dataset_type == "VALIDATE":
            req_db = 1
        elif dataset_type == "TEST":
            req_db = 2
        else:
            req_db = 3


        self.redis = redis.Redis(db=req_db)

    def get_last_iter_labels(self):
        """ Returns lastly created batch ids(labels) for each batch image """
        labels = list(map(int, self.labels))
        return labels

    def _get_all_ids(self):
        """ Reads all ids from Redis storage to set cursor dictionary """
        all_id_keys = self.redis.keys("id_*")
        ids = [ id_key.decode() for id_key in all_id_keys ]

        for id in ids:
            self.ids_cursor[id] = -1

    def get_batch(self, P, K=4):
        """ Requests batch from redis storage and stores new cursor for IDs """
        keys = list(self.ids_cursor.keys())
        selected_keys = random.choices(keys, k=P)   # Choose P keys from database

        batch_images_str = []
        batch_ids = []

        for selected_key in selected_keys:
            """ Get images from selected keys and store new cursor to this IDs """ 
            key_cursor = 0 if self.ids_cursor[selected_key] == -1 else self.ids_cursor[selected_key]
            key_cursor, images = self.redis.sscan(selected_key, key_cursor, count=K)
            self.ids_cursor[selected_key] = key_cursor
            
            car_id = selected_key.split("_")[1]             # Get ID from format id_{car_id}
            batch_images_str = batch_images_str + images[0:K]
            batch_ids = batch_ids + [car_id] * K

        batch = list(map(self.transform_to_tensor, batch_images_str))
        self._remove_empty_cursors()
        
        return batch, batch_ids

    def transform_to_tensor(self,input):
        """ Transform bytes -> string -> PIL Image -> Preprocessed PIL Image """
        input = self.string_to_image(input)
        input = Image.fromarray(input)
        input = self.preprocess(input)

        return input

    def create_batch_tensor(self, batch_list: list):
        """ Creates Tensor [Batch_number, batch_size, 3, heigh, width] from list of Tensors""" 
        squeezed_list = list(map(torch.squeeze, batch_list))
        tensor_batch = torch.stack(squeezed_list)   # Add batch number dimension to Tensor 

        return tensor_batch
    
    def string_to_image(self, image_str):
        ''' Converts byte string of image into numpy image format '''
        nparr = np.frombuffer(image_str, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        return img_np
    
    def _remove_empty_cursors(self):
        """ Removes interal cursors if set has been already fully used """
        empty_cursors = []

        for key in self.ids_cursor:
            if self.ids_cursor[key] == 0:
                empty_cursors.append(key)
        
        for key in empty_cursors:
            self.ids_cursor.pop(key)
