import os
import sqlite3
import pickle
import pandas as pd
import numpy as np
import datetime
import random
import csv
import json
import secrets
from io import StringIO
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash

import database as db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Initialize database
db.init_db()

# Load trained Random Forest model
try:
    with open("study_planner_model.pkl", "rb") as f:
        model = pickle.load(f)
except Exception as e:
    model = None
    print("WARNING: study_planner_model.pkl not found or failed to load. Defaulting to heuristics.", e)

# Motivational Quotes
QUOTES = [
    ("Discipline is choosing between what you want now and what you want most.", "Abraham Lincoln"),
    ("Small daily improvements over time lead to stunning results.", "Robin Sharma"),
    ("Success is the sum of small efforts, repeated day in and day out.", "Robert Collier"),
    ("Focus on being productive instead of busy.", "Tim Ferriss"),
    ("You don't have to be extreme, just consistent.", "Unknown"),
    ("Action is the foundational key to all success.", "Pablo Picasso"),
    ("It's not that I'm so smart, it's just that I stay with problems longer.", "Albert Einstein"),
    ("The secret of your future is hidden in your daily routine.", "Mike Murdock"),
    ("Your mind is for having ideas, not holding them.", "David Allen"),
    ("Discipline beats motivation every single time.", "Namit"),
    ("Consistency is the key that unlocks potential.", "Unknown")
]

# Helper: Map subjects to stream
def get_subjects_by_class(student_class):
    if "Commerce" in student_class:
        return ["Accountancy", "Economics", "Business Studies", "Maths", "English", "Physical Education"]
    elif "Humanities" in student_class:
        return ["History", "Geography", "Political Science", "English", "Physical Education", "AI and Robotics"]
    elif "Class 10" in student_class:
        return ["Science", "Social Studies", "Maths", "English", "Hindi", "Physical Education"]
    else:  # Science Stream
        return ["Maths", "Physics", "Chemistry", "AI and Robotics", "English", "Physical Education"]

# Helper: Get subject difficulty from DB user row by index mapping
def get_subject_difficulty(user, subject_name):
    subjects = get_subjects_by_class(user['student_class'])
    try:
        idx = subjects.index(subject_name)
    except ValueError:
        return 5  # default
        
    diff_cols = [
        'maths_difficulty',
        'physics_difficulty',
        'chemistry_difficulty',
        'ai_robotics_difficulty',
        'english_difficulty',
        'physical_education_difficulty'
    ]
    return user[diff_cols[idx]]

# Helper: Calculate Productivity Score
def calculate_productivity_score(user):
    # Inputs: sleep, attendance, distraction, physical activity, test_score
    # Max score = 100
    sleep_score = min(20, (user['sleep_hours'] / 8.0) * 20) if user['sleep_hours'] <= 8 else max(0, 20 - (user['sleep_hours'] - 8) * 4)
    attendance_score = (user['attendance'] / 100.0) * 20
    distraction_score = ((10 - user['distraction_level']) / 10.0) * 20
    activity_score = min(10, (user['physical_activity'] / 2.0) * 10)
    test_score_contrib = (user['test_score'] / 100.0) * 30
    
    total = sleep_score + attendance_score + distraction_score + activity_score + test_score_contrib
    return int(max(0, min(100, total)))

# Helper: AI Prediction
def predict_study_plan(user):
    if model is None:
        # Fallback to rule-based classification if model pickle fails
        score = calculate_productivity_score(user)
        if score < 50:
            return "Heavy"
        elif score > 80:
            return "Light"
        return "Medium"
        
    # Format user data as DataFrame matching training features
    input_data = pd.DataFrame([[
        user['study_hours'],
        user['sleep_hours'],
        user['attendance'],
        user['test_score'],
        user['distraction_level'],
        user['physical_activity'],
        user['maths_difficulty'],
        user['physics_difficulty'],
        user['chemistry_difficulty'],
        user['ai_robotics_difficulty'],
        user['english_difficulty'],
        user['physical_education_difficulty']
    ]], columns=[
        'study_hours',
        'sleep_hours',
        'attendance',
        'test_score',
        'distraction_level',
        'physical_activity',
        'maths_difficulty',
        'physics_difficulty',
        'chemistry_difficulty',
        'ai_robotics_difficulty',
        'english_difficulty',
        'physical_education_difficulty'
    ])
    
    try:
        prediction = model.predict(input_data)
        return prediction[0]
    except Exception as e:
        print("Model prediction failed, falling back to heuristics:", e)
        return "Medium"

