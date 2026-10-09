import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    exit("Ошибка: Токен бота (BOT_TOKEN) не найден в файле .env!")
