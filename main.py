import asyncio
import logging
 
from aiogram import Bot, Dispatcher
 
import os
import logging
from handlers import router
import database as db
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

 
async def main():
    # 1. Инициализируем базу данных
    db.init_db()
    print("База данных успешно запущена и проверена!")
 
    # 2. Создаём бота. Никаких зеркал и прокси:
    #    на Amvera Telegram доступен напрямую, а на ПК трафик идёт через VPN (режим TUN).
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
 
    # 3. Подключаем обработчики и запускаем опрос
    dp.include_router(router)
    print("Бот готов к работе...")
    await dp.start_polling(bot)
 
 
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем.")