# Helper: Generate 30-Day Rotating Timetable
def generate_30_day_schedule(user_id, user):
    subjects = get_subjects_by_class(user['student_class'])
    weak_sub = user['weak_subject']
    days_left = user['days_left_exam']
    plan = predict_study_plan(user)
    
    schedule_items = []
    start_date = datetime.date.today()
    
    for day in range(1, 31):
        current_date = start_date + datetime.timedelta(days=day-1)
        date_str = current_date.strftime("%Y-%m-%d")
        
        # 1. Revision / Mock Test on Sundays
        if day % 7 == 0:
            subject = "Revision + Mock Test"
            # Adjust hours based on countdown
            if days_left < 10:
                hours = 5.0
            elif days_left < 30:
                hours = 4.0
            else:
                hours = 3.0
        # 2. Focus on weak subject on Saturdays
        elif day % 7 == 6:
            subject = weak_sub if weak_sub in subjects else subjects[0]
            hours = 2.0
            diff = get_subject_difficulty(user, subject)
            if diff >= 8: hours += 1.5
            elif diff >= 5: hours += 0.8
            # Weak subject Saturday bonus
            hours += 1.0
        # 3. Rotating subjects on weekdays
        else:
            # Simple rotation index
            sub_idx = (day - 1) % len(subjects)
            subject = subjects[sub_idx]
            
            # Base hours
            if subject == "Physical Education":
                hours = 0.5
            else:
                hours = 1.5
                
            # Difficulty tuning
            diff = get_subject_difficulty(user, subject)
            if diff >= 8: hours += 1.5
            elif diff >= 5: hours += 0.8
            
            # Weak subject boost
            if subject == weak_sub:
                hours += 1.0
                
        # 4. Model predictions adjustments
        if plan == "Heavy" and subject != "Physical Education":
            hours += 0.5
        elif plan == "Light":
            if subject == "Physical Education":
                hours += 0.5
            else:
                hours = max(0.5, hours - 0.5)
                
        # 5. Exam Countdown Intensive adjustments
        if subject != "Physical Education" and subject != "Revision + Mock Test":
            if days_left < 10:
                hours += 1.5
            elif days_left < 30:
                hours += 0.7
                
        # Clamp hours
        hours = round(max(0.5, min(8.0, hours)), 1)
        
        schedule_items.append({
            'day_number': day,
            'date_string': date_str,
            'subject': subject,
            'hours_scheduled': hours,
            'holiday_mode': 0
        })
        
    db.save_schedule(user_id, schedule_items)

# Filters / Decorators
def get_today_subject_and_hours(user_id, user):
    schedule = db.get_schedule(user_id)
    if not schedule:
        # Generate initial schedule if missing
        generate_30_day_schedule(user_id, user)
        schedule = db.get_schedule(user_id)
        
    # Get day index based on user logs count or relative date
    logs = db.get_user_logs(user_id)
    # Day count = logs completed mod 30
    day_idx = len(logs) % 30
    if day_idx < len(schedule):
        today_row = schedule[day_idx]
        hours = today_row['hours_scheduled']
        # If holiday mode activated for the day, cut hours in half
        if today_row['holiday_mode']:
            hours = round(hours * 0.5, 1)
        return today_row['subject'], hours
    return "Revision + Mock Test", 2.0

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        
        user = db.get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['name'] = user['name']
            session['class'] = user['student_class']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password.")
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        username = request.form['username'].strip()
        password = request.form['password']
        student_class = request.form['student_class']
        
        # Check if username exists
        existing = db.get_user_by_username(username)
        if existing:
            flash("Username already taken.")
            return render_template('register.html')
            
        user_id = db.create_user(username, password, name, student_class)
        if user_id:
            session['user_id'] = user_id
            session['name'] = name
            session['class'] = student_class
            
            # Generate default schedule
            user = db.get_user_by_id(user_id)
            generate_30_day_schedule(user_id, user)
            
            return redirect(url_for('dashboard'))
        else:
            flash("Database registration failed.")
            
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    
    productivity = calculate_productivity_score(user)
    today_sub, today_hrs = get_today_subject_and_hours(user_id, user)
    
    # Completed pomodoros count today
    logs = db.get_user_logs(user_id)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    today_log = next((l for l in logs if l['log_date'] == today_str), None)
    pomodoros = today_log['completed_pomodoros'] if today_log else 0
    
    # Pick a random quote
    random.seed(datetime.date.today().toordinal())
    quote = random.choice(QUOTES)
    
    return render_template(
        'dashboard.html', 
        active_page='dashboard',
        user=user,
        name=user['name'],
        productivity_score=productivity,
        today_subject=today_sub,
        today_hours=today_hrs,
        pomodoros_completed=pomodoros,
        quote_text=quote[0],
        quote_author=quote[1]
    )

