import os
import csv
from typing import Dict


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DATASET_PATH = os.path.join(DATA_DIR, "ai_dataset.csv")


def append_result_to_dataset(user_id: int, topic_accuracy: Dict[str, float]) -> None:
    new_file = not os.path.exists(DATASET_PATH)
    fieldnames = ["user_id", "topic", "accuracy"]
    with open(DATASET_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if new_file:
            writer.writeheader()
        for topic, acc in topic_accuracy.items():
            writer.writerow({"user_id": user_id, "topic": topic, "accuracy": acc})


