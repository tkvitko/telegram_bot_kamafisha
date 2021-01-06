#!/usr/bin/python3.6

import logging
from datetime import datetime, timedelta

from pymongo import MongoClient, errors
from pytz import timezone
from telethon import TelegramClient, events
from telethon.tl.custom import Button

from cache import get_from_cache, put_to_cache
from sql_connection import get_news_from_db, get_events_from_db_by_date, get_events_from_db_by_category

mongo_con_string = 'mongodb://localhost:27017'
db_client = MongoClient(mongo_con_string)
db = db_client['users_kamafisha']
logging.basicConfig(filename='bot.log')

date_limit = '2020-07-01'  # минимальная дата при обращении в SQL, чтобы не перегружать ответ
max_elements = 20  # максимальное количество элементов в ответе, чтобы телеграмм пропустил сообщение

# Названия кнопок меню
TODAY = 'Афиша на сегодня'
TOMORROW = 'Афиша на завтра'
AFTER_TOMORROW = 'Афиша на послезавтра'
CATEGORIES = 'Категории'
NEWS = 'Новости'
ABOUT = 'О боте'

ABOUT_TEXT = """Бот http://kamafisha.ru/
Разработка: @taraskvitko
"""


def get_categories_list():
    # Функция, определяющая категории событий

    prod_list = {
        'Выставки': b'25',
        'Прочие': b'26',
        'Встречи': b'27',
        'Спектакли': b'28',
        'Концерты': b'29',
        'Обучение': b'30',
        'Праздники': b'31'
    }

    return prod_list


def get_news(date):
    # Взятие из кеша
    news_message = get_from_cache('news', date)

    if not news_message:
        # Взятие из базы
        news_message = 'Новости:\n\n'
        data = get_news_from_db(date)

        for item in data:
            new_string = f'{item[1]}\n{item[2]}\n\n'
            news_message += new_string

        # Кладем в кеш
        put_to_cache(news_message, 'news', date)
    return news_message


def get_events(date, category=None, category_name=None):
    if category:
        # Взятие из кеша
        events_message = get_from_cache('events', date, category)

        if not events_message:
            # Взятие из базы
            events_message = f'Мероприятия категории {category_name}:\n\n'
            data = get_events_from_db_by_category(category, date, date_limit)
            for item in data[:max_elements]:
                new_string = f'{item[1]}\n{item[2]}\nДата начала: {item[3].split(" ")[0]}\n\n'
                events_message += new_string
            # Кешируем
            put_to_cache(events_message, 'events', date, category)

    else:
        # Взятие из кеша
        events_message = get_from_cache('events', date)

        if not events_message:
            # Взятие из базы
            events_message = f'Мероприятия на {date}:\n\n'
            data = get_events_from_db_by_date(date, date_limit)
            for item in data[:max_elements]:
                new_string = f'{item[1]}\n{item[2]}\nДата начала: {item[3].split(" ")[0]}\n\n'
                events_message += new_string
            # Кешируем
            put_to_cache(events_message, 'events', date)

    # print(events_message)
    return events_message


async def send_message(bot, message, user):
    # Отправка данных пользователям

    if user == 'all':
        # если вместо пользователя явно передано 'all', отправляем всем
        users_list = db.users.find()
        for recipient in users_list:
            await bot.send_message(recipient['_id'], message)
    else:
        # если передан пользователь, отправляем по нему
        try:
            await bot.send_message(user, message)
        except Exception as e:
            print(e)


async def get_and_send_events(bot, user, date=None, category=None, category_name=None):
    # Получение событий из кеша и отправка

    data = None
    if category:
        data = get_events(date, category, category_name)
    else:
        data = get_events(date)

    if data:
        await send_message(bot=bot, message=data, user=user)


async def get_and_send_news(bot, user, date=None):
    # Получение событий из кеша и отправка
    data = get_news(date=date)
    await send_message(bot=bot, message=data, user=user)


