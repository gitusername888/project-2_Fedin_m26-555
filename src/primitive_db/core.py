from typing import Any, Dict, List, Tuple

ALLOWED_TYPES = {"int", "str", "bool"}

def parse_column_spec(col_spec: str) -> Tuple[str, str]:
    """
    Парсит спецификацию столбца вида 'name:type'.
    Возвращает (name, type).
    """
    if ":" not in col_spec:
        raise ValueError(f"Некорректный формат столбца: {col_spec}. Ожидалось 'name:type'.")
    name, typ = col_spec.split(":", 1)
    name = name.strip()
    typ = typ.strip().lower()
    if not name:
        raise ValueError("Имя столбца не может быть пустым.")
    if typ not in ALLOWED_TYPES:
        raise ValueError(f"Недопустимый тип '{typ}'. Разрешены: {', '.join(ALLOWED_TYPES)}.")
    return name, typ

def create_table(metadata: Dict[str, Any], table_name: str, columns: List[str]) -> Dict[str, Any]:
    """
    Создаёт таблицу:
      - добавляет ID:int в начало списка столбцов;
      - проверяет уникальность имени;
      - валидирует типы;
      - возвращает обновлённые метаданные.
    """
    if table_name in metadata:
        print(f"Ошибка: таблица '{table_name}' уже существует.")
        return metadata
    
        

    parsed_columns = []
    # Добавляем ID:int первым столбцом
    parsed_columns.append(("ID", "int"))

    for col_spec in columns:
        name, typ = parse_column_spec(col_spec)
        parsed_columns.append((name, typ))

    metadata[table_name] = {
        "columns": parsed_columns,
        "rows": []  # Заготовка для строк (пока не используется, но нужна для структуры)
    }
    print(f"Таблица '{table_name}' успешно создана со столбцами: {parsed_columns}")
    return metadata

def drop_table(metadata: Dict[str, Any], table_name: str) -> Dict[str, Any]:
    """Удаляет таблицу из метаданных."""
    if table_name not in metadata:
        print(f"Ошибка: Таблица '{table_name}' не найдена.")
        return metadata
    del metadata[table_name]
    print(f"Таблица '{table_name}' удалена.")
    return metadata


def list_tables(metadata: Dict[str, Any]) -> None:
    """Выводит список всех таблиц и их столбцы."""
    if not metadata:
        print("Таблиц нет.")
        return
    for name, info in metadata.items():
        cols = ", ".join(f"{n}:{t}" for n, t in info["columns"])
        print(f"- {name}: [{cols}]")