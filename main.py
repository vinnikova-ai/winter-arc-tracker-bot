import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN
from handlers import router
from apscheduler.schedulers.asyncio import AsyncIOScheduler # Импортируем планировщик
import database as db

logging.basicConfig(level=logging.INFO)

# Глобальный объект бота, чтобы планировщик мог отправлять сообщения
session = AiohttpSession(proxy="socks5://127.0.0.1:10808")
bot = Bot(token=BOT_TOKEN, session=session)

async def send_evening_reminders():
    """Функция автоматической вечерней рассылки напоминаний"""
    users = db.get_all_users()
    for user_id in users:
        try:
            await bot.send_message(
                chat_id=user_id,
                text="🔔 **Winter Arc Напоминание!**\n\n"
                     "Вечер уже наступил! Не забудь нажать кнопку **«✅ Отметиться за сегодня»** и внести свой вклад в дисциплину. Каждая галочка приближает тебя к цели! ❄️",
                parse_mode="Markdown"
            )
            print(f"Напоминание успешно отправлено пользователю {user_id}")
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def main():
    db.init_db()
    print("База данных успешно запущена и проверена!")
    
    # Настраиваем планировщик напоминаний
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    # Ровно в 21:00 каждый день будет вызываться функция рассылки
    scheduler.add_job(send_evening_reminders, "cron", hour=21, minute=0)
    scheduler.start()
    print("Планировщик напоминаний успешно запущен на 21:00 (МСК)...")
    
    dp = Dispatcher()
    dp.include_router(router)

    print("Бот готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем.")
