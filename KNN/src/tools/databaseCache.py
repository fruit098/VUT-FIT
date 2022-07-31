import redis
import os
from src import config
import numpy as np
import cv2
import random
import torch
from PIL import Image
from torchvision import transforms


class DatabaseCache():
    def __init__(self, required_image_size=256, dataset_type=None, azure=False):
        if dataset_type == "TRAIN":
            req_db = 0
        elif dataset_type == "VALIDATE":
            req_db = 1
        elif dataset_type == "TEST":
            req_db = 2
        else:
            req_db = 3

        if azure:
            self.redis = redis.Redis(host="knn-redis.redis.cache.windows.net", port = 6380, db=req_db, password="Q9aeNx+E1IJkMZceKOLFJ5ZQT7KXxT6AL0WfzMwFkW0=", ssl=True)
            connect = self.redis.ping()
            print("AZURE server: ", connect)
        else:
            self.redis = redis.Redis()

        self.required_image_size = required_image_size
        self.next_index = 0
        self.dataset_type = dataset_type

    def index_required_scenarios(self, scenarios):
        pipeline = self.redis.pipeline()

        for scenario in scenarios:
            scenario_folder = os.path.join(config.DETECTIONS_OUTPUT_FOLDER, scenario)
            # camera_list = os.listdir(scenario_folder)
            camera_list = config.CAMERAS_PER_SCENARIO[scenario]

            for camera in camera_list:
                print(f"{camera}: ", end="")
                camera_folder = os.path.join(scenario_folder, camera)
                images = os.listdir(camera_folder)

                for image_name in images:
                    car_id = image_name.split("_")[0]
                    image_path = os.path.join(camera_folder, image_name)
                    image = cv2.imread(image_path, 1)

                    resized_image = cv2.resize(image, (self.required_image_size, self.required_image_size))
                    status, image_buffer = cv2.imencode(config.IMG_FORMAT, resized_image)
                    bytes_image = image_buffer.tobytes()

                    key_value = camera + "_" + car_id
                    pipeline.sadd(key_value, bytes_image)
            
                pipeline.execute()
                print(f"OK")
            
            self.union_scenarios_by_id(scenario)        ## Creates id_{number} union sets addition to Cxx_ID indexes

    def union_scenarios_by_id(self, scenario):
        """ Creates additional keys for images in redis.
            New key is in format = id_{number}: [string_images]
        """
        cameras = config.CAMERAS_PER_SCENARIO[scenario]
        ids = list()

        for camera in cameras:
            key = f"{camera}_*"
            keys = self.redis.keys(key)
            keys_ids = [key.decode().split("_")[1] for key in keys]
            ## Union ids
            ids = list(set(ids) | set(keys_ids))
        
        for car_id in ids:
            key = f"c*_{car_id}"
            id_keys = [key.decode() for key in self.redis.keys(key)]
            self.redis.sunionstore(f"id_{car_id}", id_keys)

    def store_images(self):
        ''' Stores all images created from specified dataset
            Dataset_type = TRAIN/TEST/VALIDATE/None(all datasets)
        '''
        if self.dataset_type == "TRAIN":
            required_scenarios = config.TRAIN_SCENARIOS
        elif self.dataset_type == "VALIDATE":
            required_scenarios = config.VALIDATE_SCENARIOS
        elif self.dataset_type == "TEST":
            required_scenarios = config.TEST_SCENARIOS
        else:
            required_scenarios = config.TEST_SCENARIOS + config.TRAIN_SCENARIOS + config.VALIDATE_SCENARIOS

        self.index_required_scenarios(required_scenarios)


    def string_to_image(self, image_str):
        ''' Converts byte string of image into numpy image format '''
        nparr = np.frombuffer(image_str, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        return img_np

    def id_random_image(self, id, number=1, preprocess=None):
        if preprocess is None:
            preprocess = transforms.ToTensor()

        if isinstance(id, torch.Tensor):
            id = int(id)
        req_id_keys = self.redis.keys(f"*_{id}")
        id_random_camera = random.choice(req_id_keys)

        image_str = self.redis.srandmember(id_random_camera, number=number)
        imgs = []
        for img in image_str:
            image = self.string_to_image(img)
            image = Image.fromarray(image)
            image = preprocess(image)
            imgs.append(image)

        return torch.stack(imgs)

    def exclude_id_random_image(self, ids, size, preprocess=None):
        if preprocess is None:
            preprocess = transforms.ToTensor()

        exclude_id_keys = []

        for car_id in ids:
            if isinstance(car_id, torch.Tensor):
                car_id = int(car_id)
            exclude_id_keys.append(self.redis.keys(f"*_{car_id}"))

        all_keys = self.redis.keys("*")

        possible_keys = [x for x in all_keys if x not in exclude_id_keys]

        keys = random.choices(possible_keys, k=size)
        images = []

        for key in keys:
            image_str = self.redis.srandmember(key)
            image = self.string_to_image(image_str)
            image = Image.fromarray(image)
            processed_img = preprocess(image)

            images.append(processed_img)

        return torch.stack(images)



    def id_random_by_tuple(self, ids, preprocess):
        transform = transforms.ToTensor()

        imgs = []

        for car_id in ids:
            if isinstance(car_id, torch.Tensor):
                car_id = int(car_id)
            req_id_keys = self.redis.keys(f"*_{car_id}")
            id_random_camera = random.choice(req_id_keys)
            image_str = self.redis.srandmember(id_random_camera)
            image = self.string_to_image(image_str)
            image = Image.fromarray(image)
            image = preprocess(image)

            imgs.append(image)

        return torch.stack(imgs)


    def get_all_keys(self):
        return self.redis.keys("*")

    def get_all_dataset(self, camera=None, id=None):
        if camera is None and id is None:
            # Get all images from redis
            all_keys = self.redis.keys("*")
        elif camera is not None and id is not None:
            # Get all images on concrete camera with id
            all_keys = self.redis.keys(f"{camera}_{id}")

        elif camera is None:
            # Get all images from all cameras with id
            all_keys = self.redis.keys(f"*_{id}")
        else:
            # Get all cars images from specified cameras
            all_keys = self.redis.keys(f"{camera}_*")


        random.shuffle(all_keys)

        for key in all_keys:
            key_images = self.redis.smembers(key)

            for image in key_images:
                car_id = key.decode().split("_")[1]
                yield (car_id, self.string_to_image(image))


    def get_dataset_size(self, camera, id):
        if camera is None and id is None:
            all_keys = self.redis.keys("*")
        elif camera is None:
            all_keys = self.redis.keys(f"*_{id}")
        elif id is None:
            all_keys = self.redis.keys(f"{camera}_*")

        counter = 0
        for key in all_keys:
            counter += self.redis.scard(key)

        return counter

    def empty_storage(self):
        number_of_keys = self.redis.keys("*")

        if len(number_of_keys) == 0:
            return True

        return False

class RedisDataset(torch.utils.data.Dataset):
    def __init__(self, camera=None, id=None, dataset_type=None, transform=None, azure=False,):
        super(RedisDataset).__init__()
        self.length = 200
        self.db_cache = DatabaseCache(dataset_type=dataset_type, azure=azure)

        self.dataset_generator = self.db_cache.get_all_dataset(camera=camera, id=id)

        self.length = self.db_cache.get_dataset_size(camera, id)
        # self.all_keys = self.db_cache.get_all_keys()

        self.anchors_id = []

        if transform is None:
            self.transform = transforms.ToTensor()
        else:
            self.transform = transform

        print("Size of dataset: ", self.length)


    def __getitem__(self, index):
        anchor_image_id, anchor_image = next(self.dataset_generator)

        # self.anchors_id.append(anchor_image_id)
        # pos_image = self.db_cache.id_random_image(anchor_image_id)

        # negative_keys = self.all_keys[:]
        # negative_keys.remove(anchor_image_id)
        # neg_image = self.db_cache.id_random_image(random.choice(negative_keys))

        anchor_image = Image.fromarray(anchor_image)
        # pos_image = Image.fromarray(pos_image)
        # neg_image = Image.fromarray(neg_image)


        anchor_image = self.transform(anchor_image)
        # pos_image = self.transform(pos_image)
        # neg_image = self.transform(neg_image)

        return [anchor_image_id, anchor_image]

    def __len__(self):
        return self.length


def show_image(image):
    ''' Testing function for displaying images '''
    cv2.imshow('image', image)
    k = cv2.waitKey()
    if k==27:    # Esc key to stop
        return

if __name__ == "__main__":
    db_manager = DatabaseCache(dataset_type="TRAIN", azure=False)

    #db_manager.union_scenarios_by_id("S01")
    ## Stores all datasets into redis DB
    db_manager.store_images()

    ## Generate images by id
    ## Returns image from any camera with MTMC IDs

    # image_1_generator = db_manager.id_object_generator("1")
    # for i in range(3):
    #       image = next(image_1_generator)
    #       show_image(image)


    # # Get random images by id
    # images = db_manager.id_random_images("1", 2)

    # for image in images:
    #     show_image(image)

    # train_dataset = db_manager.get_all_dataset()
    # image = next(train_dataset)
    # show_image(image)
