import random
import logging
import openai
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode, InputFile
from aiogram.utils import executor
from dotenv import load_dotenv
import os
import aiohttp
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import html
from keyboards.buttons import keyboard, markup_vk
from db_vtinder import add_user, get_users
from vk_functions_vtinder import get_city_id, vk, get_popular_photo, blockchaine_command_handler
import requests
import json
import websocket


load_dotenv()

bot = Bot(token=os.getenv('TOKEN_BOT'))
openai.api_key = os.getenv('TOKEN_AI')
DEEPAI_API_KEY = os.getenv('DEEPAI_API_KEY')
DEEPAI_API_URL = 'https://api.deepai.org/api/text2img'

logging.basicConfig(level=logging.INFO)
logger_name = 'image_bot'
logger = logging.getLogger(logger_name)


storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def on_startup(dp):
    print('Бот вышел в онлайн')
    await bot.delete_webhook()


async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    await bot.send_message(message.from_user.id,
                            f"Привет {message.from_user.first_name}!\n\n"
                            f"Здесь вы можете найти своего родного человека в социальной сети vk.com "
                            f"или поболтать с искусственным интеллектом\n\n"
                            f"Для этого выберите режим работы:\n\n/reset\n\n")
    add_user(user_id, None, None, None, None, None)


## ============================= Сброс/выбор режима ==============================

async def reset_mode(message: types.Message):
    user_id = message.from_user.id
    user_modes.pop(user_id, None)
    await send_reset(message)


async def send_reset(message: types.Message):
    photo = InputFile("images/kissing-in-the-snow.jpg")
    await bot.send_photo(message.chat.id, photo=photo)
    await bot.send_message(chat_id=message.chat.id, text="Выбор режима:", reply_markup=markup_vk)

## ============================= end Сброс/выбор режима ==============================

# ============================= mode =============================

user_modes = {}


@dp.callback_query_handler(lambda c: c.data in ['dating', 'chatgpt'])
async def process_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    user_modes[user_id] = callback_query.data

    if user_modes[user_id] == 'dating':
        dating_icon = "✅"
        chatgpt_icon = ""
    elif user_modes[user_id] == 'chatgpt':
        dating_icon = ""
        chatgpt_icon = "✅"
    else:
        dating_icon = ""
        chatgpt_icon = ""

    # Обновляем разметку кнопок в сообщении
    markup_vk = types.InlineKeyboardMarkup(row_width=2)
    item1 = types.InlineKeyboardButton(f"Знакомства {dating_icon}", callback_data='dating')
    item2 = types.InlineKeyboardButton(f"ChatGPT 3.5 {chatgpt_icon}", callback_data='chatgpt')
    markup_vk.add(item1, item2)

    await bot.edit_message_reply_markup(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id, reply_markup=markup_vk)
    await bot.answer_callback_query(callback_query.id)

# ============================= end mode =============================

# ============================= status =============================


async def send_status(message: types.Message):
    user_id = message.from_user.id
    mode = user_modes.get(user_id)
    if mode is None:
        await bot.send_message(user_id, "Вы еще не выбрали режим работы.")
    elif mode == "dating":
        markup_vk = types.InlineKeyboardMarkup(row_width=2)
        item1 = types.InlineKeyboardButton(f"Знакомства ✅", callback_data='dating')
        item2 = types.InlineKeyboardButton(f"ChatGPT 3.5", callback_data='chatgpt')
        markup_vk.add(item1, item2)
        await bot.send_message(user_id, "В данный момент вы находитесь в режиме:\n\nЗнакомства 💕", reply_markup=markup_vk)
    elif mode == "chatgpt":
        markup_vk = types.InlineKeyboardMarkup(row_width=2)
        item1 = types.InlineKeyboardButton(f"Знакомства", callback_data='dating')
        item2 = types.InlineKeyboardButton(f"ChatGPT 3.5 ✅", callback_data='chatgpt')
        markup_vk.add(item1, item2)
        await bot.send_message(user_id, "В данный момент вы находитесь в режиме:\n\nChatGPT 3.5 Turbo⚡️", reply_markup=markup_vk)


async def send_status_command(message: types.Message):
    await send_status(message)

# ============================= end status ===========================


# ============================= faq ===========================

async def command_faq(message: types.Message):
    photo = InputFile("images/Tinder.jpg")
    information_bold = (f'{message.from_user.first_name}, как искать партнера.\n\n')
    information_italic = ('Введите четыре условия:\n'
                          'Одним сообщением, каждое слово на новой строке\n'
                          'Пол (мужской/женский)\nВозраст\nГород\nСемейное положение (свободен/замужем/ - (независимо от пола)\n\n'
                          'Пример ввода:\n\nЖенский\n33\nМосква\nсвободен')
    information_bold_1 = ('Бот ищет только активных пользователей, кто заходит минимум '
                          'один раз в неделю.\n'
                          'Поиск всегда рандомный и не повторяется. '
                          'Так как поиск рандомный, возможно, что будет не три варианта, а меньше '
                          'или вообще не быть результата, повторите запрос снова.')

    information_bold = html.escape(information_bold)
    information_bold = f"<b>{information_bold}</b>"

    information_italic = html.escape(information_italic)
    information_italic = f"<i>{information_italic}</i>"

    information_bold_1 = html.escape(information_bold_1)
    information_bold_1 = f"<b>{information_bold_1}</b>"

    caption = f"{information_bold}{information_italic}\n\n{information_bold_1}"
    await bot.send_photo(message.chat.id, photo=photo, caption=caption, parse_mode='HTML')

