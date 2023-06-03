import datetime
from vk_api import VkApi
from dotenv import load_dotenv
import os
import requests
from aiogram import Bot, Dispatcher, types

load_dotenv()

VK_TOKEN = os.getenv('VK_TOKEN')
VK_ID = os.getenv('VK_ID')

vk_session = VkApi(token=VK_TOKEN, api_version='5.131')
vk = vk_session.get_api()


def get_popular_photo(user_id: int) -> str:
    photos = vk.photos.get(owner_id=user_id, album_id='profile', extended=1)['items']
    if not photos:
        return None
    sorted_photos = sorted(photos, key=lambda x: x['likes']['count'], reverse=True)
    for photo in sorted_photos:
        sizes = photo.get('sizes', [])
        if sizes:
            return sizes[-1]['url']
    return None


def get_city_id(city_name):
    city_name = city_name.strip().lower()
    response = vk.database.getCities(country_id=1, q=city_name, count=1)
    if response["items"]:
        return response["items"][0]["id"]
    return None

##========================== Cripto ==========================


async def blockchaine_command_handler(message: types.Message):
    response = requests.get(
        'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false&include_market_cap=true')
    cryptocurrencies = response.json()

    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    await message.answer(f'Цены на криптовалюты на {current_time}')

    # Выводим данные о каждой валюте
    for currency in cryptocurrencies:
        name = currency['name']
        price = currency['current_price']
        market_cap = currency['market_cap']
        await message.answer(f'{name}: {price} USD\nMarket Cap: {market_cap} USD')

##========================== end Cripto ==========================



