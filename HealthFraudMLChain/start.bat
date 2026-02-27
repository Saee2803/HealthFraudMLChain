@echo off
echo Installing dependencies...
pip install -r requirements_fixed.txt

echo.
echo Starting Flask application...
set FLASK_APP=main.py
set FLASK_ENV=development
python main.py

pause