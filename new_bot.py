import os.path
import sys
from typing import Union
from collections import defaultdict
import telebot
from telebot import types
from dotenv import load_dotenv
import datetime
import time
import threading
import mysql.connector
import sqlite3


 class QueryError(Exception):
     pass


     def run_query(query, host, user, password, database):
         try:
             mydb = mysql.connector.connect(
                 host=host,
                 user=user,
                 password=password,
                 database=database
             )

             cursor = mydb.cursor()
             cursor.execute(query)
             result = cursor.fetchall()
             mydb.commit()
             mydb.close()
             return result
         except mysql.connector.Error as error:
             raise QueryError(str(error))


conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS user_data ('
               'chat_id INTEGER PRIMARY KEY, host TEXT, user TEXT, password TEXT, database TEXT)')


load_dotenv()
bot = telebot.TeleBot(os.environ['YB_TELEGRAM_BOT'])


def bot_description():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Показать описание бота", callback_data="bot_description"))
    return markup


def start(message):
    if os.path.isfile('user_settings.txt'):
        with open('user_settings.txt', 'r') as f:
            bot.current_user_data[message.chat.id] = eval(f.read())
    else:
        bot.current_user_data[message.chat.id] = {'host': None, 'user': None, 'password': None, 'database': None}
    if not all(bot.current_user_data[message.chat.id].values()):
        bot.send_message(message.chat.id, "Вы ещё не ввели данные подключения. Введите /connect, чтобы начать.")
    else:
        bot.send_message(message.chat.id,
                         "Привет! Я SQL-помощник. Я могу помочь тебе подключиться к базе данных."
                         " Для этого введи /connect и следуй инструкциям!"
                         " ", reply_markup=bot_description()[1])
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("/start")
        btn2 = types.KeyboardButton("/show_connection")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, text="Привет, {0.first_name}! Выберите действие".format(
            message.from_user), reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "bot_description":
        bot.send_message(call.message.chat.id, bot_description())


@bot.message_handler(commands=['connect'])
def connect_handler(message):
    if bot.current_user_data[message.chat.id]['host'] is not None:
        bot.send_message(message.chat.id, "Вы уже ввели данные подключения ранее. Если вы хотите "
                                          "начать новое подключение, введите /start. ")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(message.chat.id, "Введите host в формате 0.0.0.0 для подключения к"
                                      " базе данных:", reply_markup=markup)
    bot.register_next_step_handler(message, connect_host)


def connect_host(message):
    bot.current_user_data[message.chat.id]['host'] = message.text

    bot.send_message(message.chat.id, "Хост сохранен. Введите имя пользователя:")
    bot.register_next_step_handler(message, connect_user)


def connect_user(message):
    bot.current_user_data[message.chat.id]['user'] = message.text

    bot.send_message(message.chat.id, "Имя пользователя сохранено. Введите пароль:")
    bot.register_next_step_handler(message, connect_password)


def connect_password(message):
    bot.current_user_data[message.chat.id]['password'] = message.text

    bot.send_message(message.chat.id, "Пароль сохранен. Введите имя базы данных:")
    bot.register_next_step_handler(message, connect_database)


cursor_lock = threading.Lock()


def connect_database(message, chat_id):
    bot.current_user_data[chat_id]['database'] = message.text
    if all(bot.current_user_data[chat_id].values()):
        with open('user_settings.txt', 'w') as f:
            f.write(str(bot.current_user_data[chat_id]))

    cursor_lock.acquire()
    try:
        conn = sqlite3.connect('user_data_db.sqlite')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO user_data(chat_id, host, user, password, database) VALUES (?, ?, ?, ?, ?)',
            (chat_id, bot.current_user_data[chat_id]['host'], bot.current_user_data[chat_id]['user'],
             bot.current_user_data[chat_id]['password'], bot.current_user_data[chat_id]['database'])
        )
        conn.commit()
        cursor.close()
        conn.close()
    except sqlite3.Error as e:
        print(e)
    finally:
        cursor_lock.release()
    bot.send_message(chat_id, "Соединение с базой данных установлено. Введите /show_connection, чтобы проверить.")

    host = bot.current_user_data[message.chat.id]['host']
    if (host.startswith('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$') or host.startswith('/')):
        bot.reply_to(message, "Недопустимый символ в начале поля!")
        return
    user = bot.current_user_data[message.chat.id]['user']
    if (user.startswith('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$') or user.startswith('/')):
        bot.reply_to(message, "Недопустимый символ в начале поля!")
        return
    password = bot.current_user_data[message.chat.id]['password']
    if (password.startswith('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$') or password.startswith('/')):
        bot.reply_to(message, "Недопустимый символ в начале поля!")
        return
    database = bot.current_user_data[message.chat.id]['database']
    if (database.startswith('^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$') or database.startswith('/')):
        bot.reply_to(message, "Недопустимый символ в начале поля!")
        return

    try:
        result = run_query("SHOW TABLES", host, user, password, database)
        bot.send_message(message.chat.id, "Подключение к базе данных успешно. Результат запроса:\n{}".format(result))
    except mysql.connector.errors.Error as error:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных: {}".format(error))


