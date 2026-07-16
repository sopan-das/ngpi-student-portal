from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import Student, Admin   # make sure Admin is imported
from app.utils import save_picture

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard' if isinstance(current_user, Student) else 'admin.dashboard'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        roll_number = request.form.get('roll_number')
        registration_number = request.form.get('registration_number')
        department = request.form.get('department')
        semester = request.form.get('semester')
        session = request.form.get('session')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([full_name, roll_number, registration_number, department, semester, session, email, phone, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return render_template('auth/register.html')
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        if Student.query.filter_by(roll_number=roll_number).first():
            flash('Roll number already exists.', 'danger')
            return render_template('auth/register.html')
        if Student.query.filter_by(registration_number=registration_number).first():
            flash('Registration number already exists.', 'danger')
            return render_template('auth/register.html')
        if Student.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('auth/register.html')

        hashed_password = generate_password_hash(password)
        student = Student(
            full_name=full_name,
            roll_number=roll_number,
            registration_number=registration_number,
            department=department,
            semester=semester,
            session=session,
            email=email,
            phone=phone,
            password_hash=hashed_password,
            status='pending'
        )
        db.session.add(student)
        db.session.commit()

        flash('Your registration has been submitted successfully. Please wait for administrator approval.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard' if isinstance(current_user, Student) else 'admin.dashboard'))
    
    if request.method == 'POST':
        username_or_roll = request.form.get('roll_number')
        password = request.form.get('password')

        # 1. Try student login
        student = Student.query.filter_by(roll_number=username_or_roll).first()
        if student and check_password_hash(student.password_hash, password):
            if student.status == 'pending':
                flash('Your account is pending approval. Please wait for administrator approval.', 'warning')
                return render_template('auth/login.html')
            elif student.status == 'rejected':
                flash('Your account has been rejected. Please contact administrator.', 'danger')
                return render_template('auth/login.html')
            elif student.status == 'approved':
                login_user(student)
                return redirect(url_for('student.dashboard'))

        # 2. Try admin login
        admin = Admin.query.filter_by(username=username_or_roll).first()
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('admin.dashboard'))

        # 3. If neither works
        flash('Invalid roll number or password.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.landing'))