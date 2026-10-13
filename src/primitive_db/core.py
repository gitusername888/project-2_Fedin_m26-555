from typing import Any, Dict, List, Tuple, Optional
from .utils import load_table_data, save_table_data

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

# --- CRUD ---

def _get_schema_columns(metadata: Dict[str, Any], table_name: str):
    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")
    cols = metadata[table_name]["columns"]
    # Возвращаем список (name, type) без ID на позиции 0
    return cols

def _cast_value(value: Any, expected_type: str):
    """Приводит значение к ожидаемому типу, учитывая bool как особый случай."""
    if expected_type == "int":
        return int(value)
    elif expected_type == "str":
        return str(value)
    elif expected_type == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            v = value.lower()
            if v in ("true", "1", "yes"):
                return True
            elif v in ("false", "0", "no"):
                return False
        # fallback
        return bool(value)
    return value

def insert(metadata: Dict[str, Any], table_name: str, values: List[Any]) -> List[Dict[str, Any]]:
    schema = _get_schema_columns(metadata, table_name)
    # schema[0] — это ID:int, его мы генерируем сами
    expected_count = len(schema) - 1
    if len(values) != expected_count:
        raise ValueError(
            f"Ожидается {expected_count} значений (без ID), передано {len(values)}."
        )

    # Валидация типов
    for i, (val, (col_name, col_type)) in enumerate(zip(values, schema[1:]), start=1):
        try:
            _cast_value(val, col_type)
        except Exception:
            raise ValueError(f"Тип значения '{val}' не соответствует типу '{col_type}' для столбца '{col_name}'.")

    # Загрузка данных
    table_data = load_table_data(table_name)

    # Генерация ID
    ids = [row["ID"] for row in table_data if "ID" in row]
    new_id = (max(ids) + 1) if ids else 1

    row = {"ID": new_id}
    for (col_name, col_type), val in zip(schema[1:], values):
        row[col_name] = _cast_value(val, col_type)

    table_data.append(row)
    save_table_data(table_name, table_data)
    return table_data

def select(table_data: List[Dict], where_clause: Optional[Dict] = None):
    if not where_clause:
        return table_data
    result = []
    for row in table_data:
        match = True
        for k, v in where_clause.items():
            if k not in row or row[k] != v:
                match = False
                break
        if match:
            result.append(row)
    return result

def update(table_data: List[Dict], set_clause: Dict, where_clause: Dict) -> List[Dict]:
    updated = False
    for row in table_data:
        match = all(row.get(k) == v for k, v in where_clause.items())
        if match:
            for k, v in set_clause.items():
                if k in row:
                    row[k] = v
                    updated = True
    if updated:
        # Сохраняем внутри engine, здесь просто возвращаем
        pass
    return table_data

def delete(table_data: List[Dict], where_clause: Dict) -> List[Dict]:
    before_len = len(table_data)
    filtered = [row for row in table_data if not all(row.get(k) == v for k, v in where_clause.items())]
    if len(filtered) < before_len:
        pass  # удаление произошло
    return filtered