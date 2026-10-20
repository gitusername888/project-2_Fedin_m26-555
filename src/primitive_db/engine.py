#!/usr/bin/env python3
import shlex
from typing import Optional

from prettytable import PrettyTable

from .core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    load_table_data,
    save_table_data,
    select,
    update,
)
from .decorators import create_cacher, handle_db_errors
from .parser import parse_condition_string
from .utils import load_metadata, save_metadata

METADATA_FILE = "db_meta.json"
cache = create_cacher()



def welcome() -> None:
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> "
    "<столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> insert into <имя_таблицы> values (<значение1>, "
        "<значение2>, ...) - создать запись. \n"
        "<command> select from <имя_таблицы> where <столбец>"
        "= <значение> - прочитать записи по условию. \n"
        "<command> select from <имя_таблицы> - прочитать все записи.\n"
        "<command> update <имя_таблицы> set <столбец1> = <новое_значение1>"
        "where <столбец_условия> = <значение_условия> - обновить запись.\n"
        "<command> delete from <имя_таблицы> where <столбец> = \n"
        "<значение> - удалить запись.\n"
        "<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")

def print_help():
    """Prints the help message for the current mode."""
   
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> insert into <имя_таблицы> values (<значение1>, "
            "<значение2>, ...) - создать запись. \n"
            "<command> select from <имя_таблицы> where <столбец>"
            "= <значение> - прочитать записи по условию. \n"
            "<command> select from <имя_таблицы> - прочитать все записи.\n"
            "<command> update <имя_таблицы> set <столбец1> = <новое_значение1>"
            "where <столбец_условия> = <значение_условия> - обновить запись.\n"
            "<command> delete from <имя_таблицы> where <столбец>"
            " = <значение> - удалить запись.\n"
            "<command> info <имя_таблицы> - вывести информацию о таблице.")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    
    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n") 

def render_table(rows: list[dict]) -> None:
    if not rows:
        print("(пусто)")
        return
    headers = list(rows[0].keys())
    pt = PrettyTable()
    pt.field_names = headers
    for r in rows:
        pt.add_row([r.get(h) for h in headers])
    print(pt)

