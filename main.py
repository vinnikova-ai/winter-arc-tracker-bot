import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from handlers import router
import database as db

# 1. Проверяем токен везде: и в секретах сервера, и в локальном файле config.py
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    try:
        from config import BOT_TOKEN
    except ImportError:
        BOT_TOKEN = None

logging.basicConfig(level=logging.INFO)

async def main():
    # 2. Инициализируем базу данных
    db.init_db()
    print("База данных успешно запущена и проверена!")
    
    # 3. Настраиваем чистую сессию: в облаке Amvera интернет прямой, на ПК — прокси
    if os.getenv("BOT_TOKEN"):  # Если запущено в облаке Amvera
        session = AiohttpSession()
    else:  # Если запускаем локально на вашем ПК
        session = AiohttpSession(proxy="socks5://127.0.0.1:10808")
    
    # 4. Инициализируем бота
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()
    
    dp.include_router(router)
    
    print("Бот успешно применил настройки и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем.")
