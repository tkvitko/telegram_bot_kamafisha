#!/usr/bin/python3.6

import logging
import configparser
from datetime import datetime, timedelta

from pymongo import MongoClient, errors
from pytz import timezone
from telethon import TelegramClient, events
from telethon.tl.custom import Button

from cache import get_from_cache, put_to_cache
from sql_connection import get_news_from_db, get_events_from_db_by_date, get_events_from_db_by_category
from sql_connection import get_cinema_from_db_all, get_cinema_from_db_by_date
from sql_connection import get_news_from_db_by_category

mongo_con_string = 'mongodb://localhost:27017'
db_client = MongoClient(mongo_con_string)
db = db_client['users_lefortovo']
# logging.basicConfig(filename='bot.log')
logging.basicConfig(filename='./bot.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
logger = logging.getLogger(__name__)  # Using this object will be better

date_limit = '2020-07-01'  # минимальная дата при обращении в SQL, чтобы не перегружать ответ
max_elements = 20  # максимальное количество элементов в ответе, чтобы телеграмм пропустил сообщение

# Названия кнопок меню
TODAY_NEWS = 'Новости за сегодня'
TODAY = 'Сегодня'
TODAY_AFFICHE = 'Афиша на сегодня'
TOMORROW_AFFICHE = 'Афиша на завтра'
AFTER_TOMORROW = 'Афиша на послезавтра'
CATEGORIES = 'Категории мероприятий'
NEWS = 'Новости'
ABOUT = 'О боте'
CINEMA = 'Кино'
AFFICHE = 'Афиша'
DIGEST = 'Дайджест'
BACK = 'Назад'
CHOOSE_ACTION = 'Выберите действие:'

MENU_MAIN = [
    Button.text(NEWS, resize=True, single_use=True),
    Button.text(AFFICHE, resize=True, single_use=True),
    Button.text(ABOUT, resize=True, single_use=True)
]

MENU_NEWS = [
    Button.text(TODAY_NEWS, resize=True, single_use=True),
    Button.text(DIGEST, resize=True, single_use=True),
    Button.text(BACK, resize=True, single_use=True)
]

MENU_AFFICHE = [
    Button.text(TODAY_AFFICHE, resize=True, single_use=True),
    Button.text(TOMORROW_AFFICHE, resize=True, single_use=True),
    Button.text(CATEGORIES, resize=True, single_use=True),
    Button.text(BACK, resize=True, single_use=True)
]

ABOUT_TEXT = """
Бот информационного сайта "Лефортовец" (lefortovo.today). 
Новости и афиша мероприятий района Левортово города Москва
"""

CINEMA_CAT_ID = 122


def get_events_categories_list():
    # Функция, определяющая категории событий

    prod_list = {
        # 'Новости': b'1',
        # 'Общество': b'2',
        # 'Культура': b'3',
        # 'ЖКЖ': b'4',
        # 'Главные новости': b'5',
        # 'Органы власти': b'6',
        'Концерты': b'7',
        'Обучение': b'8',
        'Спектакли': b'9',
        'Праздники': b'10',
        'Выставки': b'11',
        'Кино': b'12',
        'Спорт': b'13',
        # 'Учреждения культуры': b'14',
        # 'Кинотеатры': b'15',
        # 'Спорт': b'16',
        # 'Политика': b'17',
        # 'Транспорт': b'18',
        # 'Главное': b'19',
        # 'Торговля и услуги': b'20',
        # 'Блог редакции': b'308'
    }

    return prod_list


def get_news_categories_list():
    # Функция, определяющая категории событий

    prod_list = {
        'Новости': b'1',
        'Общество': b'2',
        'Культура': b'3',
        'ЖКЖ': b'4',
        'Спорт': b'16',
        'Политика': b'17',
        'Транспорт': b'18',
        'Торговля и услуги': b'20',
        'Наш район': b'282',
        'История': b'283',
        'Люди': b'284',
        'Достопримечательности': b'285',
        'Здоровье': b'301',
        'Благоустройство и строительство': b'309'
    }

    return prod_list


def get_news(date):
    # Взятие из кеша
    news_message = get_from_cache('news', date)

    if not news_message:
        # Взятие из базы
        news_message = 'Новости:\n\n'
        data = get_news_from_db(date_limit=date)

        for item in data:
            new_string = f'{item[1]}\n{item[2]}\n\n'
            news_message += new_string

        # Кладем в кеш
        put_to_cache(news_message, 'news', date)
    return news_message


def get_news_by_category(category_id):
    # Взятие из кеша
    news_message = get_from_cache('news', category=category_id)
    # news_message = None

    if not news_message:
        # Взятие из базы
        # news_message = 'Новости:\n\n'
        news_message = ''
        data = get_news_from_db_by_category(category_id=category_id, date_limit=date_limit)

        for item in data:
            new_string = f'{item[1]}\n{item[2]}\n\n'
            news_message += new_string

        # Кладем в кеш
        put_to_cache(news_message, 'news', category=category_id)
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


def get_cinema(date=None):
    if date:
        # Взятие из кеша
        cinema_message = get_from_cache('cinema', date)

        if not cinema_message:
            # Взятие из базы
            cinema_message = f'Кино:\n\n'
            data = get_cinema_from_db_by_date(CINEMA_CAT_ID, date, date_limit)
            for item in data[:max_elements]:
                new_string = f'{item[1]}\n{item[2]}\nДата начала: {item[3].split(" ")[0]}\n\n'
                cinema_message += new_string
            # Кешируем
            put_to_cache(cinema_message, 'cinema', date)

    else:
        # Взятие из кеша
        cinema_message = get_from_cache('cinema', category=CINEMA_CAT_ID)

        if not cinema_message:
            # Взятие из базы
            cinema_message = f'Кино на {date}:\n\n'
            data = get_cinema_from_db_all(CINEMA_CAT_ID, date_limit)
            for item in data[:max_elements]:
                new_string = f'{item[1]}\n{item[2]}\nДата начала: {item[3].split(" ")[0]}\n\n'
                cinema_message += new_string
            # Кешируем
            put_to_cache(cinema_message, 'cinema', category=CINEMA_CAT_ID)

    # print(events_message)
    return cinema_message


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


async def get_and_send_cinema(bot, user, date=None):
    # Получение кино из кеша и отправка

    data = None
    if date:
        data = get_cinema(date)
    else:
        data = get_cinema()

    if data:
        await send_message(bot=bot, message=data, user=user)


async def send_cinema(event, bot, delta=None):
    # Функция отправки событий для категории

    print('send_events_for_category')
    chat_id = event.message.chat.id
    logging.warning(f'got CINEMA from {chat_id}')
    if delta or delta == 0:
        request_date = get_today() + timedelta(days=delta)
        print(f'DATE IS {request_date}')
        await get_and_send_cinema(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'))
    else:
        await get_and_send_cinema(bot=bot, user=chat_id)
    await welcome_board(bot, chat_id)


async def get_and_send_news(bot, user, date=None):
    # Получение событий из кеша и отправка
    data = get_news(date=date)
    # print(data)
    await send_message(bot=bot, message=data, user=user)


async def send_events_for_date(event, bot, delta, category=None):
    # Функция отправки событий для даты

    chat_id = event.message.chat.id
    request_date = get_today() + timedelta(days=delta)
    await get_and_send_events(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'), category=category)
    # await welcome_board(bot, chat_id)


async def send_events_for_category(event, bot, delta, category, category_name):
    # Функция отправки событий для категории

    print('send_events_for_category')
    chat_id = event.message.chat.id
    logging.warning(f'got EVENTS from {chat_id}')
    request_date = get_today() + timedelta(days=delta)
    await get_and_send_events(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'), category=category,
                              category_name=category_name)
    # await welcome_board(bot, chat_id)


async def get_and_send_news_by_category(bot, user, category_id):
    # Получение событий из кеша и отправка
    data = get_news_by_category(category_id=category_id)
    # print(data)
    await send_message(bot=bot, message=data, user=user)


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

    await bot.send_message(chat_id, CHOOSE_ACTION, buttons=MENU_MAIN)


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
        await bot.send_message(chat_id, CHOOSE_ACTION, buttons=MENU_NEWS)

    @bot.on(events.NewMessage(pattern=TODAY_NEWS))
    # Новости за сегодня
    async def handler(event):
        chat_id = event.message.chat.id
        logging.warning(f'got TODAY_NEWS from {chat_id}')
        request_date = get_today()
        await get_and_send_news(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'))
        # await get_and_send_news(bot=bot, user=chat_id, date='2020-12-18')
        # await welcome_board(bot, chat_id)
        await bot.send_message(chat_id, CHOOSE_ACTION, buttons=MENU_NEWS)

    @bot.on(events.NewMessage(pattern=AFFICHE))
    # Новости за сегодня
    async def handler(event):
        chat_id = event.message.chat.id
        logging.warning(f'got AFFICHE from {chat_id}')
        await bot.send_message(chat_id, CHOOSE_ACTION, buttons=MENU_AFFICHE)

    @bot.on(events.NewMessage(pattern=TODAY_AFFICHE))
    # Новости за сегодня
    async def handler(event):
        chat_id = event.message.chat.id
        logging.warning(f'got TODAY_AFFICHE from {chat_id}')
        await send_events_for_date(event, bot, delta=0)
        await bot.send_message(chat_id, CHOOSE_ACTION, buttons=MENU_AFFICHE)

    @bot.on(events.NewMessage(pattern=TOMORROW_AFFICHE))
    # Новости за сегодня
    async def handler(event):
        chat_id = event.message.chat.id
        logging.warning(f'got TODAY_AFFICHE from {chat_id}')
        await send_events_for_date(event, bot, delta=1)
        await bot.send_message(chat_id, CHOOSE_ACTION, buttons=MENU_AFFICHE)

    @bot.on(events.NewMessage(pattern=ABOUT))
    # О боте
    async def handler(event):
        chat_id = event.message.chat.id
        logging.warning(f'got ABOUT from {chat_id}')
        await bot.send_message(chat_id, ABOUT_TEXT)
        await welcome_board(bot, chat_id)

    @bot.on(events.NewMessage(pattern=BACK))
    # Новости за сегодня
    async def handler(event):
        chat_id = event.message.chat.id
        logging.warning(f'got BACK from {chat_id}')
        await bot.send_message(chat_id, CHOOSE_ACTION, buttons=MENU_MAIN)

    @bot.on(events.NewMessage(pattern=CATEGORIES))
    # Афиша по категории
    async def handler(event):

        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.message.chat.id
        logging.warning(f'got CATEGORIES from {chat_id}')

        categories = get_events_categories_list()
        buttons = [[Button.inline(k, v)] for k, v in categories.items()]

        async with bot.conversation(chat_id) as conv:
            await conv.send_message('Выберите категорию',
                                    buttons=buttons)

            press = await conv.wait_event(press_event(sender_id))

            for k, v in categories.items():
                if press.data == v:
                    await send_events_for_category(event, bot, delta=0, category=int(v), category_name=k)

            await conv.send_message(CHOOSE_ACTION, buttons=MENU_AFFICHE)

    @bot.on(events.NewMessage(pattern=DIGEST))
    # Дайджест новостей
    async def handler(event):

        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.message.chat.id
        logging.warning(f'got DIGEST from {chat_id}')

        categories = get_news_categories_list()
        for k, v in categories.items():
            await bot.send_message(chat_id, k)
            await get_and_send_news_by_category(bot, chat_id, int(v))

        await bot.send_message(chat_id, CHOOSE_ACTION, buttons=MENU_NEWS)

    # @bot.on(events.NewMessage(pattern=CINEMA))
    # # Расписание киносеансов
    # async def handler(event):
    #
    #     sender = await event.get_sender()
    #     sender_id = sender.id
    #     chat_id = event.message.chat.id
    #     logging.warning(f'got CINEMA from {chat_id}')
    #
    #     cinema_days_list = {
    #         'Сегодня': b'0',
    #         'Завтра': b'1',
    #         'Послезавтра': b'2',
    #         'Все': b'-1'
    #     }
    #
    #     buttons = [[Button.inline(k, v)] for k, v in cinema_days_list.items()]
    #
    #     async with bot.conversation(chat_id) as conv:
    #         await conv.send_message('Выберите дату',
    #                                 buttons=buttons)
    #
    #         press = await conv.wait_event(press_event(sender_id))
    #
    #         for k, v in cinema_days_list.items():
    #             if press.data == v:
    #                 print(press.data)
    #                 if press.data == b'-1':
    #                     await send_cinema(event, bot)
    #                 else:
    #                     await send_cinema(event, bot, delta=int(v))

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
    config = configparser.ConfigParser()
    config.read("config.ini")
    bot_token = (config["bot"]["bot_token"])
    api_id = (config["bot"]["api_id"])
    api_hash = (config["bot"]["api_hash"])

    work_with_chat(api_id, api_hash, bot_token)
