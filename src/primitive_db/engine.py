#!/usr/bin/env python3
import shlex


from primitive_db.utils import load_metadata, save_metadata
from primitive_db.core import create_table, drop_table, list_tables, ALLOWED_TYPES

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

        args = shlex.split(user_input)
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
            if columns != ":" or columns != ALLOWED_TYPES :
                print(f"Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            metadata = create_table(metadata, table_name, columns)
            save_metadata(METADATA_FILE, metadata)
        elif command == "drop_table":
            if len(args) != 2:
                print("Некорректное значение: {user_input}. Попробуйте снова.")
                continue
            table_name = args[1]
            metadata = drop_table(metadata, table_name)
            save_metadata(METADATA_FILE, metadata)
        else:
            print(f"Функции {command} нет. Попробуйте снова.")


