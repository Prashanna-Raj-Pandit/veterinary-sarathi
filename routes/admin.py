from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import User, Course, Content, Enrollment, Payment, get_db_connection
from forms import CourseForm, ContentUploadForm
import os
from config import Config
from functools import wraps

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You must be an administrator to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with statistics"""
    # Get statistics
    total_students = User.get_student_count()
    total_enrollments = Enrollment.get_enrollment_count()
    total_revenue = Payment.get_total_revenue()
    total_courses = len(Course.get_all())
    
    # Get recent enrollments
    recent_enrollments = Enrollment.get_recent_enrollments(5)
    
    # Get popular courses (courses with most enrollments)
    conn = get_db_connection()
    popular_courses = conn.execute('''
        SELECT c.id, c.title, COUNT(e.id) as enrollment_count
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        GROUP BY c.id
        ORDER BY enrollment_count DESC
        LIMIT 5
    ''').fetchall()
    conn.close()
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_enrollments=total_enrollments,
                         total_revenue=total_revenue,
                         total_courses=total_courses,
                         recent_enrollments=recent_enrollments,
                         popular_courses=popular_courses)

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    """View all registered students"""
    all_students = User.get_all_students()
    
    # Get enrollment count for each student
    students_with_enrollments = []
    for student in all_students:
        enrollments = Enrollment.get_by_user(student['id'])
        students_with_enrollments.append({
            'student': student,
            'enrollment_count': len(enrollments)
        })
    
    return render_template('admin/students.html', students=students_with_enrollments)

@admin_bp.route('/student/<int:student_id>')
@login_required
@admin_required
def student_detail(student_id):
    """View detailed information about a specific student"""
    student = User.get_by_id(student_id)
    if not student or student.is_admin:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.students'))
    
    enrollments = Enrollment.get_by_user(student_id)
    payments = Payment.get_by_user(student_id)
    
    return render_template('admin/student_detail.html',
                         student=student,
                         enrollments=enrollments,
                         payments=payments)

@admin_bp.route('/courses')
@login_required
@admin_required
def manage_courses():
    """Manage all courses"""
    courses = Course.get_all()
    return render_template('admin/manage_courses.html', courses=courses)

@admin_bp.route('/course/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_course():
    """Create a new course"""
    form = CourseForm()
    
    if form.validate_on_submit():
        # Handle thumbnail upload
        thumbnail_path = None
        if form.thumbnail.data:
            thumbnail = form.thumbnail.data
            if allowed_file(thumbnail.filename, Config.ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(thumbnail.filename)
                # Add timestamp to filename to avoid conflicts
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                
                # Ensure images directory exists
                images_dir = os.path.join(Config.UPLOAD_FOLDER, 'images')
                os.makedirs(images_dir, exist_ok=True)
                
                thumbnail_path = os.path.join('images', filename)
                thumbnail.save(os.path.join(Config.UPLOAD_FOLDER, thumbnail_path))
            else:
                flash('Invalid image format. Please use jpg, jpeg, png, gif, or webp.', 'danger')
                return render_template('admin/course_form.html', form=form, action='Create')
        
        # Create course
        course_id = Course.create(
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            thumbnail=thumbnail_path,
            instructor_id=current_user.id
        )
        
        if course_id:
            flash('Course created successfully!', 'success')
            return redirect(url_for('admin.manage_courses'))
        else:
            flash('Failed to create course. Please try again.', 'danger')
    
    return render_template('admin/course_form.html', form=form, action='Create')

@admin_bp.route('/course/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    """Edit an existing course"""
    course = Course.get_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    form = CourseForm()
    
    if form.validate_on_submit():
        # Handle thumbnail upload
        thumbnail_path = course['thumbnail']
        if form.thumbnail.data:
            thumbnail = form.thumbnail.data
            if allowed_file(thumbnail.filename, Config.ALLOWED_IMAGE_EXTENSIONS):
                filename = secure_filename(thumbnail.filename)
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"
                
                images_dir = os.path.join(Config.UPLOAD_FOLDER, 'images')
                os.makedirs(images_dir, exist_ok=True)
                
                thumbnail_path = os.path.join('images', filename)
                thumbnail.save(os.path.join(Config.UPLOAD_FOLDER, thumbnail_path))
            else:
                flash('Invalid image format.', 'danger')
                return render_template('admin/course_form.html', form=form, action='Edit', course=course)
        
        # Update course
        Course.update(
            course_id=course_id,
            title=form.title.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            thumbnail=thumbnail_path
        )
        
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin.manage_courses'))
    
    # Pre-fill form with course data
    if request.method == 'GET':
        form.title.data = course['title']
        form.description.data = course['description']
        form.price.data = course['price']
        form.category.data = course['category']
    
    return render_template('admin/course_form.html', form=form, action='Edit', course=course)

@admin_bp.route('/course/delete/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    """Delete a course"""
    course = Course.get_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    # Delete associated content files
    contents = Content.get_by_course(course_id)
    for content in contents:
        file_path = os.path.join(Config.UPLOAD_FOLDER, content['file_path'])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
    
    # Delete course (cascade will delete content, enrollments, etc.)
    Course.delete(course_id)
    
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('admin.manage_courses'))

@admin_bp.route('/upload-content', methods=['GET', 'POST'])
@login_required
@admin_required
def upload_content():
    """Upload course content (videos, PDFs, presentations)"""
    form = ContentUploadForm()
    
    # Populate course choices
    courses = Course.get_all()
    form.course_id.choices = [(c['id'], c['title']) for c in courses]
    
    if not courses:
        flash('Please create a course first before uploading content.', 'warning')
        return redirect(url_for('admin.create_course'))
    
    if form.validate_on_submit():
        file = form.file.data
        content_type = form.content_type.data
        
        # Determine allowed extensions and subdirectory based on content type
        if content_type == 'video':
            allowed_extensions = Config.ALLOWED_VIDEO_EXTENSIONS
            subdirectory = 'videos'
        elif content_type == 'pdf':
            allowed_extensions = Config.ALLOWED_DOCUMENT_EXTENSIONS
            subdirectory = 'notes'
        elif content_type == 'presentation':
            allowed_extensions = Config.ALLOWED_PRESENTATION_EXTENSIONS
            subdirectory = 'presentations'
        else:
            flash('Invalid content type.', 'danger')
            return render_template('admin/upload_content.html', form=form)
        
        # Validate file extension
        if not allowed_file(file.filename, allowed_extensions):
            flash(f'Invalid file format for {content_type}. Allowed: {", ".join(allowed_extensions)}', 'danger')
            return render_template('admin/upload_content.html', form=form)
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        
        # Ensure subdirectory exists
        upload_dir = os.path.join(Config.UPLOAD_FOLDER, subdirectory)
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(subdirectory, filename)
        full_path = os.path.join(Config.UPLOAD_FOLDER, file_path)
        
        # Save file
        try:
            file.save(full_path)
        except Exception as e:
            flash(f'Error uploading file: {str(e)}', 'danger')
            return render_template('admin/upload_content.html', form=form)
        
        # Create content record
        content_id = Content.create(
            course_id=form.course_id.data,
            title=form.title.data,
            content_type=content_type,
            file_path=file_path,
            display_order=form.display_order.data
        )
        
        if content_id:
            flash(f'{content_type.capitalize()} uploaded successfully!', 'success')
            return redirect(url_for('admin.upload_content'))
        else:
            flash('Failed to create content record.', 'danger')
    
    return render_template('admin/upload_content.html', form=form)

@admin_bp.route('/course/<int:course_id>/contents')
@login_required
@admin_required
def course_contents(course_id):
    """View all contents for a specific course"""
    course = Course.get_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    contents = Content.get_by_course(course_id)
    
    return render_template('admin/course_contents.html', course=course, contents=contents)

@admin_bp.route('/content/delete/<int:content_id>', methods=['POST'])
@login_required
@admin_required
def delete_content(content_id):
    """Delete course content"""
    content = Content.get_by_id(content_id)
    if not content:
        flash('Content not found.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    course_id = content['course_id']
    
    # Delete file
    file_path = os.path.join(Config.UPLOAD_FOLDER, content['file_path'])
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    # Delete content record
    Content.delete(content_id)
    
    flash('Content deleted successfully!', 'success')
    return redirect(url_for('admin.course_contents', course_id=course_id))

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    """View analytics and statistics"""
    # Get comprehensive statistics
    conn = get_db_connection()
    
    # Course statistics
    course_stats = conn.execute('''
        SELECT 
            c.id,
            c.title,
            c.category,
            c.price,
            COUNT(DISTINCT e.id) as enrollment_count,
            COALESCE(SUM(CASE WHEN p.status = 'success' THEN p.amount ELSE 0 END), 0) as revenue
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        LEFT JOIN payments p ON c.id = p.course_id
        GROUP BY c.id
        ORDER BY enrollment_count DESC
    ''').fetchall()
    
    # Category statistics
    category_stats = conn.execute('''
        SELECT 
            c.category,
            COUNT(DISTINCT c.id) as course_count,
            COUNT(DISTINCT e.id) as enrollment_count
        FROM courses c
        LEFT JOIN enrollments e ON c.id = e.course_id
        GROUP BY c.category
        ORDER BY enrollment_count DESC
    ''').fetchall()
    
    # Recent payments
    recent_payments = conn.execute('''
        SELECT p.*, u.username, c.title as course_title
        FROM payments p
        JOIN users u ON p.user_id = u.id
        JOIN courses c ON p.course_id = c.id
        ORDER BY p.payment_date DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    # General statistics
    total_students = User.get_student_count()
    total_enrollments = Enrollment.get_enrollment_count()
    total_revenue = Payment.get_total_revenue()
    total_courses = len(Course.get_all())
    
    return render_template('admin/analytics.html',
                         total_students=total_students,
                         total_enrollments=total_enrollments,
                         total_revenue=total_revenue,
                         total_courses=total_courses,
                         course_stats=course_stats,
                         category_stats=category_stats,
                         recent_payments=recent_payments)
