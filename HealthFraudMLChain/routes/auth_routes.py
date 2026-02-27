# routes/auth_routes.py

from flask import Blueprint, request, redirect, session, render_template, flash
from models.user_model import register_user, authenticate_user

auth_bp = Blueprint('auth_bp', __name__)

# Register route
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']  # patient, doctor, admin

        result = register_user(email, password, role)
        if result["success"]:
            flash("Registration successful. Please log in.", "success")
            return redirect('/login')
        else:
            flash(result["message"], "danger")
    return render_template('register.html')


# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        result = authenticate_user(email, password)
        if result["success"]:
            session['email'] = result['user']['email']
            session['role'] = result['user']['role']
            flash("Login successful!", "success")

            # Redirect to dashboard based on role
            if result['user']['role'] == 'admin':
                return redirect('/admin/dashboard')
            elif result['user']['role'] == 'doctor':
                return redirect('/doctor/dashboard')
            else:
                return redirect('/patient/dashboard')
        else:
            flash(result["message"], "danger")
    return render_template('login.html')


# Logout route
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/login')
