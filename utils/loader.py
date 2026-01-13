# utils/loader.py
import json
from typing import List
from models.medication import Medication

def load_knowledge_pack(file_path: str = "knowledge/rxlens_knowledge_pack.json") -> List[Medication]:
    with open(file_path, 'r') as f:
        data = json.load(f)
    return [Medication(**item) for item in data]