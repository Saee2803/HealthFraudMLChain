import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pickle

# Load the data
data = pd.read_csv('../data/health_insurance_claims.csv')

print("Columns in dataset:", list(data.columns))

# Map categorical variables if they exist
if 'sex' in data.columns:
    data['sex'] = data['sex'].map({'male': 1, 'female': 0})

if 'smoker' in data.columns:
    data['smoker'] = data['smoker'].map({'yes': 1, 'no': 0})

# Optional: encode 'region' if it exists
if 'region' in data.columns:
    data = pd.get_dummies(data, columns=['region'], drop_first=True)

# Drop rows with missing values
data = data.dropna()

# Define X and y
X = data.drop(['is_fraud'], axis=1)
y = data['is_fraud']

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
clf = RandomForestClassifier()
clf.fit(X_train, y_train)

# Save model
with open('fraud_model.pkl', 'wb') as f:
    pickle.dump(clf, f)

print("✅ Model trained and saved successfully.")
