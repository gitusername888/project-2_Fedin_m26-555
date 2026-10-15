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
        if isinstance(value, int):
            return value
        if not isinstance(value, str):
            raise ValueError(f"Для типа int ожидается строка или число, получено: {value!r}")
        # Убираем возможные пробелы
        s = value.strip()
        # Если вдруг случайно попала запятая как разделитель тысяч — удаляем её
        # Но только если это выглядит как число с запятой: "1,000" -> 1000
        if "," in s and s.replace(",", "").isdigit():
            s = s.replace(",", "")
        try:
            return int(s)
        except ValueError:
            raise ValueError(f"Не удалось преобразовать '{value}' в int.")
    elif expected_type == "str":
        return str(value[1:-1])
    elif expected_type == "bool":
        if isinstance(value, bool):
            return value
        if not isinstance(value, str):
            raise ValueError(f"Для типа bool ожидается строка, получено: {value!r}")

        s = value.strip().lower()

        # Очищаем от окружающих скобок: (true) -> true, (TRUE) -> true
        if s.endswith(")") and len(s) > 2:
            s = s[:-1].strip().lower()

        if s in ("true", "1", "yes"):
            return True
        if s in ("false", "0", "no"):
            return False

        raise ValueError(f"Не удалось интерпретировать '{value}' как bool. Допустимы: true/false, 1/0, yes/no.")

    else:
        return value

def insert(metadata: Dict[str, Any], table_name: str, values: List[Any]) -> int:
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
    id_count = row.get("ID")
    table_data.append(row)
    save_table_data(table_name, table_data)
    return id_count

def select(table_data: List[Dict], where_clause: Optional[Dict] = None):
    if not where_clause:
        return table_data


    result = []
    for row in table_data:
        match = True
        for k, v_where in where_clause.items():
            if k not in row:
                match = False
                break
            v_row = row[k]
            # Строгое сравнение: тип и значение
            if type(v_row) is not type(v_where) or v_row != v_where:
                match = False
                break
        if match:
            result.append(row)
    return result

def update(table_data: List[Dict], set_clause: Dict[str, Any], where_clause: Dict[str, Any]) -> Tuple[List[Dict], List]:
    id_count =[]
    for row in table_data:
        # Проверяем полное совпадение условия WHERE
      
        match = True
        for k, v_where in where_clause.items():
            # Если колонки нет в строке — не совпадение
            if k not in row:
                match = False
                break
            
            v_row = row[k]
            
            
            # Строгое сравнение: типы должны совпадать И значения должны совпадать
            if type(v_row) is not type(v_where) or v_row != v_where:
                match = False
                break
        
            if match:
                # Применяем SET только для совпавших строк
                for k, v_set in set_clause.items():
                    if k in row:
                        row[k] = v_set
                if "ID" in row:
                    id_count.append(row["ID"])    

    return table_data,id_count

def delete(table_data: List[Dict], where_clause: Dict) -> Tuple[List[Dict], List]:
    
    """
    Удаляет строки, строго совпадающие с where_clause.
    Возвращает (оставшиеся_данные, список_ID_удалённых_строк).
    """
    remaining = []
    deleted_ids = []

    for row in table_data:
        # row — это dict, у него есть .get() и ключи
        match = True
        for k, v_where in where_clause.items():
            # Если ключа нет в строке — не совпадение
            if k not in row:
                match = False
                break

            v_row = row[k]
            # Строгое сравнение: тип и значение должны совпадать
            if type(v_row) is not type(v_where) or v_row != v_where:
                match = False
                break

        if match:
            # Строка подходит под WHERE → удаляем (не добавляем в remaining)
            if "ID" in row:
                deleted_ids.append(row["ID"])
            # Можно добавить логирование: print(f"Удалена строка с ID={row['ID']}")
        else:
            # Не подходит → оставляем
            remaining.append(row)

    return remaining, deleted_ids
