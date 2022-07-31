import torch
from torchvision import transforms
from sklearn import metrics
import numpy as np
import matplotlib.pyplot as plt
import random

from src import training
from src import config

preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

data_loader = training.create_triplet_loader(dataset_type="VALIDATE")

EVAL_BATCH_SIZE = 1000
BATCH_SIZE = 16

def eval(model, device):
    cummulated_average_true_p = 0
    cummulated_average_false_p = 0
    count = 1
    first_iter = True
    with torch.no_grad():
        try:
            for anchors_id, batch in data_loader:
                batch = torch.Tensor(batch).to(device)
                _, anchor_embeddings = model(batch)

                index = random.randint(0, BATCH_SIZE-1)
                anchor_embedding = anchor_embeddings[index]
                anchor_id = anchors_id[index]

                _, gt_labels, confidence = training.get_query_prediction(model, anchor_embedding, anchor_id)
                average_true_p = metrics.average_precision_score(gt_labels, confidence)

                if first_iter:
                    gt_labels_all = torch.from_numpy(gt_labels)
                    confidence_all = torch.from_numpy(confidence)
                    first_iter = False
                else:
                    gt_labels_all = torch.cat((gt_labels_all, torch.from_numpy(gt_labels)))
                    confidence_all = torch.cat((confidence_all, torch.from_numpy(confidence)))

                revert_confidence = np.absolute(confidence - 1)
                inverted_gt = np.absolute(gt_labels - 1)
                average_false_p = metrics.average_precision_score(inverted_gt, revert_confidence)

                print("Average precisson for batch: ", average_true_p)
                print("Average precisson for batch: ", average_false_p)
                cummulated_average_true_p += average_true_p
                cummulated_average_false_p += average_false_p
                if count % EVAL_BATCH_SIZE == 0:
                    cummulated_average_true_p = cummulated_average_true_p / EVAL_BATCH_SIZE
                    cummulated_average_false_p = cummulated_average_false_p / EVAL_BATCH_SIZE
                    print("Cummulated precisson true: ", cummulated_average_true_p)
                    print("Cummulated precisson false: ", cummulated_average_false_p)
                    print("mAP : ", (cummulated_average_false_p + cummulated_average_true_p) / 2)
                    break
            count += 1
        finally:
            # prepare plots
            plt.title = "Evaluation metrics"
            fig, [ax_prc, ax_det] = plt.subplots(1, 2, figsize=(11, 5))
            fpr, fnr, thresholds = metrics.det_curve(gt_labels_all, confidence_all)
            precision, recall, thresholds = metrics.precision_recall_curve(gt_labels_all, confidence_all)
            display = metrics.DetCurveDisplay(
                fpr=fpr, fnr=fnr, estimator_name='Triplet Loss'
            )
            display.plot(ax=ax_det, name="Detection Error Trade-off")
            ax_det.set_title('Detection Error Trade-off')
            disp = metrics.PrecisionRecallDisplay(precision=precision, recall=recall)
            disp.plot(ax=ax_prc, name="Precision-Recall Curve")
            ax_prc.set_title('Precision-Recall Curve')
            plt.show()


if __name__ == "__main__":
    device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    model = training.FeatureExtractor(["avgpool"])
    model.load_state_dict(torch.load(config.MODEL_STORE_PATH, map_location=device))
    print("Model loaded")
    model.to(device)
    model.eval()
    eval(model, device)





