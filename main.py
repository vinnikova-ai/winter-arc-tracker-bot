import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import database as db

router = Router()

def get_main_keyboard():
    # Создаем клавиатуру с вашей новой ссылкой на Cloudflare Pages
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🚀 Открыть трекер",
                web_app=WebAppInfo(url="https://vinnikova-arc-bot.pages.dev/")
            )
        ]
    ])
    return keyboard

@router.message(CommandStart())
async def cmd_start(message: Message):
    # Регистрируем пользователя в базе данных, если его там нет
    db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Добро пожаловать в твой личный трекер привычек «Мой ритм».\n"
        f"Нажимай кнопку ниже, чтобы отмечать выполнение и следить за прогрессом!",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📝 **Справка по боту:**\n\n"
        "• Нажми кнопку под сообщением, чтобы открыть визуальный трекер.\n"
        "• Все привычки, уровни и очки опыта (XP) сохраняются автоматически.\n"
        "• Раз в неделю ты можешь составить ИИ-обзор своих успехов прямо в приложении!"
    )
