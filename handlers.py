from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import database as db

router = Router()

class GoalStates(StatesGroup):
    waiting_for_name = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.username)
    
    kb = [
        [types.KeyboardButton(text="📝 Добавить цель")],
        [types.KeyboardButton(text="✅ Отметиться за сегодня"), types.KeyboardButton(text="📊 Мой прогресс")],
        [types.KeyboardButton(text="❌ Удалить цель")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋 Добро пожаловать на твой личный **Winter Arc**!\n"
        f"Марафон идет с 5 октября по 31 декабря 2026 года.\n"
        f"Используй меню для управления привычками:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@router.message(F.text == "📝 Добавить цель")
async def start_adding_goal(message: types.Message, state: FSMContext):
    await state.set_state(GoalStates.waiting_for_name)
    await message.answer("Введите название вашей новой цели/привычки:")

@router.message(GoalStates.waiting_for_name)
async def process_goal_name(message: types.Message, state: FSMContext):
    goal_title = message.text.strip()
    db.add_goal(message.from_user.id, goal_title)
    await state.clear()
    await message.answer(f"✅ Отлично! Привычка «{goal_title}» успешно добавлена в программу вызова.")

@router.message(F.text == "✅ Отметиться за сегодня")
async def show_goals_for_logging(message: types.Message):
    user_goals = db.get_user_goals(message.from_user.id)
    if not user_goals:
        await message.answer("У тебя пока нет созданных целей. Сначала нажми '📝 Добавить цель'.")
        return
    builder = InlineKeyboardBuilder()
    for goal_id, title in user_goals:
        builder.button(text=title, callback_data=f"check_{goal_id}")
    builder.adjust(1)
    await message.answer("Какую цель или привычку ты выполнил(а) сегодня?", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("check_"))
async def process_goal_check(callback: types.CallbackQuery):
    goal_id = int(callback.data.split("_")[1])
    is_logged = db.log_today(goal_id)
    if is_logged:
        await callback.message.answer("🎉 Отлично! День засчитан в твою копилку дисциплины!")
    else:
        await callback.message.answer("По этой привычке ты уже отмечался сегодня. Всё под контролем! 😎")
    await callback.answer()

@router.message(F.text == "❌ Удалить цель")
async def show_goals_for_deletion(message: types.Message):
    user_goals = db.get_user_goals(message.from_user.id)
    if not user_goals:
        await message.answer("Список целей пуст.")
        return
    builder = InlineKeyboardBuilder()
    for goal_id, title in user_goals:
        builder.button(text=f"🗑️ {title}", callback_data=f"delete_{goal_id}")
    builder.adjust(1)
    await message.answer("Выбери цель, которую хочешь удалить:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("delete_"))
async def process_goal_deletion(callback: types.CallbackQuery):
    goal_id = int(callback.data.split("_")[1])
    db.delete_goal_from_db(goal_id)
    await callback.message.answer("🗑️ Привычка удалена из программы вызова.")
    await callback.answer()

# --- СТАТИСТИКА В СТИЛЕ WINTER ARC % ---
@router.message(F.text == "📊 Мой прогресс")
async def show_progress(message: types.Message):
    user_goals = db.get_user_goals(message.from_user.id)
    
    # Даты марафона Winter Arc
    start_date = datetime(2026, 10, 5)
    end_date = datetime(2026, 12, 31)
    now = datetime.now()
    
    total_days = (end_date - start_date).days + 1  # Всего 88 дней
    passed_days = (now - start_date).days + 1      # Прошло дней
    left_days = total_days - passed_days           # Осталось дней
    
    if passed_days > total_days:
        passed_days = total_days
        left_days = 0

    if not user_goals:
        await message.answer("У тебя пока нет активных привычек для расчета прогресса.")
        return
        
    # Собираем красивый заголовок как на дашборде
    response_text = (
        f"❄️ **Winter Arc Вызов**\n"
        f"📅 День **{passed_days}** из **{total_days}**\n\n"
        f"📈 **Прошло:** {passed_days} дн. | **Осталось:** {left_days} дн.\n"
        f"🗓️ *С 5 октября до 31 декабря 2026*\n"
        f"─────────────────────\n"
        f"📋 **Твои ежедневные привычки (% выполнения):**\n\n"
    )
    
    # Подсчитываем строки целей с процентами
    for goal_id, title in user_goals:
        percentage, completed = db.get_goal_percentage(goal_id)
        
        # Красивый визуальный индикатор (прогресс-бар из смайликов)
        if percentage >= 80:
            status_emoji = "🟢"
        elif percentage >= 50:
            status_emoji = "🟡"
        else:
            status_emoji = "🔴"
            
        response_text += f"{status_emoji} **{title}**\n"
        response_text += f"└ Прогресс: `{percentage}%` (Выполнено: {completed} дн.)\n\n"
        
    await message.answer(response_text, parse_mode="Markdown")