import os
import sys
from typing import Union
from collections import defaultdict
import telebot
from telebot import types
from my_connector_bot import *
from dotenv import load_dotenv

activate_this = 'D:/my_sql_project/my_virtualenv/my_bot/activate_this.py'
with open(activate_this) as f:
     exec(f.read(), {'__file__': activate_this})

load_dotenv()
bot = telebot.TeleBot(os.environ['YB_TELEGRAM_BOT'])


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("/select")
    btn2 = types.KeyboardButton("/insert")
    btn3 = types.KeyboardButton("/connect")
    markup.add(btn1, btn2, btn3)
    bot.send_message(message.chat.id, text="Привет, {0.first_name}! Выберите действие".format(
        message.from_user), reply_markup=markup)


@bot.message_handler(commands=['connect'])
def connect_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    host_button = types.KeyboardButton("Введите хост")
    user_button = types.KeyboardButton("Введите имя пользователя")
    password_button = types.KeyboardButton("Введите пароль")
    database_button = types.KeyboardButton("Введите имя базы данных")
    markup.add(host_button, user_button, password_button, database_button)

    bot.send_message(message.chat.id, "Введите host в формате 0.0.0.0 для подключения к базе данных:", reply_markup=markup)
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


def connect_database(message):
    bot.current_user_data[message.chat.id]['database'] = message.text

    host = bot.current_user_data[message.chat.id]['host']
    user = bot.current_user_data[message.chat.id]['user']
    password = bot.current_user_data[message.chat.id]['password']
    database = bot.current_user_data[message.chat.id]['database']

    try:
        result = run_query("SHOW TABLES", host, user, password, database)
        bot.send_message(message.chat.id, "Подключение к базе данных успешно. Результат запроса:\n{}".format(result))
    except mysql.connector.errors.Error as error:
        bot.send_message(message.chat.id, "Ошибка подключения к базе данных: {}".format(error))


bot.current_user_data = defaultdict(dict)


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
    if not bot.current_user_data.get(chat_id):
        bot.reply_to(message, "Сначала необходимо подключиться к базе данных. Для этого введите команду /connect.")
        return

    if text.strip().upper().startswith("SELECT"):
        query = text.strip()
        host = bot.current_user_data[chat_id]['host']
        user = bot.current_user_data[chat_id]['user']
        password = bot.current_user_data[chat_id]['password']
        database = bot.current_user_data[chat_id]['database']
        results = run_query(query, host, user, password, database)

        response = "Результаты:\n"
        for row in results:
            response += str(row) + "\n"

        response_size_ok = check_response_size(response)

        if response_size_ok:
            try:
                bot.reply_to(message, response)
            except telebot.apihelper.ApiHTTPException:
                create_shortened_response(response)
                bot.reply_to(message, f"Слишком большой объем данных. Вот обрезанный ответ:\n{create_shortened_response(response)}")

    elif text.strip().upper().startswith("INSERT"):
        query = text.strip()
        host = bot.current_user_data[chat_id]['host']
        user = bot.current_user_data[chat_id]['user']
        password = bot.current_user_data[chat_id]['password']
        database = bot.current_user_data[chat_id]['database']
        run_query(query, host, user, password, database)

        response = "Данные успешно добавлены в базу данных"
        bot.reply_to(message, response)

    else:
        bot.reply_to(message, "Некорректный запрос. Введите SQL-запрос в формате 'SELECT ...' или 'INSERT INTO ... VALUES ...'")


bot.polling(none_stop=True)
