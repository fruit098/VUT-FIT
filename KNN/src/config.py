
import os
import torch
### CHANGE AS YOU WISH ###

BASE_PATH = os.environ.get('AI_CITY_CHALLENGE_DATASET_PATH', './')   # Path to downloaded datasets fodler
# DETECTIONS_OUTPUT_FOLDER = './detection'    # Path to output directory of created images
MODEL_STORE_PATH = "./model"
# MODEL_STORE_PATH = "/home/osboxes/Desktop/github/KNN---AI-City-Challenge/src/models/ft_ext_model.pt"
DETECTIONS_OUTPUT_FOLDER = f"{BASE_PATH}/videos_processed"  # Path to output directory of created images

IMG_FORMAT = ".jpg"

### GROUNDTRUTH TEXTFILES NAMES FOR EVERY DATASET TYPE ###
### *test dataset does not have all detection method GT ###

GROUND_TRUTH_FOLDER = "gt"
DETECTION_GT_METHOD_TRAIN = "gt.txt"
DETECTION_GT_METHOD_VALIDATION = "gt.txt"
DETECTION_GT_METHOD_TEST = "mtsc_tnt_mask_rcnn.txt"
GROUND_TRUTH_FOLDER_TEST = "mtsc"
### DATASETS SCENARIOS AND CAMERAS DEFINITIONS ###

TRAIN_SCENARIOS = ["S01", "S03", "S04"]
#VALIDATE_SCENARIOS = ["S02", "S05"]
VALIDATE_SCENARIOS = ["S05",]
TEST_SCENARIOS = ["S06"]

CAMERAS_PER_SCENARIO = {
     "S01": ["c002", "c003", "c004", "c005"],
    #"S01": ["c001"],
    "S03": ["c010", "c011", "c012", "c013", "c014", "c015"],
    "S04": ["c016", "c017", "c018", "c019", "c020", "c021", "c022", "c023", "c024", "c025", "c026", "c027", "c028", "c029", "c030", "c031", "c032", "c033", "c034", "c035", "c036", "c037", "c038", "c039", "c040"],
    "S02": ["c006", "c007", "c008", "c009"],
    "S05": ["c010", "c016", "c017", "c018", "c019", "c020", "c021", "c022", "c023", "c024", "c025", "c026", "c027", "c028", "c029", "c033", "c034", "c035", "c036"],
    "S06": ["c041", "c042", "c043", "c044", "c045", "c046"]
}


device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
