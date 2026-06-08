import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'study_planner.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            student_class TEXT NOT NULL,
            mode TEXT DEFAULT 'Boards', -- Boards, ISC, JEE
            days_left_exam INTEGER DEFAULT 30,
            weak_subject TEXT DEFAULT 'Maths',
            study_hours FLOAT DEFAULT 4.0,
            sleep_hours FLOAT DEFAULT 8.0,
            attendance FLOAT DEFAULT 80.0,
            test_score FLOAT DEFAULT 75.0,
            distraction_level INTEGER DEFAULT 5,
            physical_activity FLOAT DEFAULT 1.0,
            maths_difficulty INTEGER DEFAULT 5,
            physics_difficulty INTEGER DEFAULT 5,
            chemistry_difficulty INTEGER DEFAULT 5,
            ai_robotics_difficulty INTEGER DEFAULT 5,
            english_difficulty INTEGER DEFAULT 5,
            physical_education_difficulty INTEGER DEFAULT 5,
            streak INTEGER DEFAULT 0,
            last_activity_date TEXT
        )
    ''')
    
    # Study schedules table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            date_string TEXT NOT NULL,
            subject TEXT NOT NULL,
            hours_scheduled FLOAT NOT NULL,
            holiday_mode INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Daily logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            log_date TEXT NOT NULL,
            study_hours_completed FLOAT NOT NULL,
            sleep_hours FLOAT NOT NULL,
            attendance FLOAT NOT NULL,
            distraction_level INTEGER NOT NULL,
            physical_activity FLOAT NOT NULL,
            test_score FLOAT NOT NULL,
            completed_pomodoros INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, log_date)
        )
    ''')
    
    conn.commit()
    conn.close()

# User functions
def create_user(username, password, name, student_class):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = generate_password_hash(password)
    try:
        cursor.execute(
            'INSERT INTO users (username, password_hash, name, student_class) VALUES (?, ?, ?, ?)',
            (username, password_hash, name, student_class)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

def update_user_profile(user_id, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    keys = list(data.keys())
    values = list(data.values())
    values.append(user_id)
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    cursor.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()

# Schedule functions
def save_schedule(user_id, schedule_items):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM study_schedules WHERE user_id = ?', (user_id,))
    for item in schedule_items:
        cursor.execute(
            'INSERT INTO study_schedules (user_id, day_number, date_string, subject, hours_scheduled, holiday_mode) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, item['day_number'], item['date_string'], item['subject'], item['hours_scheduled'], item.get('holiday_mode', 0))
        )
    conn.commit()
    conn.close()

def get_schedule(user_id):
    conn = get_db_connection()
    schedule = conn.execute('SELECT * FROM study_schedules WHERE user_id = ? ORDER BY day_number ASC', (user_id,)).fetchall()
    conn.close()
    return schedule

def update_day_holiday_mode(user_id, day_number, holiday_mode):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch current subject & hours scheduled
    row = cursor.execute('SELECT subject, hours_scheduled FROM study_schedules WHERE user_id = ? AND day_number = ?', (user_id, day_number)).fetchone()
    if row:
        hours = row['hours_scheduled']
        # If toggled on (holiday), cut hours in half. If toggled off (regular), restore original or just cut/restore relative.
        # However, to be robust, we'll store holiday_mode flag and we will let the UI handle the actual view logic,
        # or we update hours. Let's update the holiday_mode field itself first.
        cursor.execute(
            'UPDATE study_schedules SET holiday_mode = ? WHERE user_id = ? AND day_number = ?',
            (holiday_mode, user_id, day_number)
        )
    conn.commit()
    conn.close()

# Progress log functions
def add_daily_log(user_id, log_date, study_hours_completed, sleep_hours, attendance, distraction_level, physical_activity, test_score, completed_pomodoros=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            '''INSERT OR REPLACE INTO daily_logs 
               (user_id, log_date, study_hours_completed, sleep_hours, attendance, distraction_level, physical_activity, test_score, completed_pomodoros) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, log_date, study_hours_completed, sleep_hours, attendance, distraction_level, physical_activity, test_score, completed_pomodoros)
        )
        conn.commit()
        # Update streak logic
        update_streak(user_id, log_date, cursor)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print("Error saving log:", e)
        conn.close()
        return False

def get_user_logs(user_id):
    conn = get_db_connection()
    logs = conn.execute('SELECT * FROM daily_logs WHERE user_id = ? ORDER BY log_date ASC', (user_id,)).fetchall()
    conn.close()
    return logs

def update_streak(user_id, log_date, cursor):
    import datetime
    user = cursor.execute('SELECT streak, last_activity_date FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        return
        
    streak = user['streak']
    last_date_str = user['last_activity_date']
    
    current_date = datetime.datetime.strptime(log_date, "%Y-%m-%d").date()
    
    if last_date_str:
        try:
            last_date = datetime.datetime.strptime(last_date_str, "%Y-%m-%d").date()
            delta = current_date - last_date
            if delta.days == 1:
                streak += 1
            elif delta.days > 1:
                streak = 1
            # If delta.days == 0, keep same streak
        except Exception:
            streak = 1
    else:
        streak = 1
        
    cursor.execute('UPDATE users SET streak = ?, last_activity_date = ? WHERE id = ?', (streak, log_date, user_id))
