import sqlite3
import datetime


conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    sex INTEGER,
    age INTEGER,
    birth_year INTEGER,
    city TEXT,
    status INTEGER
)
''')


def add_user(user_id, sex, age, birth_year, city, status):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO users (user_id, sex, age, birth_year, city, status) VALUES (?, ?, ?, ?, ?, ?)''',
                   (user_id, sex, age, birth_year, city, status))
    conn.commit()
    conn.close()


def get_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM users''')
    users = cursor.fetchall()
    conn.close()
    return users
