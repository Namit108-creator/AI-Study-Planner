import pandas as pd
import numpy as np

# Seed for reproducibility
np.random.seed(42)

n_samples = 500

# Generate random but realistic data
study_hours = np.random.uniform(1.0, 10.0, n_samples)
sleep_hours = np.random.uniform(4.0, 9.5, n_samples)
attendance = np.random.uniform(50.0, 100.0, n_samples)
test_score = np.random.uniform(30.0, 100.0, n_samples)
distraction_level = np.random.randint(1, 11, n_samples)
physical_activity = np.random.uniform(0.0, 4.0, n_samples)

maths = np.random.randint(1, 11, n_samples)
physics = np.random.randint(1, 11, n_samples)
chemistry = np.random.randint(1, 11, n_samples)
ai_robotics = np.random.randint(1, 11, n_samples)
english = np.random.randint(1, 11, n_samples)
pe = np.random.randint(1, 11, n_samples)

# Logic to label the study plan (Heavy, Medium, Light)
# We will compute a need-score:
# High difficulties, high distraction, low test score, low attendance, low current study hours
# -> Higher need for a "Heavy" study plan to catch up.
# Low difficulties, low distraction, high test score, high attendance, high current study hours
# -> "Light" study plan (they are already doing great).
# Otherwise -> "Medium".

study_plans = []
for i in range(n_samples):
    avg_difficulty = (maths[i] + physics[i] + chemistry[i] + ai_robotics[i] + english[i] + pe[i]) / 6.0
    
    # Calculate score representing academic pressure/need
    # Scale from 0 to 10
    score = 0.0
    
    # High average difficulty increases need
    score += (avg_difficulty / 10.0) * 3.0
    
    # High distraction increases need
    score += (distraction_level[i] / 10.0) * 1.5
    
    # Low test score increases need
    score += ((100.0 - test_score[i]) / 70.0) * 2.5
    
    # Low attendance increases need
    score += ((100.0 - attendance[i]) / 50.0) * 1.5
    
    # Low current study hours increases need
    score += ((10.0 - study_hours[i]) / 9.0) * 1.5
    
    # Determine plan based on need score
    if score >= 6.0:
        plan = "Heavy"
    elif score <= 3.8:
        plan = "Light"
    else:
        plan = "Medium"
        
    study_plans.append(plan)

# Create DataFrame
df = pd.DataFrame({
    'study_hours': study_hours,
    'sleep_hours': sleep_hours,
    'attendance': attendance,
    'test_score': test_score,
    'distraction_level': distraction_level,
    'physical_activity': physical_activity,
    'maths_difficulty': maths,
    'physics_difficulty': physics,
    'chemistry_difficulty': chemistry,
    'ai_robotics_difficulty': ai_robotics,
    'english_difficulty': english,
    'physical_education_difficulty': pe,
    'study_plan': study_plans
})

# Save to CSV
df.to_csv("data.csv", index=False)
print(f"Generated data.csv with {n_samples} records.")
print(df['study_plan'].value_counts())
