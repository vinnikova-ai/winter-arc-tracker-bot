import os
import logging
import asyncio
from aiogram import Bot, Dispatcher
from handlers import router
import database as db
from dotenv import load_dotenv
from aiohttp import web

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загружаем переменные окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)

# Простейший хэндлер для порта Render
async def handle_ping(request):
    return web.Response(text="Bot is running!")

# Фоновая задача для запуска веб-сервера
async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Читаем порт, который требует Render (по умолчанию 10000)
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server started on port {port}")

async def main():
    # Запускаем БД
    db.init_db()
    
    # Запускаем веб-сервер для прохождения проверки Render
    asyncio.create_task(start_web_server())
    
    # Запускаем сам процесс получения обновлений Telegram
    logging.info("Starting bot long polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
