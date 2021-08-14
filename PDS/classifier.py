#Author: Andrej Zaujec

import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support

import matplotlib.pyplot as plt
import seaborn as sn

def eval_fingeprints():
    test_set_path = "./test.csv"
    db_set_path = "./db_fp.csv"

    test_set = pd.read_csv(test_set_path)
    db = pd.read_csv(db_set_path)

    gt = list(test_set.pop("app_name"))


    results = pd.merge(test_set, db, how="left", on=["ja3","ja3s","sni"])

    our_prediction = list(map(lambda x: x if type(x) != float else "unknown", list(results["app_name"])))
    labels=["instagram", "tiktok", "medium","gmail", "binance","netflix","blockfolio","kaloricketabulky","twitter","messenger", "unknown"]

    conf_matrix = confusion_matrix(gt, our_prediction, labels=labels)
    precision, recall, fbeta_score, support = precision_recall_fscore_support(gt, our_prediction, average="macro")

    df_cm = pd.DataFrame(conf_matrix)
    sn.set(font_scale=1.4)
    sn.heatmap(df_cm, annot=True)
    plt.show()

    print(f"Precision: {precision}, Recall: {recall}")


if __name__ == "__main__":
    eval_fingeprints()

