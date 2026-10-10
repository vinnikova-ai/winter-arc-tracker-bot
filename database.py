import sqlite3
from datetime import datetime
import os

# Умный путь от Клоуда: если папка /data существует (в облаке) — сохраняем туда.
# Если папки нет (на вашем ПК) — база автоматически создастся прямо в папке проекта.
DB_NAME = "/data/database.db" if os.path.isdir("/data") else "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Таблица целей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            goal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # 3. Таблица ежедневных отметок
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER,
            date TEXT,
            status INTEGER,
            FOREIGN KEY (goal_id) REFERENCES goals(goal_id),
            UNIQUE(goal_id, date)
        )
    ''')
    
    conn.commit()
    conn.close()

def add_user(user_id: int, username: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def add_goal(user_id: int, title: str):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO goals (user_id, title) VALUES (?, ?)", (user_id, title))
    conn.commit()
    conn.close()

def get_user_goals(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT goal_id, title FROM goals WHERE user_id = ?", (user_id,))
    goals = cursor.fetchall()
    conn.close()
    return goals

def log_today(goal_id: int):
    """Ставит отметку выполнения на сегодняшнюю дату"""
    today_date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO logs (goal_id, date, status) VALUES (?, ?, 1)", (goal_id, today_date))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def get_goal_stats(goal_id: int):
    """Считает общее количество успешных дней для цели"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM logs WHERE goal_id = ? AND status = 1", (goal_id,))
    count = cursor.fetchone()[0] # Забираем число напрямую
    conn.close()
    return count

def get_goal_percentage(goal_id: int):
    """Считает процент выполнения цели относительно прошедших дней Winter Arc"""
    start_date = datetime(2026, 10, 5)
    now = datetime.now()
    
    passed_days = (now - start_date).days + 1
    if passed_days <= 0:
        passed_days = 1
        
    completed_days = get_goal_stats(goal_id)
    percentage = int((completed_days / passed_days) * 100)
    return percentage, completed_days

def delete_goal_from_db(goal_id: int):
    """Удаляет цель и все связанные с ней отметки"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM logs WHERE goal_id = ?", (goal_id,))
    cursor.execute("DELETE FROM goals WHERE goal_id = ?", (goal_id,))
    conn.commit()
    conn.close()

def get_all_users():
    """Возвращает список всех ID пользователей для рассылки напоминаний"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users
