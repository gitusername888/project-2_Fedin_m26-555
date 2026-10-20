import re


def parse_condition_string(condition: str) -> dict:
    """
    Парсит строку вида: "age = 28" или "name = 'Alice'" 
    в словарь {'age': 28, 'name': 'Alice'}
    Требование: строковые значения должны быть в кавычках.
    Поддерживаемые кавычки: одинарные или двойные.
    """
    result = {}
    # Ищем пары key = value, 
    # где value может быть числом, true/false или строкой в кавычках
    pattern = r'(\w+)\s*=\s*(?:(true|false)|(-?\d+)|(["\'])(.*?)\4)'
    matches = re.findall(pattern, condition)

    for match in matches:
        key = match[0]
        bool_val = match[1]
        int_val = match[2]
        quote_char = match[3]
        str_val = match[4]

        if bool_val:
            value = bool_val.lower() == "true"
        elif int_val:
            value = int(int_val)
        elif quote_char:
            # str_val уже без кавычек
            value = str_val
        else:
            continue
        result[key] = value
    return result