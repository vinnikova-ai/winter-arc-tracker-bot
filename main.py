import os
import json
import sqlite3
import threading
from datetime import date, timedelta
from urllib.parse import parse_qs, unquote

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- НАСТРОЙКИ ---
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")
WEBAPP_URL = "https://vinnikova-arc-bot.pages.dev"
DB_PATH = "tracker.db"

# --- ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ ---
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                xp INTEGER DEFAULT 0
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                color TEXT,
                created_at TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                habit_id INTEGER,
                log_date TEXT,
                PRIMARY KEY (habit_id, log_date)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                summary TEXT,
                week_start TEXT,
                week_end TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

init_db()

# --- ТЕЛЕГРАМ БОТ ---
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=["start"])
def send_welcome(message):
    name = message.from_user.first_name or "друг"
    keyboard = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="Открыть трекер",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    keyboard.add(button)
    bot.send_message(
        message.chat.id,
        f"Привет, {name}! Продолжим работать над привычками?",
        reply_markup=keyboard
    )

def run_bot():
    try:
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print("Ошибка бота:", e)

threading.Thread(target=run_bot, daemon=True).start()

# --- FASTAPI СЕРВЕР ДЛЯ WEBAPP ---
app = FastAPI(title="Habit Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HabitCreate(BaseModel):
    name: str
    color: str

def get_user_from_headers(x_telegram_init_data: str | None = None):
    if x_telegram_init_data:
        try:
            parsed = parse_qs(x_telegram_init_data)
            if "user" in parsed:
                user_data = json.loads(unquote(parsed["user"][0]))
                return user_data.get("id", 1), user_data.get("first_name", "Евгения")
        except Exception:
            pass
    return 1, "Евгения"

@app.get("/api/dashboard")
def get_dashboard(x_telegram_init_data: str | None = Header(None)):
    user_id, first_name = get_user_from_headers(x_telegram_init_data)
    today_str = date.today().isoformat()
    last_7_days = [(date.today() - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT first_name, xp FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO users (user_id, first_name, xp) VALUES (?, ?, ?)", (user_id, first_name, 0))
            conn.commit()
            xp = 0
        else:
            xp = row[1]

        level = 1 + (xp // 250)
        level_progress = xp % 250
        xp_to_next = 250 - level_progress

        c.execute("SELECT id, name, color FROM habits WHERE user_id = ?", (user_id,))
        raw_habits = c.fetchall()

        habits = []
        completed_today_count = 0

        for h_id, h_name, h_color in raw_habits:
            c.execute("SELECT log_date FROM habit_logs WHERE habit_id = ?", (h_id,))
            completed_dates = {r[0] for r in c.fetchall()}

            week_bools = [d in completed_dates for d in last_7_days]
            is_done_today = today_str in completed_dates
            if is_done_today:
                completed_today_count += 1

            streak = 0
            check_date = date.today()
            if today_str not in completed_dates:
                check_date -= timedelta(days=1)
            while check_date.isoformat() in completed_dates:
                streak += 1
                check_date -= timedelta(days=1)

            habits.append({
                "id": h_id,
                "name": h_name,
                "color": h_color,
                "completed_today": is_done_today,
                "streak": streak,
                "week": week_bools
            })

        c.execute("""
            SELECT l.log_date, COUNT(*) 
            FROM habit_logs l 
            JOIN habits h ON l.habit_id = h.id 
            WHERE h.user_id = ? AND l.log_date >= ?
            GROUP BY l.log_date
        """, (user_id, last_7_days[0]))
        counts_by_day = {d: 0 for d in last_7_days}
        for log_date, count in c.fetchall():
            if log_date in counts_by_day:
                counts_by_day[log_date] = count

        total_possible = len(habits) * 7
        total_done = sum(counts_by_day.values())
        weekly_rate = round((total_done / total_possible * 100)) if total_possible > 0 else 0

        c.execute("SELECT summary, week_start, week_end FROM reports WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
        rep = c.fetchone()
        latest_report = None
        if rep:
            latest_report = {"summary": rep[0], "week_start": rep[1], "week_end": rep[2]}

    return {
        "user": {
            "first_name": first_name,
            "xp": xp,
            "level": level,
            "xp_to_next_level": xp_to_next,
            "level_progress": level_progress
        },
        "today": today_str,
        "completed_today": completed_today_count,
        "total_habits": len(habits),
        "is_demo": (x_telegram_init_data is None),
        "habits": habits,
        "week": last_7_days,
        "weekly_rate": weekly_rate,
        "completion_by_day": counts_by_day,
        "latest_report": latest_report
    }

@app.post("/api/habits")
def add_habit(habit: HabitCreate, x_telegram_init_data: str | None = Header(None)):
    user_id, _ = get_user_from_headers(x_telegram_init_data)
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO habits (user_id, name, color, created_at) VALUES (?, ?, ?, ?)",
                  (user_id, habit.name, habit.color, date.today().isoformat()))
        conn.commit()
    return {"status": "ok"}

@app.post("/api/habits/{habit_id}/toggle")
def toggle_habit(habit_id: int, x_telegram_init_data: str | None = Header(None)):
    user_id, _ = get_user_from_headers(x_telegram_init_data)
    today_str = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT 1 FROM habit_logs WHERE habit_id = ? AND log_date = ?", (habit_id, today_str))
        exists = c.fetchone()
        if exists:
            c.execute("DELETE FROM habit_logs WHERE habit_id = ? AND log_date = ?", (habit_id, today_str))
            c.execute("UPDATE users SET xp = MAX(0, xp - 25) WHERE user_id = ?", (user_id,))
        else:
            c.execute("INSERT INTO habit_logs (habit_id, log_date) VALUES (?, ?)", (habit_id, today_str))
            c.execute("UPDATE users SET xp = xp + 25 WHERE user_id = ?", (user_id,))
        conn.commit()
    return {"status": "ok"}

@app.delete("/api/habits/{habit_id}")
def delete_habit(habit_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM habits WHERE id = ?", (habit_id,))
        c.execute("DELETE FROM habit_logs WHERE habit_id = ?", (habit_id,))
        conn.commit()
    return {"status": "ok"}

@app.post("/api/reports/generate")
def generate_report(x_telegram_init_data: str | None = Header(None)):
    user_id, _ = get_user_from_headers(x_telegram_init_data)
    start_date = (date.today() - timedelta(days=7)).isoformat()
    end_date = date.today().isoformat()
    summary = "Отличная неделя! Вы продолжаете закреплять привычки и двигаться вперед. Держите этот ритм!"
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO reports (user_id, summary, week_start, week_end, created_at) VALUES (?, ?, ?, ?, ?)",
                  (user_id, summary, start_date, end_date, date.today().isoformat()))
        conn.commit()
    return {"summary": summary, "week_start": start_date, "week_end": end_date}
