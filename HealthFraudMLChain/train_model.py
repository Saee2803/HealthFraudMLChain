import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import pickle


df = pd.read_csv("insurance.csv")


df = df.drop(columns=["Patient ID"])


df["Date Admitted"] = pd.to_datetime(df["Date Admitted"], format="%d-%m-%Y")
df["Date Discharged"] = pd.to_datetime(df["Date Discharged"], format="%d-%m-%Y")
df["Stay Duration"] = (df["Date Discharged"] - df["Date Admitted"]).dt.days


y = df["Fraud Type"]
X = df.drop(columns=["Fraud Type", "Date Admitted", "Date Discharged"])

# 5. Encode features
X = pd.get_dummies(X)

# 6. Encode target
le = LabelEncoder()
y = le.fit_transform(y)

# Print class distribution for debugging
print("Fraud Type classes:", le.classes_)
print("Class distribution:")
for i, cls in enumerate(le.classes_):
    count = (y == i).sum()
    print(f"  {cls}: {count} ({count/len(y)*100:.1f}%)")

# 7. Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 8. Train model
# FIX: Use class_weight="balanced" to handle class imbalance
# FIX: Increase n_estimators for better probability calibration
# FIX: Set random_state for reproducibility
model = RandomForestClassifier(
    n_estimators=300,          # More trees for better calibration
    class_weight="balanced",   # Handle class imbalance
    random_state=42,           # Reproducibility
    max_depth=15,              # Prevent overfitting
    min_samples_split=5        # Minimum samples to split
)
model.fit(X_train, y_train)

print("Accuracy:", model.score(X_test, y_test))

# 9. Save model + encoder + columns
with open("fraud_model.pkl", "wb") as f:
    pickle.dump((model, le, X.columns.tolist()), f)

print("✅ Model saved to fraud_model.pkl")
