import asyncio
import logging
 
from aiogram import Bot, Dispatcher
 
from config import BOT_TOKEN
from handlers import router
import database as db
 
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