import json
import os
from pathlib import Path

METADATA_FILE = "db_meta.json"
DATA_DIR = "data"

os.makedirs(DATA_DIR, exist_ok=True)

def load_metadata(filepath: str | Path | None = None) -> dict:
    "Загружает данные из JSON-файла."
    " Если файл не найден, возвращает пустой словарь."
    if filepath is None:
        filepath = METADATA_FILE
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_metadata(filepath: str | Path, data: dict) -> None:
    """Сохраняет переданные данные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_table_file_path(table_name: str) -> Path:
    return Path(DATA_DIR) / f"{table_name}.json"

def load_table_data(table_name: str):
    path = get_table_file_path(table_name)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Гарантируем список
            return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_table_data(table_name: str, data):
    path = get_table_file_path(table_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)