@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    schedule = db.get_schedule(user_id)
    
    # Process schedule list to reflect holiday mode halving
    processed_schedule = []
    for item in schedule:
        hours = item['hours_scheduled']
        if item['holiday_mode']:
            hours = round(hours * 0.5, 1)
        processed_schedule.append({
            'day_number': item['day_number'],
            'date_string': item['date_string'],
            'subject': item['subject'],
            'hours_scheduled': hours,
            'holiday_mode': item['holiday_mode']
        })
        
    return render_template(
        'calendar.html',
        active_page='calendar',
        user=user,
        schedule=processed_schedule
    )

@app.route('/regenerate_schedule', methods=['POST'])
def regenerate_schedule():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    
    # Update profile tuning parameters
    profile_data = {
        'mode': request.form['mode'],
        'days_left_exam': int(request.form['days_left']),
        'weak_subject': request.form['weak_subject'],
        'maths_difficulty': int(request.form['maths_diff']),
        'physics_difficulty': int(request.form['physics_diff']),
        'chemistry_difficulty': int(request.form['chemistry_diff']),
        'ai_robotics_difficulty': int(request.form['ai_diff']),
        'english_difficulty': int(request.form['english_diff']),
        'physical_education_difficulty': int(request.form['pe_diff'])
    }
    
    db.update_user_profile(user_id, profile_data)
    user = db.get_user_by_id(user_id)
    
    # Regenerate 30-day timetable
    generate_30_day_schedule(user_id, user)
    
    flash("Study schedule regenerated successfully!")
    return redirect(url_for('calendar'))

@app.route('/progress')
def progress():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    logs = db.get_user_logs(user_id)
    return render_template('progress.html', active_page='progress', logs=logs)

@app.route('/log_progress', methods=['POST'])
def log_progress():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    log_date = request.form['log_date']
    study_hours = float(request.form['study_hours'])
    sleep_hours = float(request.form['sleep_hours'])
    attendance = float(request.form['attendance'])
    distraction = int(request.form['distraction_level'])
    activity = float(request.form['physical_activity'])
    test_score = float(request.form['test_score'])
    
    # Save to SQLite daily logs
    db.add_daily_log(
        user_id, log_date, study_hours, sleep_hours, attendance, distraction, activity, test_score
    )
    
    # Sync user profile details to match latest logged stats dynamically
    profile_update = {
        'study_hours': study_hours,
        'sleep_hours': sleep_hours,
        'attendance': attendance,
        'distraction_level': distraction,
        'physical_activity': activity,
        'test_score': test_score
    }
    db.update_user_profile(user_id, profile_update)
    
    flash("Daily progress saved and AI profile synchronized!")
    return redirect(url_for('progress'))

@app.route('/ai-advisor')
def ai_advisor():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    
    # Run Random Forest classifier prediction
    plan = predict_study_plan(user)
    today_sub, _ = get_today_subject_and_hours(user_id, user)
    
    return render_template(
        'ai_advisor.html',
        active_page='ai_advisor',
        user=user,
        study_plan=plan,
        today_subject=today_sub
    )

# API: Toggle Holiday Mode
@app.route('/api/toggle_holiday/<int:day_number>', methods=['POST'])
def api_toggle_holiday(day_number):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    user_id = session['user_id']
    schedule = db.get_schedule(user_id)
    
    day_row = next((d for d in schedule if d['day_number'] == day_number), None)
    if not day_row:
        return jsonify({'success': False, 'error': 'Day not found'}), 404
        
    # Toggle (0 -> 1, 1 -> 0)
    new_mode = 0 if day_row['holiday_mode'] else 1
    db.update_day_holiday_mode(user_id, day_number, new_mode)
    
    return jsonify({'success': True, 'holiday_mode': new_mode})

