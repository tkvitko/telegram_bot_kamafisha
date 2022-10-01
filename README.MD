<h1>News Telegram bot</h1>

This bot sends news and events to his users

<b>Functionality:</b>
- takes data from source in MySQL database,
- forms a message for user,
- caches all formed messages in local MongoDB to reduce requests to the source,
- sends info both by user's request and by schedule,
- stores user's list for broadcast messaging.

<b>Stack:</b>
- Telethon (Telegram API)
- pymongo
- mysql.connector (with sshtunnel)
- asyncio with aioschedule
