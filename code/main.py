from flask import Flask, render_template_string, request
import pickle
import numpy as np

app = Flask(__name__)

# Load model
with open("model_training/model.pkl", "rb") as f:
    model = pickle.load(f)

# HTML form template
form_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Health Claim Fraud Detection</title>
</head>
<body>
    <h2>Enter Health Insurance Claim Details</h2>
    <form method="POST">
        Age: <input type="number" name="age" required><br><br>
        Sex: 
        <select name="sex">
            <option value="male">Male</option>
            <option value="female">Female</option>
        </select><br><br>
        BMI: <input type="number" name="bmi" step="0.1" required><br><br>
        Children: <input type="number" name="children" required><br><br>
        Smoker:
        <select name="smoker">
            <option value="yes">Yes</option>
            <option value="no">No</option>
        </select><br><br>
        Region:
        <select name="region">
            <option value="northeast">Northeast</option>
            <option value="northwest">Northwest</option>
            <option value="southeast">Southeast</option>
            <option value="southwest">Southwest</option>
        </select><br><br>
        Charges: <input type="number" name="charges" step="0.01" required><br><br>
        <input type="submit" value="Predict">
    </form>

    {% if prediction is not none %}
        <h3>Result: {{ prediction }}</h3>
    {% endif %}
</body>
</html>
"""

# Encode categorical inputs like training data
def preprocess_input(data):
    sex = 1 if data['sex'] == 'male' else 0
    smoker = 1 if data['smoker'] == 'yes' else 0
    region_map = {'northeast': 0, 'northwest': 1, 'southeast': 2, 'southwest': 3}
    region = region_map.get(data['region'].lower(), 0)

    return [
        float(data['age']),
        sex,
        float(data['bmi']),
        int(data['children']),
        smoker,
        region,
        float(data['charges'])
    ]

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    if request.method == "POST":
        input_data = preprocess_input(request.form)
        input_array = np.array([input_data])
        result = model.predict(input_array)[0]
        prediction = "❌ Fraud Detected" if result == 1 else "✅ Claim is Genuine"
    return render_template_string(form_template, prediction=prediction)

if __name__ == "__main__":
    app.run(debug=True)