async def send_events_for_date(event, bot, delta):
    # Функция отправки событий для даты

    chat_id = event.message.chat.id
    request_date = get_today() + timedelta(days=delta)
    await get_and_send_events(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'))
    await welcome_board(bot, chat_id)


async def send_events_for_category(event, bot, delta, category, category_name):
    # Функция отправки событий для категории

    chat_id = event.message.chat.id
    logging.warning(f'got EVENTS from {chat_id}')
    request_date = get_today() + timedelta(days=delta)
    await get_and_send_events(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'), category=category,
                              category_name=category_name)
    await welcome_board(bot, chat_id)


def get_today():
    # Функция получения текущего времени

    moscow = timezone('Europe/Moscow')
    moscow_time = datetime.now(moscow)

    return moscow_time


def save_user_to_mongo(user_id):
    # Функция сохранения телеграм-пользователя в монго

    new_user = {'_id': user_id}
    try:
        db.users.insert_one(new_user)
    except errors.DuplicateKeyError:
        pass


def press_event(user_id):
    return events.CallbackQuery(func=lambda e: e.sender_id == user_id)


async def welcome_board(bot, chat_id):
    # Start keyboard
    await bot.send_message(chat_id, 'Выберите действие:', buttons=[
        [
            Button.text(TODAY, resize=True, single_use=True),
            Button.text(TOMORROW, resize=True, single_use=True),
            Button.text(AFTER_TOMORROW, resize=True, single_use=True)
        ],
        [
            Button.text(CATEGORIES, resize=True, single_use=True),
            Button.text(NEWS, resize=True, single_use=True),
            Button.text(ABOUT, resize=True, single_use=True)
        ]
    ])


def work_with_chat(api_id, api_hash, bot_token):
    bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

    @bot.on(events.NewMessage(pattern='/start'))
    # Начало работы с ботом
    async def handler(event):

        chat_id = event.message.chat.id
        logging.warning(f'got /start from {chat_id}')

        # Start keyboard
        await welcome_board(bot, chat_id)

        # Сохранение пользователя в базу (для рассылок)
        save_user_to_mongo(chat_id)

    @bot.on(events.NewMessage(pattern=NEWS))
    # Новости за сегодня
    async def handler(event):
        chat_id = event.message.chat.id
        logging.warning(f'got NEWS from {chat_id}')
        request_date = get_today()
        await get_and_send_news(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'))
        # await get_and_send_news(bot=bot, user=chat_id, date='2020-12-18')
        await welcome_board(bot, chat_id)

    @bot.on(events.NewMessage(pattern=ABOUT))
    # О боте
    async def handler(event):
        chat_id = event.message.chat.id
        logging.warning(f'got ABOUT from {chat_id}')
        await bot.send_message(chat_id, ABOUT_TEXT)
        await welcome_board(bot, chat_id)

    @bot.on(events.NewMessage(pattern=TODAY))
    # Афиша на сегодня
    async def handler(event):
        await send_events_for_date(event, bot, delta=0)

    @bot.on(events.NewMessage(pattern=TOMORROW))
    # Афиша на завтра
    async def handler(event):
        await send_events_for_date(event, bot, delta=1)

    @bot.on(events.NewMessage(pattern=AFTER_TOMORROW))
    # Афиша на послезавтра
    async def handler(event):
        await send_events_for_date(event, bot, delta=2)

    @bot.on(events.NewMessage(pattern=CATEGORIES))
    # Афиша по категории
    async def handler(event):

        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.message.chat.id
        logging.warning(f'got CATEGORIES from {chat_id}')

        categories = get_categories_list()
        buttons = [[Button.inline(k, v)] for k, v in categories.items()]

        async with bot.conversation(chat_id) as conv:
            await conv.send_message('Выберите категорию',
                                    buttons=buttons)

            press = await conv.wait_event(press_event(sender_id))

            for k, v in categories.items():
                if press.data == v:
                    await send_events_for_category(event, bot, delta=0, category=int(v), category_name=k)

    @bot.on(events.NewMessage(pattern='/send_admin_message'))
    # Отправка массовой рассылки админом
    async def handler(event):
        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.message.chat.id
        logging.warning(f'got ADMIN_MESSAGE from {chat_id}')

        async with bot.conversation(chat_id) as conv:
            await conv.send_message('Введите сообщение для отправки всем пользователям бота:')
            answer_message = await conv.get_response()
            message_to_send = answer_message.text
            await send_message(bot, message_to_send, user='all')
            await conv.send_message('Сообщение отправлено')

    bot.start()
    bot.run_until_disconnected()


if __name__ == "__main__":
    bot_token = ''  # prod
    api_id = 0
    api_hash = ''

    work_with_chat(api_id, api_hash, bot_token)