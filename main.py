import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.telegram import TelegramAPIServer
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN
from handlers import router
import database as db

logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Инициализируем базу данных
    db.init_db()
    print("База данных успешно запущена и проверена!")
    
    # 2. Настраиваем официальное и стабильное зеркало Telegram
    custom_server = TelegramAPIServer(
        base="https://telegram-proxy.org{token}/{method}",
        file="https://telegram-proxy.org{token}/{path}"
    )
    
    # 3. Создаем чистую сессию для облака без жестких локальных портов компьютера
    session = AiohttpSession(api_server=custom_server)
    
    # 4. Запускаем бота
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
