import sqlite3
from bcrypt import hashpw, gensalt
from data.Users import User


def create_database(db_name):
    # Создаем подключение к базе данных (если базы данных нет, она будет создана)
    conn = sqlite3.connect(db_name)

    # Создаем курсор для выполнения SQL-запросов
    cursor = conn.cursor()

    # Создаем таблицу с указанными полями
    cursor.execute('''
        CREATE TABLE Users IF NOT EXISTS (
    FIO          TEXT,
    Login        TEXT    UNIQUE,
    h_password TEXT,
    role         TEXT,
    status_str   TEXT,
    status_int   INTEGER
);
    ''')

    # Сохраняем изменения и закрываем соединение
    conn.commit()
    conn.close()

    print(f"База данных '{db_name}' и таблица 'Users' успешно созданы.")


def add_user(db_name, fio, login, h_password, role, status_str, status_int):
    # Создаем подключение к базе данных
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    h_password = hashpw(bytes(h_password, 'utf-8'), salt=gensalt())

    # Вставляем нового пользователя в таблицу
    try:
        cursor.execute('''
            INSERT INTO Users (fio, login, h_password, role, status_str, status_int)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (fio, login, h_password, role, status_str, status_int))

        # Сохраняем изменения
        conn.commit()
        print(f"Пользователь '{fio}' успешно добавлен в базу данных.")
        return True

    except sqlite3.IntegrityError:
        print(f"Ошибка: пользователь с логином '{login}' уже существует.")
        return False

    finally:
        # Закрываем соединение
        conn.close()


def get_user_by_login(db_session, user_login):
    # fields = ['FIO', 'login', 'h_password', 'role', 'status_str', 'status_int']
    # conn = sqlite3.connect(db_name)
    # cursor = conn.cursor()
    # res = cursor.execute(f'''SELECT * FROM Users WHERE Login = "{user_login}"''').fetchone()
    # conn.close()
    user = db_session.query(User).filter(User.Login == user_login).first()
    if user:
        return user
    else:
        print(f'Пользователь с логином {user_login} не найден')
        return False

#
# Пример использования функций
# create_database('users_database.db')

# Добавляем пользователя
# add_user('users_database.db', 'Гильдин Александр Григорьевич', 'teacher_1', 'gildin', 'teacher', '', 0)
#
# add_user('users_database.db', 'Петров Петр Петрович', 'user_1', '', 'student', '', 0)
#
# add_user('users_database.db', 'Иванов Иван Иванович', 'user_2', '', 'student', '', 0)
