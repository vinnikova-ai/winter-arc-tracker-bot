import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN
from handlers import router
import database as db

# Включаем логирование
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Инициализируем базу данных локально
    db.init_db()
    print("База данных успешно запущена и проверена!")

    # 2. Настраиваем чистую сессию с прокси для вашего Xray Tun
    session = AiohttpSession(proxy="socks5://127.0.0.1:10808")

    # 3. Запускаем бота (токен берется из вашего файла config.py)
    bot = Bot(token=BOT_TOKEN, session=session)
    dp = Dispatcher()
    dp.include_router(router)

    print("Бот успешно запущен локально и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем.")
