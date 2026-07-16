from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash   # <-- add these
from app.extensions import db
from app.models import Student, Teacher, Notice, Result, ClassRoutine, ExamRoutine, AcademicCalendar, StudyMaterial, Gallery
from app.utils import save_picture, allowed_file
import os
from datetime import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    if not isinstance(current_user, Student):
        return redirect(url_for('admin.dashboard'))
    return render_template('student/dashboard.html')

@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if not isinstance(current_user, Student):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')
        if email and phone:
            existing = Student.query.filter(Student.email == email, Student.id != current_user.id).first()
            if existing:
                flash('Email already exists.', 'danger')
            else:
                current_user.email = email
                current_user.phone = phone
                db.session.commit()
                flash('Profile updated successfully.', 'success')

        if 'profile_pic' in request.files:
            file = request.files['profile_pic']
            if file and allowed_file(file.filename):
                pic_filename = save_picture(file, 'profile_pics', output_size=(300, 300))
                current_user.profile_pic = pic_filename
                db.session.commit()
                flash('Profile picture updated.', 'success')
            else:
                flash('Invalid file type. Allowed: png, jpg, jpeg, gif.', 'danger')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=current_user)

# ---------- NEW: Password Change Route ----------
@student_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    if not isinstance(current_user, Student):
        flash('Access denied.', 'danger')
        return redirect(url_for('admin.dashboard'))

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_password or not new_password or not confirm_password:
        flash('All password fields are required.', 'danger')
        return redirect(url_for('student.profile'))

    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('student.profile'))

    if not check_password_hash(current_user.password_hash, current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('student.profile'))

    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('student.profile'))
# -------------------------------------------------

@student_bp.route('/teachers')
@login_required
def teachers():
    teachers = Teacher.query.all()
    return render_template('student/teachers.html', teachers=teachers)

@student_bp.route('/notices')
@login_required
def notices():
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    # Mark notices as read
    if isinstance(current_user, Student):
        current_user.last_notice_viewed = datetime.utcnow()
        db.session.commit()
    return render_template('student/notices.html', notices=notices)

@student_bp.route('/results')
@login_required
def results():
    results = Result.query.order_by(Result.created_at.desc()).all()
    return render_template('student/results.html', results=results)

@student_bp.route('/class_routine')
@login_required
def class_routine():
    routines = ClassRoutine.query.all()
    return render_template('student/class_routine.html', routines=routines)

@student_bp.route('/exam_routine')
@login_required
def exam_routine():
    routines = ExamRoutine.query.all()
    return render_template('student/exam_routine.html', routines=routines)

@student_bp.route('/academic_calendar')
@login_required
def academic_calendar():
    calendars = AcademicCalendar.query.all()
    return render_template('student/academic_calendar.html', calendars=calendars)

@student_bp.route('/study_materials')
@login_required
def study_materials():
    materials = StudyMaterial.query.all()
    return render_template('student/study_materials.html', materials=materials)

@student_bp.route('/gallery')
@login_required
def gallery():
    images = Gallery.query.all()
    return render_template('student/gallery.html', images=images)

@student_bp.route('/download/<folder>/<filename>')
@login_required
def download_file(folder, filename):
    allowed_folders = ['notice', 'results', 'class_routine', 'exam_routine', 'calendar', 'study_materials', 'gallery']
    if folder not in allowed_folders:
        flash('Invalid folder.', 'danger')
        return redirect(url_for('student.dashboard'))
    uploads = os.path.join(current_app.root_path, 'static/uploads', folder)
    return send_from_directory(uploads, filename, as_attachment=True)

@student_bp.route('/alumni')
@login_required
def alumni_redirect():
    return redirect('https://alumni.example.com')