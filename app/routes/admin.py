from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models import Student, Teacher, Notice, Result, ClassRoutine, ExamRoutine, AcademicCalendar, StudyMaterial, Gallery, Admin
from app.utils import save_picture, save_file, allowed_file
import os

admin_bp = Blueprint('admin', __name__)

# Ensure only admin can access
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, Admin):
            flash('You are not authorized to access this page.', 'danger')
            return redirect(url_for('student.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Dashboard
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = Student.query.count()
    pending_students = Student.query.filter_by(status='pending').count()
    total_teachers = Teacher.query.count()
    total_notices = Notice.query.count()
    total_files = (Result.query.count() + ClassRoutine.query.count() + ExamRoutine.query.count() +
                   AcademicCalendar.query.count() + StudyMaterial.query.count() + Gallery.query.count())
    return render_template('admin/dashboard.html', 
                           total_students=total_students,
                           pending_students=pending_students,
                           total_teachers=total_teachers,
                           total_notices=total_notices,
                           total_files=total_files)

# Pending Students
@admin_bp.route('/pending_students')
@login_required
@admin_required
def pending_students():
    students = Student.query.filter_by(status='pending').all()
    return render_template('admin/pending_students.html', students=students)

@admin_bp.route('/approve_student/<int:id>')
@login_required
@admin_required
def approve_student(id):
    student = Student.query.get_or_404(id)
    student.status = 'approved'
    db.session.commit()
    flash(f'Student {student.full_name} approved.', 'success')
    return redirect(url_for('admin.pending_students'))

@admin_bp.route('/reject_student/<int:id>')
@login_required
@admin_required
def reject_student(id):
    student = Student.query.get_or_404(id)
    student.status = 'rejected'
    db.session.commit()
    flash(f'Student {student.full_name} rejected.', 'warning')
    return redirect(url_for('admin.pending_students'))

# Students Management
@admin_bp.route('/students')
@login_required
@admin_required
def students():
    all_students = Student.query.all()
    return render_template('admin/students.html', students=all_students)
@admin_bp.route('/delete_student/<int:id>')
@login_required
@admin_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    
    # Delete profile picture if it exists and is not the default
    if student.profile_pic and student.profile_pic != 'default.png':
        pic_path = os.path.join(current_app.root_path, 'static/uploads/profile_pics', student.profile_pic)
        if os.path.exists(pic_path):
            os.remove(pic_path)
    
    db.session.delete(student)
    db.session.commit()
    flash(f'Student {student.full_name} (Roll: {student.roll_number}) has been deleted.', 'success')
    return redirect(url_for('admin.students'))
@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def profile():
    if request.method == 'POST':
        username = request.form.get('username')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Update username if changed
        if username and username != current_user.username:
            existing = Admin.query.filter_by(username=username).first()
            if existing:
                flash('Username already taken.', 'danger')
                return redirect(url_for('admin.profile'))
            current_user.username = username
            flash('Username updated.', 'success')

        # Handle password change
        if current_password or new_password or confirm_password:
            if not current_password or not new_password or not confirm_password:
                flash('Please fill all password fields.', 'danger')
                return redirect(url_for('admin.profile'))
            if not check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('admin.profile'))
            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('admin.profile'))
            current_user.password_hash = generate_password_hash(new_password)
            flash('Password changed successfully.', 'success')

        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('admin.profile'))

    return render_template('admin/profile.html')

# Teachers CRUD
@admin_bp.route('/teachers', methods=['GET', 'POST'])
@login_required
@admin_required
def teachers():
    if request.method == 'POST':
        name = request.form.get('name')
        designation = request.form.get('designation')
        department = request.form.get('department')
        email = request.form.get('email')
        phone = request.form.get('phone')
        photo = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and allowed_file(file.filename):
                photo = save_picture(file, 'teachers', output_size=(200, 200))
        teacher = Teacher(name=name, designation=designation, department=department,
                          email=email, phone=phone, photo=photo or 'default_teacher.png')
        db.session.add(teacher)
        db.session.commit()
        flash('Teacher added successfully.', 'success')
        return redirect(url_for('admin.teachers'))
    teachers = Teacher.query.all()
    return render_template('admin/teachers.html', teachers=teachers)

