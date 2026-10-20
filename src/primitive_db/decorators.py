import time
from functools import wraps
from typing import Any, Callable


def handle_db_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден."
                  " Возможно, база данных не инициализирована.")
        except KeyError as e:
            print(f"Ошибка: Таблица или столбец {e} не найден.")
        except ValueError as e:
            print(f"Ошибка валидации: {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
    return wrapper


def confirm_action(action_name: str):
    """
    Декоратор с аргументом: запрашивает подтверждение у пользователя.
    Если ввод != 'y', функция не выполняется.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            text = (f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')
            confirm = input(text).strip().lower()
            if confirm != "y":
                print("⚠️ Операция отменена.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def log_time(func: Callable) -> Callable:
    """
    Замеряет время выполнения функции через time.monotonic().
    Выводит: Функция <имя> выполнилась за X.XXX секунд.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.monotonic()
        result = func(*args, **kwargs)
        end = time.monotonic()
        elapsed = end - start
        print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд.")
        return result
    return wrapper

def create_cacher() -> Callable[[str, Callable[[], Any]], Any]:
    """
    Возвращает функцию cache_result(key, value_func).
    Кэш (словарь) хранится в замыкании.
    """
    cache = {}

    def cache_result(key: str, value_func: Callable[[], Any]) -> Any:
        if key in cache:
            return cache[key]

        value = value_func()
        cache[key] = value
        return value

    return cache_result

