from typing import List, Dict
import json
import re


def normalize_currency(text: str) -> str:
    t = text.replace("，", ",").replace("．", ".")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def load_labelstudio_json(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data
