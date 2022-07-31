import cv2
import numpy as np
from src import config
import os
import logging as log
from dataclasses import dataclass

class VideoManager():
    '''
        Class for converting videos to sliced images of cars based on previous detection
    '''

    def crop_images_from_frame(self, frame, frame_number, frame_detections):
        cropped_images = {}

        for detection in frame_detections:
            id = int(detection[1])
            left = int(detection[2])
            top = int(detection[3])
            right = int(left + detection[4])
            bottom = int(top + detection[5])

            image_name = f"{id}_{frame_number}"
            cropped_image = frame[top:bottom, left:right]
            cropped_images[image_name] = cropped_image

        return cropped_images


    def store_images(self, det_images, store_path):
        for image in det_images.keys():
            img_path = os.path.join(store_path, image + config.IMG_FORMAT)
            if det_images[image].size != 0:
                cv2.imwrite(img_path, det_images[image])


    def get_video_detections(self, detection_truth):
        ''' Loads file with object detection groundtruth and deletes unused values '''
        detections = np.loadtxt(detection_truth, delimiter=',')
        detections = np.delete(detections, [6,7,8,9], 1)

        return detections


    def crop_video(self, video_path, store_path, detection_truth):
        ''' Opens video as sequence of frames and crops all detected cars with corresponding IDs from detection truth file '''
        capture = cv2.VideoCapture(video_path)
        detections = self.get_video_detections(detection_truth)

        frame_counter = 1
        print(f"storing to: {store_path}")
        while (capture.isOpened()):
            ret, frame = capture.read()

            if not ret:
                break   # Video is at the last frame

            frame_detections = detections[np.where(detections[:,0] == frame_counter)]   # Get detections for current frame number
            car_images = self.crop_images_from_frame(frame, frame_counter, frame_detections)

            if car_images:
                # Some frames may be without cars, skip storing
                self.store_images(car_images, store_path)


            frame_counter += 1

        print(f"{video_path} has been processed!")


    def create_cropped_subdir(self, scenario, camera):
        ''' Creates directories in output path if dont exists '''
        output_dir = os.path.join(config.DETECTIONS_OUTPUT_FOLDER, scenario, camera)

        os.makedirs(output_dir, exist_ok=True)
        return output_dir


    def process_dataset(self, dataset_videos):
        ''' Process all given videos. Crops images from videos and store created images '''
        for video_bundle in dataset_videos:
            images_output_directory = self.create_cropped_subdir(video_bundle.scenario, video_bundle.camera)
            if not images_output_directory:
                log.error(f"Couldn't create output directory for {video_bundle.video_path}")

            self.crop_video(video_bundle.video_path, images_output_directory, video_bundle.detection_truth)


    def get_video_paths(self, dataset_type=None):
        ''' Process all videos in dataset of given type

            @param dataset_type: TRAIN/VALIDATE/TEST/None(All datasets)
        '''
        train_folder = os.path.join(config.BASE_PATH, "train/")
        validate_folder = os.path.join(config.BASE_PATH, "validation/")
        test_folder = os.path.join(config.BASE_PATH, "test/")

        train_videos = self.get_type_videos(train_folder, "TRAIN")
        validate_videos = self.get_type_videos(validate_folder, "VALIDATE")
        test_videos = self.get_type_videos(test_folder, "TEST")

        if dataset_type == "TRAIN":
            return train_videos

        elif dataset_type == "VALIDATE":
            return validate_videos

        elif dataset_type == "TEST":
            return test_videos

        return train_videos + validate_videos + test_videos



    def get_type_videos(self, root_folder, dataset_type):
        ''' Returns paths to given type of dataset videos '''
        video_paths = []

        if dataset_type == "TRAIN":
            scenarios = config.TRAIN_SCENARIOS
            gt_method = config.DETECTION_GT_METHOD_TRAIN
            gt_folder = config.GROUND_TRUTH_FOLDER
        elif dataset_type == "VALIDATE":
            scenarios = config.VALIDATE_SCENARIOS
            gt_method = config.DETECTION_GT_METHOD_VALIDATION
            gt_folder = config.GROUND_TRUTH_FOLDER
        else:
            scenarios = config.TEST_SCENARIOS
            gt_method = config.DETECTION_GT_METHOD_TEST
            gt_folder = config.GROUND_TRUTH_FOLDER_TEST

        for scenario in scenarios:
            scenario_cameras = config.CAMERAS_PER_SCENARIO[scenario]
            scenario_folder = os.path.join(root_folder, scenario)

            for camera in scenario_cameras:
                camera_video_path = os.path.join(scenario_folder, camera, "vdo.avi")
                detection_truth = os.path.join(scenario_folder, camera, gt_folder, gt_method)

                video_bundle = VideoBundle(video_path = camera_video_path, scenario = scenario, camera = camera, detection_truth= detection_truth)
                video_paths.append(video_bundle)

        return video_paths


    def prepare_datasets(self, dataset_type=None):
        ''' Prepare images from datasets videos
            @param dataset_type:Select specific dataset for preparation.
                                If nothing is given, all Train, Test and
                                Validate datasets are prepared
                                TRAIN/VALIDATE/TEST/NONE
        '''
        videos = self.get_video_paths(dataset_type)
        self.process_dataset(videos)


@dataclass
class VideoBundle():
    video_path: str
    scenario: str
    camera: str
    detection_truth: str



if __name__ == '__main__':
    video_manager = VideoManager()

    ## Prepare all videos from train, test and validation datasets
    # video_manager.prepare_datasets()

    ## Prepare only train datasets
    video_manager.prepare_datasets("TRAIN")

    ## Prepare only validate datasets
    # video_manager.prepare_datasets("TEST")