bot.current_user_data = defaultdict(dict)


@bot.message_handler(commands=['show_connection'])
def show_connection(message):
    user_data = bot.current_user_data[message.chat.id]
    connection_data = "Данные подключения:\n" \
                      "Хост: {}\n" \
                      "Имя пользователя: {}\n" \
                      "Пароль: {}\n" \
                      "Имя базы данных: {}".format(user_data['host'], user_data['user'], user_data['password'],
                                                   user_data['database'])
    bot.send_message(message.chat.id, connection_data)


def check_response_size(response: Union[str, bytes]):
    max_size = 10 * 1024 * 1024
    if isinstance(response, str):
        response_size = sys.getsizeof(response.encode("utf-8"))
    else:
        response_size = sys.getsizeof(response.content)
    if response_size > max_size:
        return False
    return True


def create_shortened_response(response):
    max_allowed_size = 4000
    current_size = len(response)
    chars_to_remove = current_size - max_allowed_size
    shortened_response = response[:-chars_to_remove]
    return shortened_response


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    text = message.text

    if not text.endswith(';'):
        bot.reply_to(message, "Запрос должен заканчиваться символом ';'!")
        return

    if not bot.current_user_data.get(chat_id):
        bot.reply_to(message, "Сначала необходимо подключиться к базе данных. Для этого введите команду /connect.")
        return

    host = bot.current_user_data[chat_id]['host']
    user = bot.current_user_data[chat_id]['user']
    password = bot.current_user_data[chat_id]['password']
    database = bot.current_user_data[chat_id]['database']

    if text.strip().upper().startswith("SELECT"):
        query = text.strip()
        time.sleep(5)
        try:
            results = run_query(query, host, user, password, database)
        except QueryError:
            bot.reply_to(message, 'Произошла ошибка, попробуйте другой запрос.')
            return
        response = "Результаты:\n"
        for row in results:
            response += str(row) + "\n"

        response_size_ok = check_response_size(response)

        if response_size_ok:
            try:
                bot.reply_to(message, response)
            except telebot.apihelper.ApiHTTPException:
                max_length = 4096
                chunks = [response[i:i+max_length] for i in range(0, len(response), max_length)]
                create_shortened_response(response)
                for chunk in chunks:
                    bot.reply_to(message, chunk)
    elif text.strip().upper().startswith("DESCRIBE"):
        query = text.strip()
        time.sleep(5)
        try:
            results = run_query(query, host, user, password, database)
        except QueryError:
            bot.reply_to(message, "Произошла ошибка, попробуйте выполнить другой запрос.")
            return
        response = "Структура таблицы:\n"
        for row in results:
            response += str(row) + "\n"

        bot.reply_to(message, response)

    elif text.strip().upper().startswith("SHOW"):
        query = text.strip()
        time.sleep(5)
        try:
            results = run_query(query, host, user, password, database)
        except QueryError:
            bot.reply_to(message, "Произошла ошибка, попробуйте выполнить другой запрос.")
            return
        response = "Результаты:\n"
        for row in results:
            response += str(row) + "\n"

        bot.reply_to(message, response)
    else:
        bot.reply_to(message,
                     "Некорректный запрос. Введите SQL-запрос в формате 'SELECT, SHOW, DESCRIBE'")

    with open('sql_users_search.txt', 'a', encoding='utf-8') as f:
        f.write(
            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Запрос пользователя id {chat_id}: запрос sql {text}\n")


bot.polling(none_stop=True)
