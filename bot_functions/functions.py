import logging
from datetime import timedelta

from pymongo import MongoClient, errors
from pytz import timezone
from telethon import events
from telethon.tl.custom import Button

from bot_functions.strings import *
from cache import get_from_cache, put_to_cache
from sql_connection import get_news_from_db, get_events_from_db_by_category, get_events_from_db_by_date, \
    get_cinema_from_db_by_date, get_cinema_from_db_all

db_client = MongoClient(MONGO_CON_STRING)
db = db_client['users_kamafisha']
logging.basicConfig(filename='bot.log')


def get_categories_list():
    # Categories mapping

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
    # Getting from cache
    news_message = get_from_cache('news', date)

    if not news_message:
        # Getting from DB
        news_message = 'Новости:\n\n'
        data = get_news_from_db()

        for item in data:
            new_string = f'{item[1]}\n{item[2]}\n\n'
            news_message += new_string

        # Putting to cache
        put_to_cache(news_message, 'news', date)
    return news_message


def get_events(date, category=None, category_name=None):
    if category:
        # Getting from cache
        events_message = get_from_cache('events', date, category)

        if not events_message:
            # Getting from DB
            events_message = f'Мероприятия категории {category_name}:\n\n'
            data = get_events_from_db_by_category(category, date, date_limit)
            for item in data[:max_elements]:
                new_string = f'{item[1]}\n{item[2]}\nДата начала: {item[3].split(" ")[0]}\n\n'
                events_message += new_string
            # Putting to cache
            put_to_cache(events_message, 'events', date, category)

    else:
        # Getting from cache
        events_message = get_from_cache('events', date)

        if not events_message:
            # Getting from DB
            events_message = f'Мероприятия на {date}:\n\n'
            data = get_events_from_db_by_date(date, date_limit)
            for item in data[:max_elements]:
                new_string = f'{item[1]}\n{item[2]}\nДата начала: {item[3].split(" ")[0]}\n\n'
                events_message += new_string
            # Putting to cache
            put_to_cache(events_message, 'events', date)

    return events_message


def get_cinema(date=None):
    if date:
        # Getting from cache
        cinema_message = get_from_cache('cinema', date)

        if not cinema_message:
            # Getting from DB
            cinema_message = f'Кино:\n\n'
            data = get_cinema_from_db_by_date(CINEMA_CAT_ID, date, date_limit)
            for item in data[:max_elements]:
                new_string = f'{item[1]}\n{item[2]}\nДата начала: {item[3].split(" ")[0]}\n\n'
                cinema_message += new_string
            # Putting to cache
            put_to_cache(cinema_message, 'cinema', date)

    else:
        # Getting from cache
        cinema_message = get_from_cache('cinema', category=CINEMA_CAT_ID)

        if not cinema_message:
            # Getting from DB
            cinema_message = f'Кино на {date}:\n\n'
            data = get_cinema_from_db_all(CINEMA_CAT_ID, date_limit)
            for item in data[:max_elements]:
                new_string = f'{item[1]}\n{item[2]}\nДата начала: {item[3].split(" ")[0]}\n\n'
                cinema_message += new_string
            # Putting to cache
            put_to_cache(cinema_message, 'cinema', category=CINEMA_CAT_ID)

    return cinema_message


async def send_message(bot, message, user):
    # Sending data to users

    if user == 'all':
        users_list = db.users.find()
        for recipient in users_list:
            await bot.send_message(recipient['_id'], message)
    else:
        # if user has been defined, send only to him
        try:
            await bot.send_message(user, message)
        except Exception as e:
            print(e)


async def get_and_send_events(bot, user, date=None, category=None, category_name=None):
    # Getting events from cache and sending

    if category:
        data = get_events(date, category, category_name)
    else:
        data = get_events(date)

    if data:
        await send_message(bot=bot, message=data, user=user)


async def get_and_send_cinema(bot, user, date=None):
    # Getting cinema from cache and sending

    if date:
        data = get_cinema(date)
    else:
        data = get_cinema()

    if data:
        await send_message(bot=bot, message=data, user=user)


async def send_cinema(event, bot, delta=None):
    """Function to send events by category"""

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
    """Getting events from cache"""
    data = get_news(date=date)
    await send_message(bot=bot, message=data, user=user)


async def send_events_for_date(event, bot, delta, category=None):
    """Sending events for date"""

    chat_id = event.message.chat.id
    request_date = get_today() + timedelta(days=delta)
    await get_and_send_events(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'), category=category)
    await welcome_board(bot, chat_id)


async def send_events_for_category(event, bot, delta, category, category_name):
    """Sending events for category"""

    print('send_events_for_category')
    chat_id = event.message.chat.id
    logging.warning(f'got EVENTS from {chat_id}')
    request_date = get_today() + timedelta(days=delta)
    await get_and_send_events(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'), category=category,
                              category_name=category_name)
    await welcome_board(bot, chat_id)


def get_today():
    """Get current Moscow time"""

    moscow = timezone('Europe/Moscow')
    moscow_time = datetime.now(moscow)

    return moscow_time


def save_user_to_mongo(user_id):
    """Add new user to MongoDB"""

    new_user = {'_id': user_id}
    try:
        db.users.insert_one(new_user)
    except errors.DuplicateKeyError:
        pass


def press_event(user_id):
    """Function to get sender_id from telegram event"""

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
            Button.text(CINEMA, resize=True, single_use=True),
            Button.text(CATEGORIES, resize=True, single_use=True),
            Button.text(NEWS, resize=True, single_use=True),
            Button.text(ABOUT, resize=True, single_use=True)
        ]
    ])
