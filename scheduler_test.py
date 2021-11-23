#!/usr/bin/python3.6

import configparser
from datetime import timedelta

from pymongo import MongoClient
from telethon.sync import TelegramClient

from sql_connection import get_news_from_db_by_category_by_time
from tg_bot import get_today, get_and_send_news, get_and_send_events, logger

mongo_con_string = 'mongodb://localhost:27017'
db_client = MongoClient(mongo_con_string)
db = db_client['users_lefortovo']

MAIN_NEWS_ID = 5
BLOG_ID = 308


def send_lefortovo(bot):
    # отправка новостей категорй Главный и Блог редакции

    logger.warning('Start task')
    # время, за которое получаем новости
    time_from = get_today() - timedelta(hours=1)
    time_from = time_from.strftime('%Y-%m-%d %H:%M:%S')
    logger.warning(f'Getting news from {time_from}')

    # кортежи новостей из базы
    data = []
    for category_id in [MAIN_NEWS_ID, BLOG_ID]:
        items = get_news_from_db_by_category_by_time(category_id=category_id,
                                                     time_limit=time_from)
        for item in items:
            data.append(item)

    logger.warning(f'Got {len(data)} new itmes to send')

    if len(data) != 0:
        # формирование сообщения для рассылки
        news_message = ''
        for item in data:
            new_string = f'{item[1]}\n{item[2]}\n\n'
            news_message += new_string

        # получение всех пользователей сервиса
        users_list = db.users.find()

        # отправка сообщения всем пользователям сервиса:
        for user in users_list:
            recipient = user['_id']
            try:
                bot.send_message(recipient, news_message)
                logger.warning(f'Message has been sent to {recipient}')
            except Exception as e:
                logger.warning(f'Cant send message to {recipient}: {e}')


if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.read("config.ini")
    bot_token = (config["bot"]["bot_token"])
    api_id = (config["bot"]["api_id"])
    api_hash = (config["bot"]["api_hash"])

    bot = TelegramClient('bot_scheduler', api_id, api_hash).start(bot_token=bot_token)

    send_lefortovo(bot=bot)