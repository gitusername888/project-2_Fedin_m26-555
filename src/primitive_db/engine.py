#!/usr/bin/env python3
import shlex
from typing import Optional
from .utils import load_metadata, save_metadata
from .core import (create_table, drop_table, 
list_tables, insert, select, update, delete, ALLOWED_TYPES)
from .parser import parse_condition_string
from prettytable import PrettyTable

METADATA_FILE = "db_meta.json"

def welcome() -> None:
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")

def print_help():
    """Prints the help message for the current mode."""
   
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
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

def run() -> None:
    welcome()
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break
        if not user_input:
            continue

        try:
            args = shlex.split(user_input)
        except ValueError as e:
            print(f"Ошибка разбора команды: {e}")
            print("Не используйте незакрытые кавычки. Пример: insert users Alice 25 true")
            continue

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
                print("Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            table_name = args[1]
            columns = args[2:]
            """if columns not in list(ALLOWED_TYPES) :
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue"""
            metadata = create_table(metadata, table_name, columns)
            save_metadata(METADATA_FILE, metadata)
        elif command == "drop_table":
            if len(args) != 2:
                print("Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            table_name = args[1]
            metadata = drop_table(metadata, table_name)
            save_metadata(METADATA_FILE, metadata)
        elif command == "insert":
            if len(args) < 2:
                print("Формат: insert <table> <value1> [value2] ... (без ID)")
                continue
            table_name = args[1]
            values = args[2:]
            try:
                insert(metadata, table_name, values)
                print(f"Запись в таблицу '{table_name}' добавлена.")
            except Exception as e:
                print(f"Ошибка insert: {e}")
        elif command == "select":
            if len(args) < 2:
                print("Формат: select <table> [where <condition>]")
                continue
            table_name = args[1]
            where_clause: Optional[dict] = None
            if len(args) >= 3 and args[2].lower() == "where":
                condition_str = " ".join(args[3:])
                try:
                    where_clause = parse_condition_string(condition_str)
                except Exception as e:
                    print(f"Ошибка парсинга условия: {e}")
                    continue
            try:
                table_data = select(load_table_data(table_name), where_clause)
                render_table(table_data)
            except Exception as e:
                print(f"Ошибка select: {e}")
        elif command == "update":
            if len(args) < 6 or args[2].lower() != "set" or "where" not in args:
                print("Формат: update <table> set <key=val ...> where <key=val ...>")
                print('Пример: update users set age=30 where name="Alice"')
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
            where_str = " ".join(args[where_index + 1:])

            try:
                set_clause = parse_condition_string(set_str)
                where_clause = parse_condition_string(where_str)
            except Exception as e:
                print(f"Ошибка парсинга условий: {e}")
                continue

            try:
                table_data = load_table_data(table_name)
                updated_data = update(table_data, set_clause, where_clause)
                save_table_data(table_name, updated_data)
                print(f"Записи в таблице '{table_name}' обновлены.")
            except Exception as e:
                print(f"Ошибка update: {e}")
        elif command == "delete":
            if len(args) < 4 or args[2].lower() != "where":
                print("Формат: delete <table> where <key=val ...>")
                print('Пример: delete users where age=25')
                continue

            table_name = args[1]
            condition_str = " ".join(args[3:])

            try:
                where_clause = parse_condition_string(condition_str)
            except Exception as e:
                print(f"Ошибка парсинга условия: {e}")
                continue

            try:
                table_data = load_table_data(table_name)
                filtered_data = delete(table_data, where_clause)
                if len(filtered_data) < len(table_data):
                    save_table_data(table_name, filtered_data)
                    print(f"Записи из таблицы '{table_name}' удалены.")
                else:
                    print("Записей, соответствующих условию, не найдено — ничего не удалено.")
            except Exception as e:
                print(f"Ошибка delete: {e}")
        else:
            print(f"Функции {command} нет. Попробуйте снова.")