@admin_bp.route('/edit_teacher/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    teacher.name = request.form.get('name')
    teacher.designation = request.form.get('designation')
    teacher.department = request.form.get('department')
    teacher.email = request.form.get('email')
    teacher.phone = request.form.get('phone')
    if 'photo' in request.files:
        file = request.files['photo']
        if file and allowed_file(file.filename):
            photo = save_picture(file, 'teachers', output_size=(200, 200))
            teacher.photo = photo
    db.session.commit()
    flash('Teacher updated.', 'success')
    return redirect(url_for('admin.teachers'))

@admin_bp.route('/delete_teacher/<int:id>')
@login_required
@admin_required
def delete_teacher(id):
    teacher = Teacher.query.get_or_404(id)
    db.session.delete(teacher)
    db.session.commit()
    flash('Teacher deleted.', 'success')
    return redirect(url_for('admin.teachers'))

# Generic file upload helper for admin modules
def handle_file_upload(model_class, folder, form_fields, redirect_route):
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            flash('Invalid file. Allowed: PDF, Images.', 'danger')
            return redirect(url_for(redirect_route))
        filename = save_file(file, folder)
        data = {}
        for field in form_fields:
            data[field] = request.form.get(field)
        data['file_path'] = filename
        entry = model_class(**data)
        db.session.add(entry)
        db.session.commit()
        flash('Uploaded successfully.', 'success')
        return redirect(url_for(redirect_route))
    items = model_class.query.all()
    return render_template(f'admin/{folder}.html', items=items)

# Notice
@admin_bp.route('/notices', methods=['GET', 'POST'])
@login_required
@admin_required
def notices():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            flash('Invalid file.', 'danger')
            return redirect(url_for('admin.notices'))
        filename = save_file(file, 'notice')
        notice = Notice(title=title, description=description, file_path=filename)
        db.session.add(notice)
        db.session.commit()
        flash('Notice uploaded.', 'success')
        return redirect(url_for('admin.notices'))
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template('admin/notices.html', notices=notices)

@admin_bp.route('/delete_notice/<int:id>')
@login_required
@admin_required
def delete_notice(id):
    notice = Notice.query.get_or_404(id)
    # Delete file from disk
    filepath = os.path.join(current_app.root_path, 'static/uploads/notice', notice.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted.', 'success')
    return redirect(url_for('admin.notices'))

# Results
@admin_bp.route('/results', methods=['GET', 'POST'])
@login_required
@admin_required
def results():
    if request.method == 'POST':
        title = request.form.get('title')
        semester = request.form.get('semester')
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            flash('Invalid file.', 'danger')
            return redirect(url_for('admin.results'))
        filename = save_file(file, 'results')
        result = Result(title=title, semester=semester, file_path=filename)
        db.session.add(result)
        db.session.commit()
        flash('Result uploaded.', 'success')
        return redirect(url_for('admin.results'))
    results = Result.query.order_by(Result.created_at.desc()).all()
    return render_template('admin/results.html', results=results)

@admin_bp.route('/delete_result/<int:id>')
@login_required
@admin_required
def delete_result(id):
    result = Result.query.get_or_404(id)
    filepath = os.path.join(current_app.root_path, 'static/uploads/results', result.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(result)
    db.session.commit()
    flash('Result deleted.', 'success')
    return redirect(url_for('admin.results'))

# Class Routine
@admin_bp.route('/class_routine', methods=['GET', 'POST'])
@login_required
@admin_required
def class_routine():
    if request.method == 'POST':
        semester = request.form.get('semester')
        department = request.form.get('department')
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            flash('Invalid file.', 'danger')
            return redirect(url_for('admin.class_routine'))
        filename = save_file(file, 'class_routine')
        routine = ClassRoutine(semester=semester, department=department, file_path=filename)
        db.session.add(routine)
        db.session.commit()
        flash('Class Routine uploaded.', 'success')
        return redirect(url_for('admin.class_routine'))
    routines = ClassRoutine.query.all()
    return render_template('admin/class_routine.html', routines=routines)

@admin_bp.route('/delete_class_routine/<int:id>')
@login_required
@admin_required
def delete_class_routine(id):
    routine = ClassRoutine.query.get_or_404(id)
    filepath = os.path.join(current_app.root_path, 'static/uploads/class_routine', routine.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(routine)
    db.session.commit()
    flash('Class Routine deleted.', 'success')
    return redirect(url_for('admin.class_routine'))

# Exam Routine
@admin_bp.route('/exam_routine', methods=['GET', 'POST'])
@login_required
@admin_required
def exam_routine():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            flash('Invalid file.', 'danger')
            return redirect(url_for('admin.exam_routine'))
        filename = save_file(file, 'exam_routine')
        routine = ExamRoutine(file_path=filename)
        db.session.add(routine)
        db.session.commit()
        flash('Exam Routine uploaded.', 'success')
        return redirect(url_for('admin.exam_routine'))
    routines = ExamRoutine.query.all()
    return render_template('admin/exam_routine.html', routines=routines)

@admin_bp.route('/delete_exam_routine/<int:id>')
@login_required
@admin_required
def delete_exam_routine(id):
    routine = ExamRoutine.query.get_or_404(id)
    filepath = os.path.join(current_app.root_path, 'static/uploads/exam_routine', routine.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(routine)
    db.session.commit()
    flash('Exam Routine deleted.', 'success')
    return redirect(url_for('admin.exam_routine'))

# Academic Calendar
@admin_bp.route('/academic_calendar', methods=['GET', 'POST'])
@login_required
@admin_required
def academic_calendar():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file or not allowed_file(file.filename):
            flash('Invalid file.', 'danger')
            return redirect(url_for('admin.academic_calendar'))
        filename = save_file(file, 'calendar')
        calendar = AcademicCalendar(file_path=filename)
        db.session.add(calendar)
        db.session.commit()
        flash('Academic Calendar uploaded.', 'success')
        return redirect(url_for('admin.academic_calendar'))
    calendars = AcademicCalendar.query.all()
    return render_template('admin/academic_calendar.html', calendars=calendars)

@admin_bp.route('/delete_academic_calendar/<int:id>')
@login_required
@admin_required
def delete_academic_calendar(id):
    calendar = AcademicCalendar.query.get_or_404(id)
    filepath = os.path.join(current_app.root_path, 'static/uploads/calendar', calendar.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(calendar)
    db.session.commit()
    flash('Academic Calendar deleted.', 'success')
    return redirect(url_for('admin.academic_calendar'))

# Study Materials
@admin_bp.route('/study_materials', methods=['GET', 'POST'])
@login_required
@admin_required
def study_materials():
    if request.method == 'POST':
        subject = request.form.get('subject')
        semester = request.form.get('semester')
        file = request.files.get('file')
        if not file or not allowed_file(file.filename) or not file.filename.lower().endswith('.pdf'):
            flash('Invalid file. Only PDF allowed.', 'danger')
            return redirect(url_for('admin.study_materials'))
        filename = save_file(file, 'study_materials')
        material = StudyMaterial(subject=subject, semester=semester, file_path=filename)
        db.session.add(material)
        db.session.commit()
        flash('Study Material uploaded.', 'success')
        return redirect(url_for('admin.study_materials'))
    materials = StudyMaterial.query.all()
    return render_template('admin/study_materials.html', materials=materials)

@admin_bp.route('/delete_study_material/<int:id>')
@login_required
@admin_required
def delete_study_material(id):
    material = StudyMaterial.query.get_or_404(id)
    filepath = os.path.join(current_app.root_path, 'static/uploads/study_materials', material.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(material)
    db.session.commit()
    flash('Study Material deleted.', 'success')
    return redirect(url_for('admin.study_materials'))

# Gallery
@admin_bp.route('/gallery', methods=['GET', 'POST'])
@login_required
@admin_required
def gallery():
    if request.method == 'POST':
        caption = request.form.get('caption')
        file = request.files.get('image')
        if not file or not allowed_file(file.filename):
            flash('Invalid image file.', 'danger')
            return redirect(url_for('admin.gallery'))
        filename = save_picture(file, 'gallery', output_size=(800, 800))
        image = Gallery(image_path=filename, caption=caption)
        db.session.add(image)
        db.session.commit()
        flash('Image uploaded.', 'success')
        return redirect(url_for('admin.gallery'))
    images = Gallery.query.all()
    return render_template('admin/gallery.html', images=images)

@admin_bp.route('/delete_gallery/<int:id>')
@login_required
@admin_required
def delete_gallery(id):
    image = Gallery.query.get_or_404(id)
    filepath = os.path.join(current_app.root_path, 'static/uploads/gallery', image.image_path)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(image)
    db.session.commit()
    flash('Image deleted.', 'success')
    return redirect(url_for('admin.gallery'))