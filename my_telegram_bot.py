from collections import defaultdict
import telebot
from telebot import types
from my_connector_bot import *
from my_connector_bot import run_query

bot = telebot.TeleBot('')


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

    bot.send_message(message.chat.id, "Введите данные для подключения к базе данных:", reply_markup=markup)
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


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if not bot.current_user_data.get(message.chat.id):
        bot.reply_to(message, "Сначала необходимо подключиться к базе данных. Для этого введите команду /connect.")
        return
    if message.text.strip().upper().startswith("SELECT"):
        query = message.text.strip()
        host = bot.current_user_data[message.chat.id]['host']
        user = bot.current_user_data[message.chat.id]['user']
        password = bot.current_user_data[message.chat.id]['password']
        database = bot.current_user_data[message.chat.id]['database']
        results = run_query(query, host, user, password, database)
        response = "Результаты:\n"
        for row in results:
            response += str(row) + "\n"
        bot.reply_to(message, response)
    elif message.text.strip().upper().startswith("INSERT"):
        query = message.text.strip()
        host = bot.current_user_data[message.chat.id]['host']
        user = bot.current_user_data[message.chat.id]['user']
        password = bot.current_user_data[message.chat.id]['password']
        database = bot.current_user_data[message.chat.id]['database']
        run_query(query, host, user, password, database)

        response = "Данные успешно добавлены в базу данных"
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Некорректный запрос. Введите SQL-запрос в формате 'SELECT ...' или 'INSERT INTO ... VALUES ...'")


bot.polling(none_stop=True)
