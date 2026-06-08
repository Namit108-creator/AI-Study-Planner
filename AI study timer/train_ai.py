import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import pickle

# Load dataset
file = pd.read_csv("data.csv")

# Input features
X = file[[
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
]]

# Output
y = file['study_plan']

# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# Create AI model - Random Forest Classifier
model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)

# Train AI
model.fit(X_train, y_train)

# Predictions
predictions = model.predict(X_test)

# Evaluation
accuracy = accuracy_score(y_test, predictions)
cv_scores = cross_val_score(model, X, y, cv=5)

print("===== AI TRAINING COMPLETE =====")
print(f"Model Accuracy on Test Set: {accuracy:.4f}")
print(f"5-Fold Cross Validation Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
print("\nClassification Report:")
print(classification_report(y_test, predictions))

# Save model
with open("study_planner_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("Advanced AI Random Forest model saved successfully!")