# ============================= end faq ===========================

# ============================= engineer ===========================


async def command_use(message: types.Message):
    photo = InputFile("images/YuriyBaragin.jpg")
    information_italic = (f'Привет {message.from_user.first_name}, меня зовут Юрий.\n\n'
                          f'Если у вас есть какие нибудь пожелания к боту.\n'
                          f'Напишите мне в telegram: ')

    information_italic = html.escape(information_italic)
    information_italic = f"<i>{information_italic}</i>"

    caption = f"{information_italic}"
    await bot.send_photo(message.chat.id, photo=photo, caption=caption, parse_mode='HTML', reply_markup=keyboard)

# ============================= end engineer ===========================


## -============================== coingecko ===========================


async def blockchaine_handler(message: types.Message):
    await blockchaine_command_handler(message)

## -============================== end coingecko ===========================


dp.register_message_handler(send_welcome, commands='start')
dp.register_message_handler(reset_mode, commands='reset')
dp.register_message_handler(send_status_command, commands='status')
dp.register_callback_query_handler(process_callback, lambda c: c.data in ['dating', 'chatgpt'])
dp.register_message_handler(command_faq, commands='faq')
dp.register_message_handler(blockchaine_handler, commands='crypto')
dp.register_message_handler(command_use, commands='engineer')


# ============================= ChatGPT ===========================


@dp.message_handler(lambda message: user_modes.get(message.from_user.id) == 'chatgpt')
async def chatgpt_handler(message: types.Message):
    user_id = message.from_user.id
    mode = user_modes.get(user_id)
    if mode == 'chatgpt':

        processing_message = await message.answer("⏳ Пожалуйста, подождите...")
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system",
                           "content": "You are a helpful assistant."},
                          {
                              "role": "user",
                              "content": message.text}],
                temperature=0.7,
                max_tokens=1024,
            )
        except openai.error.APIError as e:
            await message.answer(f'⚠️ Произошла ошибка: {e}.\n'
                                 f'Повторите запрос, пожалуйста')
            return

        await bot.delete_message(chat_id=message.chat.id, message_id=processing_message.message_id)
        await message.answer(response['choices'][0]['message']['content'])

# ============================= end ChatGPT ===========================


# ============================= VK ===========================

@dp.message_handler(lambda message: user_modes.get(message.from_user.id) == 'dating')
async def get_photos(message: types.Message):
    user_id = message.from_user.id
    if user_modes.get(user_id) != 'dating':
        return

    try:
        sex, age, city, status_text = map(str.strip, message.text.split('\n'[:3]))
    except ValueError:
        await bot.send_message(message.from_user.id, "Введите четыре условия:\n\nпол\nвозраст\nгород\nсемейное положение\n\n"
                                                     "Одним сообщением каждое слово на новой строке, пример ввода в /faq.")
        return

    sex = 2 if sex.lower() == 'мужской' else 1

    status_map = {'свободен': 1, 'замужем': 3}
    status = status_map.get(status_text.lower(), 0)

    city_id = get_city_id(city)
    if city_id is None:
        await bot.send_message(message.from_user.id, f"Город '{city}' не найден. Пожалуйста, попробуйте другой город.")
        return

    birth_year = datetime.date.today().year - int(age)
    saved_users = get_users()
    saved_user_ids = [u[0] for u in saved_users]
    users = [(u[0], u[1], u[2], u[3], u[4], u[5]) for u in saved_users]
    search_result = vk.users.search(count=1000, fields=['photo_max', 'domain', 'last_seen', 'bdate', 'is_closed', 'relation'], sex=sex, age=age,
                                    city=city_id, status=status, birth_year=birth_year)
    active_users = [user for user in search_result['items'] if
                    datetime.datetime.now().timestamp() - user.get('last_seen', {}).get('time', 0) < 7 * 24 * 60 * 60 and
                    user.get('bdate', '').endswith(f'.{birth_year}') and
                    user['id'] not in saved_user_ids and
                    not user['is_closed'] and
                    user.get('relation', 0) == status
    ]
    try:
        selected_users = random.sample(active_users, 3)
    except ValueError as e:
        await bot.send_message(message.from_user.id, "Не удалось выбрать пользователей. Попробуйте другой запрос.")
        return

    for user in selected_users:
        users.append((user['id'], sex, age, birth_year, city, status))
        add_user(user['id'], sex, age, birth_year, city, status)

        keyboard = InlineKeyboardMarkup()
        profile_button = types.InlineKeyboardButton(text="Профиль 👤", url=f"https://vk.com/{user['domain']}")
        chat_button = types.InlineKeyboardButton(text="Cообщение 💬", url=f"https://vk.com/im?sel={user['id']}")
        keyboard.add(profile_button, chat_button)

        await message.reply_photo(photo=get_popular_photo(user['id']),
                                  caption=f"{user['first_name']} {user['last_name']}, {age} года/лет", reply_markup=keyboard)

# ============================= end VK ===========================

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
