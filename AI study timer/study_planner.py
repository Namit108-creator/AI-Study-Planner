import pickle
import pandas as pd

# Load trained AI model
with open("study_planner_model.pkl", "rb") as f:
    model = pickle.load(f)

print("===== ISC AI STUDY PLANNER =====")
print()

# Student details
name = input("Enter your name: ")
student_class = input("Enter your class: ")

print()
print("===== DAILY HABITS =====")

study_hours = float(input("Daily study hours: "))
sleep_hours = float(input("Sleep hours per day: "))
attendance = float(input("Attendance percentage: "))
test_score = float(input("Latest average test score: "))
distraction_level = float(input("Distraction level (1-10): "))
physical_activity = float(input("Daily physical activity hours: "))

print()
print("===== SUBJECT DIFFICULTY ANALYSIS =====")
print("Rate each subject difficulty from 1 to 10")

maths = int(input("Maths difficulty: "))
physics = int(input("Physics difficulty: "))
chemistry = int(input("Chemistry difficulty: "))
ai_robotics = int(input("AI and Robotics difficulty: "))
english = int(input("English difficulty: "))
physical_education = int(input("Physical Education difficulty: "))

weak_subject = input("Which subject do you find the weakest? ")

# Create dataframe for prediction
input_data = pd.DataFrame([[
    study_hours,
    sleep_hours,
    attendance,
    test_score,
    distraction_level,
    physical_activity,
    maths,
    physics,
    chemistry,
    ai_robotics,
    english,
    physical_education
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

# AI prediction
result = model.predict(input_data)

plan = result[0]

print()
print("===== AI RESULT =====")
print(f"Hello {name}!")
print(f"Class: {student_class}")
print("Recommended Study Plan:", plan)

print()

# Base study hours
subject_hours = {
    "Maths": 1,
    "Physics": 1,
    "Chemistry": 1,
    "AI and Robotics": 1,
    "English": 1,
    "Physical Education": 0.5
}

# Difficulty adjustment
difficulties = {
    "Maths": maths,
    "Physics": physics,
    "Chemistry": chemistry,
    "AI and Robotics": ai_robotics,
    "English": english,
    "Physical Education": physical_education
}

for subject in difficulties:
    if difficulties[subject] >= 8:
        subject_hours[subject] += 2
    elif difficulties[subject] >= 5:
        subject_hours[subject] += 1

# Weak subject bonus
if weak_subject in subject_hours:
    subject_hours[weak_subject] += 1

# Heavy study plan adjustments
if plan == "Heavy":
    for subject in subject_hours:
        subject_hours[subject] += 0.5

# Light study plan adjustments
elif plan == "Light":
    subject_hours["Physical Education"] += 0.5

print("===== WEEKLY AI STUDY SCHEDULE =====")
print()

print("+-----------+----------------------+----------------+")
print("| Day       | Subject              | Study Hours    |")
print("+-----------+----------------------+----------------+")

schedule = [
    ("Monday", "Maths"),
    ("Tuesday", "Physics"),
    ("Wednesday", "Chemistry"),
    ("Thursday", "AI and Robotics"),
    ("Friday", "English"),
    ("Saturday", weak_subject),
    ("Sunday", "Revision + Mock Test")
]

for day, subject in schedule:

    if subject == "Revision + Mock Test":
        hours = 3
    else:
        hours = subject_hours.get(subject, 2)

    print(f"| {day:<9} | {subject:<20} | {hours} hours       |")

print("+-----------+----------------------+----------------+")

print()
print("===== SUBJECT-WISE STUDY HOURS =====")
print()

for subject, hours in subject_hours.items():
    print(f"{subject}: {hours} hours")

print()
print("===== AI HEALTH AND PRODUCTIVITY ADVICE =====")

if distraction_level >= 8:
    print("- Reduce social media usage")
    print("- Keep phone away while studying")

if sleep_hours < 6:
    print("- Improve sleep schedule for better memory")

if attendance < 75:
    print("- Attend school more regularly")

if physical_activity < 1:
    print("- Add exercise or walking to your routine")

if test_score >= 85:
    print("- Start solving advanced ISC/JEE-level questions")

print()
print("===== FINAL AI MESSAGE =====")
print("Stay consistent and disciplined.")
print("Small daily improvements create big success.")
print("Good luck with your ISC journey!")