@handle_db_errors
def run() -> None:
    welcome()
    while True:
        user_input = input("> ").strip()

        if not user_input:
            continue

        try:
            args = shlex.split(user_input)
        except ValueError as e:
            print(f"Ошибка разбора команды: {e}")

        command = args[0].lower() if args else ""

        # Загружаем актуальные метаданные перед каждой операцией
        metadata = load_metadata(METADATA_FILE)

        if command == "exit":
            print("Выход.")
            break
        elif command == "help":
            print_help()
        elif command == "list_tables":
            list_tables(metadata)
        elif command == "create_table":
            if len(args) < 3:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            table_name = args[1]
            columns = args[2:]
            """if columns not in list(ALLOWED_TYPES) :
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue"""
            metadata = create_table(metadata, table_name, columns)
            if metadata is None:
                # handle_db_errors уже вывел понятное сообщение об ошибке
                continue
            save_metadata(METADATA_FILE, metadata)
        elif command == "drop_table":
            if len(args) != 2:
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            table_name = args[1]
            metadata = drop_table(metadata, table_name)
            save_metadata(METADATA_FILE, metadata)
        elif command == "insert":
            if len(args) < 2:
                raise ValueError("Формат не корректный")
                
            table_name = args[2]
            values = args[4:]
            
            id_count = insert(metadata, table_name, values)
            if id_count is None:
                print("Не удалось установить \"ID\"")
            else:
                print(f"Запись с ID={id_count} успешно "
                      f"добавлена в таблицу \"{table_name}\".")

        elif command == "select":
            # 1. Базовая валидация аргументов
            if len(args) < 2:
                print("Ошибка: не указано имя таблицы после select.")
                continue
    
            table_name = args[2]  # args[0] это 'select', значит таблица в args[1]

            # 2. Проверка наличия таблицы в метаданных
            if table_name not in metadata:
                print(f"Ошибка: таблица '{table_name}' не найдена.")
                continue
            current_data = load_table_data(table_name)
            
            # 3. Парсинг условия WHERE (если есть)
            where_clause: Optional[dict] = None
    
            # Ищем часть после "where" в исходной строке ввода
            if "where" in user_input:
                condition_str = user_input[user_input.find("where") + 6:].strip()
                # Замена двойных кавычек на одинарные для удобства парсера 
                condition_str = condition_str.replace('\'', "\"")
                
        
                try:
                    where_clause = parse_condition_string(condition_str)
                except Exception as e:
                    print(f"Ошибка парсинга условия WHERE: {e}")
                    continue
                    

            # 4. Формируем уникальный ключ для кэша
            # sorted нужен, чтобы порядок ключей в словаре не влиял на ключ кэша
            
            key_suffix = str(sorted(where_clause.items())) if where_clause else "ALL"
            cache_key = f"select:{table_name}:{key_suffix}"
        
            # 5. Кэшируем результат вызова select
            # cache должен быть создан один раз при старте: cache = create_cacher()
            try:
                result = cache(
                    cache_key,
                    lambda: select(current_data, where_clause)
                )
            except Exception as e:
                print(f"Ошибка выполнения select : {e}")
                continue

            # 6. Вывод результатов
            print(f"Найдено строк: {len(result)}")
            
                
    
            # Рендерим именно результат (result), а не промежуточную переменную
            render_table(result)            
       
            
        elif command == "update":
            if len(args) < 6 or args[2].lower() != "set" or "where" not in args:
                print("Формат не корректный")

                continue

            table_name = args[1]
            set_start = 3
            where_index = None
            
            for i, a in enumerate(args):
                if a.lower() == "where":
                    where_index = i
                    break

            if where_index is None or where_index <= set_start:
                print("Ошибка формата: ожидается 'set ... where ...'")
                continue

            set_str = " ".join(args[set_start:where_index])
                 
            
            try:
                set_clause = parse_condition_string(set_str)
                where_clause = parse_condition_string(user_input
                        [user_input.find("where")+6:].replace('\"','\''))
            except Exception as e:
                print(f"Ошибка парсинга условий: {e}")
                continue

            
            try:
                id_count =[]
                table_data = load_table_data(table_name)
                updated_data, id_count = update(table_data, set_clause, where_clause)
                save_table_data(table_name, updated_data)
                print(f"Запись с ID={id_count}"
                      f" в таблице \"{table_name}\" успешно обновлена.")
            except Exception as e:
                print(f"Ошибка update: {e}")
        elif command == "delete":


            table_name = args[2]
            condition_str = " ".join(args[3:])

            try:
                where_clause = parse_condition_string(condition_str)
            except Exception as e:
                print(f"Ошибка парсинга условия: {e}")
                continue

            try:
                deleted_ids = []
                table_data = load_table_data(table_name)
                filtered_data, deleted_ids = delete(table_data, where_clause)
                if len(filtered_data) < len(table_data):
                    save_table_data(table_name, filtered_data)
                    print(f"Запись с ID={deleted_ids}"
                          f" успешно удалена из таблицы \"{table_name}\".")
                else:
                    print("Записей, соответствующих "
                          "условию, не найдено — ничего не удалено.")
            except Exception as e:
                print(f"Ошибка delete: {e}")
        elif command == "info":
            if len(args) < 2:
                print("Формат: info <имя_таблицы>")
                print('Пример: info users')
                continue

            table_name = args[1]



            #Загружаем данные, чтобы посчитать количество записей
            try:
                table_data = load_table_data(table_name)
                count = len(table_data)
            except FileNotFoundError:
                print(f"Таблица '{table_name}' не найдена (нет файла данных).")
                continue
            except Exception as e:
                print(f"Ошибка загрузки данных: {e}")
                continue
            print(f"Таблица: {table_name}")
            for table_name, info in metadata.items():
                    cols = ", ".join(f"{n}:{t}" for n, t in info["columns"])

            print(f"Столбцы: {cols}")
            print(f"Количество записей: {count}")

        else:
            print(f"Функции {command} нет. Попробуйте снова.")


