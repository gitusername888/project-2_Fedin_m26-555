def show_help():
    """Выводит справочную информацию по доступным командам."""
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")

def welcome():
    """
    Выводит приветственное сообщение, справку по командам и запускает
    игровой цикл: принимает команды от пользователя и обрабатывает их.
    """
    print("Первая попытка запустить проект! \n \n***")
    show_help()

    while True:
        command = input("Введите команду: ").strip().lower()

        if not command:
            continue

        if command == "exit":
            print("Выход из программы.")
            break

        elif command == "help":
            print("\n")
            show_help()

        else:
            # Сюда позже можно добавить обработку других команд
            print(f"Некорректная команда {command}")


