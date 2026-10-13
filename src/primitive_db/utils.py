import json
from pathlib import Path

METADATA_FILE = "db_meta.json"

def load_metadata(filepath: str | Path | None = None) -> dict:
    """Загружает данные из JSON-файла. Если файл не найден, возвращает пустой словарь."""
    if filepath is None:
        filepath = METADATA_FILE
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        # Если файл битый — возвращаем пустой словарь, чтобы не ломать систему
        return {}

def save_metadata(filepath: str | Path, data: dict) -> None:
    """Сохраняет переданные данные в JSON-файл."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)