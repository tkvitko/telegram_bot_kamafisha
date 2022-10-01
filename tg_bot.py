#!/usr/bin/python3.6

import configparser
import logging

from telethon import TelegramClient, events
from telethon.tl.custom import Button

from bot_functions.functions import welcome_board, save_user_to_mongo, get_today, get_and_send_news, \
    send_events_for_date, get_categories_list, press_event, send_events_for_category, send_cinema, send_message
from bot_functions.strings import *

logging.basicConfig(filename='bot.log')


def work_with_chat(api_id, api_hash, bot_token):
    bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

    @bot.on(events.NewMessage(pattern='/start'))
    async def handler(event):
        """User sent /start"""

        chat_id = event.message.chat.id
        logging.warning(f'got /start from {chat_id}')
        await welcome_board(bot, chat_id)
        save_user_to_mongo(chat_id)

    @bot.on(events.NewMessage(pattern=NEWS))
    async def handler(event):
        """New for today"""

        chat_id = event.message.chat.id
        logging.warning(f'got NEWS from {chat_id}')
        request_date = get_today()
        await get_and_send_news(bot=bot, user=chat_id, date=request_date.strftime('%Y-%m-%d'))
        # await get_and_send_news(bot=bot, user=chat_id, date='2020-12-18')
        await welcome_board(bot, chat_id)

    @bot.on(events.NewMessage(pattern=ABOUT))
    async def handler(event):
        """About bot"""

        chat_id = event.message.chat.id
        logging.warning(f'got ABOUT from {chat_id}')
        await bot.send_message(chat_id, ABOUT_TEXT)
        await welcome_board(bot, chat_id)

    @bot.on(events.NewMessage(pattern=TODAY))
    async def handler(event):
        """Events for today"""

        await send_events_for_date(event, bot, delta=0)

    @bot.on(events.NewMessage(pattern=TOMORROW))
    async def handler(event):
        """Events for tomorrow"""

        await send_events_for_date(event, bot, delta=1)

    @bot.on(events.NewMessage(pattern=AFTER_TOMORROW))
    async def handler(event):
        """Events for the day after today"""

        await send_events_for_date(event, bot, delta=2)

    @bot.on(events.NewMessage(pattern=CATEGORIES))
    async def handler(event):
        """Events by category"""

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

    @bot.on(events.NewMessage(pattern=CINEMA))
    async def handler(event):
        """Cinemas for date"""

        sender = await event.get_sender()
        sender_id = sender.id
        chat_id = event.message.chat.id
        logging.warning(f'got CINEMA from {chat_id}')

        cinema_days_list = {
            'Сегодня': b'0',
            'Завтра': b'1',
            'Послезавтра': b'2',
            'Все': b'-1'
        }

        buttons = [[Button.inline(k, v)] for k, v in cinema_days_list.items()]

        async with bot.conversation(chat_id) as conv:
            await conv.send_message('Выберите дату',
                                    buttons=buttons)

            press = await conv.wait_event(press_event(sender_id))

            for k, v in cinema_days_list.items():
                if press.data == v:
                    print(press.data)
                    if press.data == b'-1':
                        await send_cinema(event, bot)
                    else:
                        await send_cinema(event, bot, delta=int(v))

    @bot.on(events.NewMessage(pattern='/send_admin_message'))
    async def handler(event):
        """Sending admin message to users"""

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
