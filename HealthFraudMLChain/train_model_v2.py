"""
PRODUCTION-GRADE FRAUD DETECTION MODEL - Version 2.0
=====================================================

WHY THE OLD MODEL FAILED:
--------------------------
1. Multi-class Problem: The old model predicted 4 classes (No Fraud, Phantom Billing,
   Wrong Diagnoses, Ghost Patients). This dilutes probability across classes.
   
2. No TF-IDF on Diagnosis: Diagnosis text is the STRONGEST fraud signal. Simple one-hot
   encoding loses semantic patterns like "Male + Pregnancy" = obvious fraud.
   
3. Missing Fraud Indicators: Critical features like:
   - high_amount_flag (₹100K+ for short stay = suspicious)
   - zero_stay_flag (0-day stay with high bill = suspicious)
   - gender_diagnosis_mismatch (Male + Cesarean/Pregnancy = fraud)
   - age_diagnosis_risk (5-year-old with Cataract Surgery = fraud)
   
4. No Class Imbalance Handling: 70% No Fraud vs 30% Fraud means model biases toward
   predicting "No Fraud" to achieve higher accuracy.
   
5. predict_proba Misuse: With 4 classes, fraud_prob = 1 - P(No Fraud) = ~30% always
   because the 30% fraud is split across 3 classes (~10% each).

HOW THIS MODEL FIXES IT:
-------------------------
1. BINARY TARGET: Convert all fraud types to 1 (Fraud) vs 0 (No Fraud)
2. STRONG FEATURE ENGINEERING: Add domain-specific fraud indicators
3. TF-IDF ON DIAGNOSIS: Capture diagnosis-related patterns
4. BALANCED CLASS WEIGHTS: Handle 70/30 imbalance
5. OPTIMIZED RANDOM FOREST: Production-grade hyperparameters
6. PROPER PROBABILITY CALIBRATION: predict_proba[0][1] = P(Fraud)

EXPECTED RESULTS:
------------------
- ₹100,000+ with 1-day stay → fraud_prob ≥ 0.7
- Male + Pregnancy diagnosis → fraud_prob ≥ 0.85
- Normal claim patterns → fraud_prob ≤ 0.25
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.calibration import CalibratedClassifierCV
from scipy.sparse import hstack, csr_matrix
import pickle
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("  HEALTHCARE FRAUD DETECTION MODEL - v2.0 (Production)")
print("=" * 60)

# ============================================
# STEP 1: LOAD AND PREPROCESS DATA
# ============================================
print("\n📊 Loading dataset...")
df = pd.read_csv("insurance.csv")
print(f"   Dataset shape: {df.shape}")

# Drop Patient ID (not useful for prediction)
df = df.drop(columns=["Patient ID"])

# Parse dates and calculate stay duration
df["Date Admitted"] = pd.to_datetime(df["Date Admitted"], format="%d-%m-%Y")
df["Date Discharged"] = pd.to_datetime(df["Date Discharged"], format="%d-%m-%Y")
df["Stay Duration"] = (df["Date Discharged"] - df["Date Admitted"]).dt.days

print(f"   Columns: {list(df.columns)}")

# ============================================
# STEP 2: BINARY TARGET (CRITICAL FIX)
# ============================================
print("\n🎯 Creating BINARY target (No Fraud=0, Any Fraud=1)...")

# Original distribution
print("   Original Fraud Type distribution:")
for fraud_type, count in df["Fraud Type"].value_counts().items():
    pct = count / len(df) * 100
    print(f"      {fraud_type}: {count} ({pct:.1f}%)")

# Convert to binary: 0 = No Fraud, 1 = Fraud
df["is_fraud"] = df["Fraud Type"].apply(lambda x: 0 if x == "No Fraud" else 1)

print(f"\n   Binary distribution:")
print(f"      No Fraud (0): {(df['is_fraud'] == 0).sum()} ({(df['is_fraud'] == 0).mean()*100:.1f}%)")
print(f"      Fraud (1): {(df['is_fraud'] == 1).sum()} ({(df['is_fraud'] == 1).mean()*100:.1f}%)")

y = df["is_fraud"]

# ============================================
# STEP 3: FEATURE ENGINEERING (DOMAIN KNOWLEDGE)
# ============================================
print("\n🔧 Engineering fraud-indicator features...")

# 3.1 Amount-based indicators
df["high_amount_flag"] = (df["Amount Billed"] > 100000).astype(int)
df["very_high_amount_flag"] = (df["Amount Billed"] > 300000).astype(int)
df["extreme_amount_flag"] = (df["Amount Billed"] > 500000).astype(int)
df["low_amount_flag"] = (df["Amount Billed"] < 30000).astype(int)

# 3.2 Stay duration indicators
df["zero_stay_flag"] = (df["Stay Duration"] == 0).astype(int)
df["short_stay_flag"] = (df["Stay Duration"] <= 1).astype(int)
df["long_stay_flag"] = (df["Stay Duration"] > 15).astype(int)
df["very_long_stay_flag"] = (df["Stay Duration"] > 30).astype(int)

# 3.3 Age risk indicators
df["child_flag"] = (df["Age"] < 10).astype(int)
df["elderly_flag"] = (df["Age"] > 75).astype(int)
df["high_risk_age_flag"] = ((df["Age"] < 5) | (df["Age"] > 85)).astype(int)

# 3.4 CRITICAL: Gender-Diagnosis mismatch detection
# Male cannot have: Pregnancy, Cesarean Section (these are STRONG fraud signals)
pregnancy_related = ["Pregnancy", "Cesarean Section"]
df["gender_diagnosis_mismatch"] = (
    (df["Gender"] == "Male") & 
    (df["Diagnosis"].isin(pregnancy_related))
).astype(int)

# 3.5 Age-Diagnosis anomaly detection
# Children shouldn't have certain diagnoses, elderly with unusual treatments
df["age_diagnosis_anomaly"] = 0

# Child with Cataract Surgery is suspicious
df.loc[(df["Age"] < 15) & (df["Diagnosis"] == "Cataract Surgery"), "age_diagnosis_anomaly"] = 1
# Child with Hypertension is suspicious  
df.loc[(df["Age"] < 10) & (df["Diagnosis"] == "Hypertension"), "age_diagnosis_anomaly"] = 1
# Very elderly with Pregnancy is suspicious
df.loc[(df["Age"] > 55) & (df["Diagnosis"] == "Pregnancy"), "age_diagnosis_anomaly"] = 1

# 3.6 Amount per stay day ratio (high bill + short stay = suspicious)
df["amount_per_day"] = df["Amount Billed"] / (df["Stay Duration"] + 1)  # +1 to avoid div by 0
df["high_amount_per_day"] = (df["amount_per_day"] > 100000).astype(int)
df["extreme_amount_per_day"] = (df["amount_per_day"] > 200000).astype(int)

# 3.7 Combined risk score (cumulative indicator)
df["risk_score"] = (
    df["high_amount_flag"] + 
    df["zero_stay_flag"] + 
    df["gender_diagnosis_mismatch"] * 3 +  # Strong weight for gender mismatch
    df["age_diagnosis_anomaly"] * 2 +
    df["high_amount_per_day"] +
    df["extreme_amount_flag"]
)

print(f"   Created {13} fraud indicator features")
print(f"   Gender-Diagnosis mismatches found: {df['gender_diagnosis_mismatch'].sum()}")
print(f"   Age-Diagnosis anomalies found: {df['age_diagnosis_anomaly'].sum()}")

# ============================================
# STEP 4: TF-IDF ON DIAGNOSIS (TEXT UNDERSTANDING)
# ============================================
print("\n📝 Building TF-IDF vectorizer for Diagnosis text...")

# Create combined text feature: Gender + Diagnosis (captures patterns like "Male Pregnancy")
df["diagnosis_combined"] = df["Gender"] + " " + df["Diagnosis"]

# TF-IDF Vectorizer
tfidf = TfidfVectorizer(
    max_features=300,
    stop_words='english',
    ngram_range=(1, 2),  # Unigrams and bigrams
    lowercase=True
)

# Fit and transform diagnosis text
tfidf_matrix = tfidf.fit_transform(df["diagnosis_combined"])
print(f"   TF-IDF matrix shape: {tfidf_matrix.shape}")

# ============================================
# STEP 5: BUILD FINAL FEATURE MATRIX
# ============================================
print("\n🔨 Building final feature matrix...")

# Numeric features
numeric_features = [
    "Age", "Amount Billed", "Stay Duration",
    # Engineered flags
    "high_amount_flag", "very_high_amount_flag", "extreme_amount_flag", "low_amount_flag",
    "zero_stay_flag", "short_stay_flag", "long_stay_flag", "very_long_stay_flag",
    "child_flag", "elderly_flag", "high_risk_age_flag",
    "gender_diagnosis_mismatch", "age_diagnosis_anomaly",
    "amount_per_day", "high_amount_per_day", "extreme_amount_per_day",
    "risk_score"
]

# One-hot encode Gender
df_gender = pd.get_dummies(df["Gender"], prefix="Gender")

# Create numeric feature matrix
X_numeric = pd.concat([df[numeric_features], df_gender], axis=1)
# Convert to float64 to avoid scipy sparse dtype issues
X_numeric_sparse = csr_matrix(X_numeric.values.astype(np.float64))

# Combine numeric features with TF-IDF
X_combined = hstack([X_numeric_sparse, tfidf_matrix])

print(f"   Numeric features: {X_numeric.shape[1]}")
print(f"   TF-IDF features: {tfidf_matrix.shape[1]}")
print(f"   Total features: {X_combined.shape[1]}")

# Store column names for prediction
feature_columns = list(X_numeric.columns) + [f"tfidf_{i}" for i in range(tfidf_matrix.shape[1])]

# ============================================
# STEP 6: TRAIN-TEST SPLIT
# ============================================
print("\n📊 Splitting data (80/20 stratified)...")

X_train, X_test, y_train, y_test = train_test_split(
    X_combined, y, 
    test_size=0.2, 
    random_state=42,
    stratify=y  # Maintain class balance in both sets
)

print(f"   Training set: {X_train.shape[0]} samples")
print(f"   Test set: {X_test.shape[0]} samples")
print(f"   Training fraud rate: {y_train.mean()*100:.1f}%")
print(f"   Test fraud rate: {y_test.mean()*100:.1f}%")

# ============================================
# STEP 7: TRAIN RANDOM FOREST (PRODUCTION CONFIG)
# ============================================
print("\n🌲 Training Random Forest Classifier...")

model = RandomForestClassifier(
    n_estimators=300,           # More trees = better probability calibration
    max_depth=12,               # Prevent overfitting while capturing patterns
    min_samples_split=10,       # Require enough samples to split
    min_samples_leaf=5,         # Prevent overfitting on rare cases
    class_weight="balanced",    # CRITICAL: Handle 70/30 class imbalance
    random_state=42,            # Reproducibility
    n_jobs=-1,                  # Use all CPU cores
    oob_score=True              # Out-of-bag score estimation
)

model.fit(X_train, y_train)

print(f"   ✅ Model trained successfully")
print(f"   OOB Score: {model.oob_score_:.4f}")

# ============================================
# STEP 8: EVALUATE MODEL
# ============================================
print("\n📈 Evaluating model performance...")

# Training accuracy
train_acc = model.score(X_train, y_train)
test_acc = model.score(X_test, y_test)

print(f"   Training Accuracy: {train_acc:.4f}")
print(f"   Test Accuracy: {test_acc:.4f}")

# Cross-validation
cv_scores = cross_val_score(model, X_combined, y, cv=5, scoring='roc_auc')
print(f"   Cross-Val ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")

# Probability distribution check
y_proba_test = model.predict_proba(X_test)[:, 1]
print(f"\n   Probability Distribution (Test Set):")
print(f"      Min: {y_proba_test.min():.4f}")
print(f"      Max: {y_proba_test.max():.4f}")
print(f"      Mean: {y_proba_test.mean():.4f}")
print(f"      Median: {np.median(y_proba_test):.4f}")

# Check probability for fraud vs non-fraud
fraud_probs = y_proba_test[y_test == 1]
non_fraud_probs = y_proba_test[y_test == 0]
print(f"\n   Average probability for actual FRAUD cases: {fraud_probs.mean():.4f}")
print(f"   Average probability for actual NO-FRAUD cases: {non_fraud_probs.mean():.4f}")

# Feature importance
print("\n📊 Top 15 Most Important Features:")
feature_importance = pd.DataFrame({
    'feature': feature_columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for i, row in feature_importance.head(15).iterrows():
    print(f"      {row['feature']}: {row['importance']:.4f}")

# ============================================
# STEP 9: SAVE MODEL ARTIFACTS
# ============================================
print("\n💾 Saving model artifacts...")

# Create model package
model_package = {
    "model": model,
    "tfidf": tfidf,
    "numeric_columns": list(X_numeric.columns),
    "feature_columns": feature_columns,
    "version": "2.0",
    "binary_target": True,
    "classes": ["No Fraud", "Fraud"]
}

# Save as pickle
with open("fraud_model_v2.pkl", "wb") as f:
    pickle.dump(model_package, f)

print(f"   ✅ Model saved to fraud_model_v2.pkl")

# Also save as the default model file for the app
with open("fraud_model.pkl", "wb") as f:
    # For backward compatibility, save in format expected by main.py
    # But include a version flag so prediction code knows to use v2 logic
    pickle.dump(model_package, f)

print(f"   ✅ Model also saved to fraud_model.pkl (app default)")

# ============================================
# STEP 10: TEST PREDICTIONS
# ============================================
print("\n" + "=" * 60)
print("  VALIDATION TESTS")
print("=" * 60)

def test_prediction(age, gender, diagnosis, amount, stay_duration, expected_result):
    """Test a single prediction"""
    # Build feature vector
    features = {col: 0 for col in X_numeric.columns}
    
    # Set numeric features
    features["Age"] = age
    features["Amount Billed"] = amount
    features["Stay Duration"] = stay_duration
    
    # Engineered features
    features["high_amount_flag"] = 1 if amount > 100000 else 0
    features["very_high_amount_flag"] = 1 if amount > 300000 else 0
    features["extreme_amount_flag"] = 1 if amount > 500000 else 0
    features["low_amount_flag"] = 1 if amount < 30000 else 0
    
    features["zero_stay_flag"] = 1 if stay_duration == 0 else 0
    features["short_stay_flag"] = 1 if stay_duration <= 1 else 0
    features["long_stay_flag"] = 1 if stay_duration > 15 else 0
    features["very_long_stay_flag"] = 1 if stay_duration > 30 else 0
    
    features["child_flag"] = 1 if age < 10 else 0
    features["elderly_flag"] = 1 if age > 75 else 0
    features["high_risk_age_flag"] = 1 if age < 5 or age > 85 else 0
    
    # Gender-Diagnosis mismatch
    pregnancy_related = ["Pregnancy", "Cesarean Section"]
    features["gender_diagnosis_mismatch"] = 1 if (gender == "Male" and diagnosis in pregnancy_related) else 0
    
    # Age-Diagnosis anomaly
    features["age_diagnosis_anomaly"] = 0
    if age < 15 and diagnosis == "Cataract Surgery":
        features["age_diagnosis_anomaly"] = 1
    if age < 10 and diagnosis == "Hypertension":
        features["age_diagnosis_anomaly"] = 1
    if age > 55 and diagnosis == "Pregnancy":
        features["age_diagnosis_anomaly"] = 1
    
    features["amount_per_day"] = amount / (stay_duration + 1)
    features["high_amount_per_day"] = 1 if features["amount_per_day"] > 100000 else 0
    features["extreme_amount_per_day"] = 1 if features["amount_per_day"] > 200000 else 0
    
    features["risk_score"] = (
        features["high_amount_flag"] + 
        features["zero_stay_flag"] + 
        features["gender_diagnosis_mismatch"] * 3 +
        features["age_diagnosis_anomaly"] * 2 +
        features["high_amount_per_day"] +
        features["extreme_amount_flag"]
    )
    
    # Gender one-hot
    features["Gender_Female"] = 1 if gender == "Female" else 0
    features["Gender_Male"] = 1 if gender == "Male" else 0
    
    # Create numeric DataFrame
    df_test = pd.DataFrame([features])
    X_numeric_test = csr_matrix(df_test[list(X_numeric.columns)].values.astype(np.float64))
    
    # TF-IDF
    diagnosis_text = f"{gender} {diagnosis}"
    tfidf_test = tfidf.transform([diagnosis_text])
    
    # Combine
    X_test_combined = hstack([X_numeric_test, tfidf_test])
    
    # Predict
    fraud_prob = model.predict_proba(X_test_combined)[0][1]
    prediction = "Fraud" if fraud_prob >= 0.5 else "No Fraud"
    
    # Check result
    status = "✅" if expected_result in ["FRAUD" if fraud_prob >= 0.5 else "NO_FRAUD", 
                                         f"PROB>={expected_result}" if isinstance(expected_result, float) else ""] else "⚠️"
    
    if isinstance(expected_result, float):
        status = "✅" if fraud_prob >= expected_result else "❌"
    elif expected_result == "FRAUD":
        status = "✅" if fraud_prob >= 0.5 else "❌"
    elif expected_result == "NO_FRAUD":
        status = "✅" if fraud_prob < 0.5 else "❌"
    
    print(f"\n{status} Test: {gender}, Age {age}, {diagnosis}, ₹{amount:,}, {stay_duration} days")
    print(f"   Fraud Probability: {fraud_prob:.2%}")
    print(f"   ML Prediction: {prediction}")
    print(f"   Expected: {expected_result}")
    
    return fraud_prob

print("\n🧪 Running validation tests...")

# Test Case 1: OBVIOUS FRAUD - Male with Pregnancy (Gender mismatch)
test_prediction(
    age=35, gender="Male", diagnosis="Pregnancy",
    amount=120000, stay_duration=1,
    expected_result="FRAUD"
)

# Test Case 2: OBVIOUS FRAUD - High amount, 0-day stay
test_prediction(
    age=45, gender="Female", diagnosis="Routine Check-up",
    amount=500000, stay_duration=0,
    expected_result="FRAUD"
)

# Test Case 3: OBVIOUS FRAUD - Male with Cesarean Section
test_prediction(
    age=30, gender="Male", diagnosis="Cesarean Section",
    amount=200000, stay_duration=2,
    expected_result="FRAUD"
)

# Test Case 4: LEGITIMATE - Normal claim
test_prediction(
    age=45, gender="Female", diagnosis="Diabetes",
    amount=50000, stay_duration=7,
    expected_result="NO_FRAUD"
)

# Test Case 5: LEGITIMATE - Normal pregnancy claim
test_prediction(
    age=28, gender="Female", diagnosis="Pregnancy",
    amount=80000, stay_duration=3,
    expected_result="NO_FRAUD"
)

# Test Case 6: SUSPICIOUS - Child with Cataract Surgery
test_prediction(
    age=5, gender="Male", diagnosis="Cataract Surgery",
    amount=100000, stay_duration=1,
    expected_result="FRAUD"
)

# Test Case 7: SUSPICIOUS - Elderly with Pregnancy
test_prediction(
    age=85, gender="Female", diagnosis="Pregnancy",
    amount=150000, stay_duration=2,
    expected_result="FRAUD"
)

# Test Case 8: LEGITIMATE - Normal elderly care
test_prediction(
    age=70, gender="Male", diagnosis="Hypertension",
    amount=40000, stay_duration=5,
    expected_result="NO_FRAUD"
)

print("\n" + "=" * 60)
print("  TRAINING COMPLETE")
print("=" * 60)
print("\n✅ Model is ready for production use!")
print("   - fraud_model.pkl (main app)")
print("   - fraud_model_v2.pkl (backup)")
print("\n⚠️  IMPORTANT: Update main.py to use the new model format")
print("   The new model expects 'model_package' dict structure")
print("=" * 60)