# API: Pomodoro Log
@app.route('/api/log_pomodoro', methods=['POST'])
def api_log_pomodoro():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    user_id = session['user_id']
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    user = db.get_user_by_id(user_id)
    
    # Fetch today's log or create default
    logs = db.get_user_logs(user_id)
    today_log = next((l for l in logs if l['log_date'] == today_str), None)
    
    if today_log:
        count = today_log['completed_pomodoros'] + 1
        db.add_daily_log(
            user_id,
            today_str,
            today_log['study_hours_completed'] + 0.4, # add 25 min study contribution
            today_log['sleep_hours'],
            today_log['attendance'],
            today_log['distraction_level'],
            today_log['physical_activity'],
            today_log['test_score'],
            count
        )
    else:
        count = 1
        # Use profile standards if no log today
        db.add_daily_log(
            user_id,
            today_str,
            user['study_hours'] + 0.4,
            user['sleep_hours'],
            user['attendance'],
            user['distraction_level'],
            user['physical_activity'],
            user['test_score'],
            count
        )
        
    # Refetch user to get updated streak
    updated_user = db.get_user_by_id(user_id)
    
    return jsonify({'success': True, 'today_count': count, 'streak': updated_user['streak']})

# API: Progress data for Chart.js
@app.route('/api/progress_data')
def api_progress_data():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
        
    user_id = session['user_id']
    user = db.get_user_by_id(user_id)
    logs = db.get_user_logs(user_id)
    schedule = db.get_schedule(user_id)
    
    # 1. Completed vs Scheduled hours
    study_dates = []
    hours_completed = []
    hours_scheduled = []
    
    # Align logs with schedules
    # We take matching dates or indices
    for i, log in enumerate(logs[-10:]): # past 10 logs
        study_dates.append(log['log_date'])
        hours_completed.append(log['study_hours_completed'])
        
        # get scheduled hours matching index mod 30
        sched_idx = i % 30
        if sched_idx < len(schedule):
            hours_scheduled.append(schedule[sched_idx]['hours_scheduled'])
        else:
            hours_scheduled.append(4.0)
            
    # 2. Subject difficulties
    subjects = get_subjects_by_class(user['student_class'])
    difficulties = [get_subject_difficulty(user, sub) for sub in subjects]
    
    # 3. Productivity score trend
    productivity_dates = []
    productivity_scores = []
    for log in logs[-15:]: # past 15 logs
        productivity_dates.append(log['log_date'])
        # Create a mock user dict to pass to score calculator
        temp_user = {
            'sleep_hours': log['sleep_hours'],
            'attendance': log['attendance'],
            'distraction_level': log['distraction_level'],
            'physical_activity': log['physical_activity'],
            'test_score': log['test_score']
        }
        productivity_scores.append(calculate_productivity_score(temp_user))
        
    return jsonify({
        'study_dates': study_dates,
        'hours_completed': hours_completed,
        'hours_scheduled': hours_scheduled,
        'subjects': subjects,
        'difficulties': difficulties,
        'productivity_dates': productivity_dates,
        'productivity_scores': productivity_scores
    })

# CSV / JSON Timetable Exports
@app.route('/export/csv')
def export_csv():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    schedule = db.get_schedule(user_id)
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Day Number', 'Date', 'Subject Focus', 'Hours Scheduled', 'Holiday Mode Active'])
    
    for row in schedule:
        hours = row['hours_scheduled']
        if row['holiday_mode']:
            hours = round(hours * 0.5, 1)
        cw.writerow([row['day_number'], row['date_string'], row['subject'], hours, 'YES' if row['holiday_mode'] else 'NO'])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=study_schedule.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/export/json')
def export_json():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    schedule = db.get_schedule(user_id)
    
    data = []
    for row in schedule:
        hours = row['hours_scheduled']
        if row['holiday_mode']:
            hours = round(hours * 0.5, 1)
        data.append({
            'day_number': row['day_number'],
            'date_string': row['date_string'],
            'subject': row['subject'],
            'hours_scheduled': hours,
            'holiday_mode_active': True if row['holiday_mode'] else False
        })
        
    response = make_response(json.dumps(data, indent=2))
    response.headers["Content-Disposition"] = "attachment; filename=study_schedule.json"
    response.headers["Content-type"] = "application/json"
    return response

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    # Running locally
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    app.run(debug=True)
