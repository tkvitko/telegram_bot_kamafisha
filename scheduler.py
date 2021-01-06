#!/usr/bin/python3.6

import asyncio
import time

import aioschedule as schedule
from pymongo import MongoClient
from telethon.sync import TelegramClient

from tg_bot import get_today, get_and_send_news, get_and_send_events

mongo_con_string = 'mongodb://localhost:27017'
db_client = MongoClient(mongo_con_string)
db = db_client['users_kamafisha']

# Расписание автоматических рассылок
TIME_TO_SEND_NEWS = '10:00'


# TIME_TO_SEND_EVENTS = '11:00'


async def send_news(bot):
    # Отправка новостей

    request_date = get_today()
    users_list = db.users.find()

    for recipient in users_list:
        await get_and_send_news(bot=bot, user=recipient['_id'], date=request_date.strftime('%Y-%m-%d'))


async def send_events(bot):
    # Отправка мероприятий

    request_date = get_today()
    users_list = db.users.find()

    for recipient in users_list:
        await get_and_send_events(bot=bot, user=recipient['_id'], date=request_date.strftime('%Y-%m-%d'))


if __name__ == '__main__':

    bot_token = ''
    api_id = 0
    api_hash = ''

    bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

    schedule.every().day.at(TIME_TO_SEND_NEWS).do(send_news, bot=bot)
    # schedule.every().day.at(TIME_TO_SEND_EVENTS).do(send_events, bot=bot)

    loop = asyncio.get_event_loop()

    while True:
        loop.run_until_complete(schedule.run_pending())
        time.sleep(10)
