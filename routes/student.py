from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from models import Course, Enrollment, Content, Cart, get_db_connection
from forms import SearchForm
import os
from config import Config

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard showing enrolled courses"""
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))
    
    enrollments = Enrollment.get_by_user(current_user.id)
    return render_template('student/dashboard.html', enrollments=enrollments)

@student_bp.route('/courses')
def courses():
    """Browse all available courses"""
    form = SearchForm()
    
    # Get search and filter parameters
    search_query = request.args.get('query', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    # Fetch courses based on filters
    if search_query:
        courses_list = Course.search(search_query)
    elif category_filter:
        courses_list = Course.get_by_category(category_filter)
    else:
        courses_list = Course.get_all()
    
    return render_template('student/courses.html', courses=courses_list, form=form)

@student_bp.route('/course/<int:course_id>')
def course_detail(course_id):
    """Display course details"""
    course = Course.get_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('student.courses'))
    
    # Check if user is enrolled
    is_enrolled = False
    in_cart = False
    
    if current_user.is_authenticated:
        is_enrolled = Enrollment.is_enrolled(current_user.id, course_id)
        # Check if course is in cart
        cart_items = Cart.get_items(current_user.id)
        in_cart = any(item['course_id'] == course_id for item in cart_items)
    
    # Get course content preview (first item of each type)
    contents = Content.get_by_course(course_id)
    
    return render_template('student/course_detail.html', 
                         course=course, 
                         is_enrolled=is_enrolled,
                         in_cart=in_cart,
                         contents=contents)

@student_bp.route('/watch/<int:course_id>')
@login_required
def watch_course(course_id):
    """Watch course content (videos, view notes, presentations)"""
    if current_user.is_admin:
        flash('Admin users cannot access student courses.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    # Check if user is enrolled
    if not Enrollment.is_enrolled(current_user.id, course_id):
        flash('You must enroll in this course to access the content.', 'warning')
        return redirect(url_for('student.course_detail', course_id=course_id))
    
    course = Course.get_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # Get all course content
    contents = Content.get_by_course(course_id)
    
    # Get enrollment details for progress
    conn = get_db_connection()
    enrollment = conn.execute(
        'SELECT * FROM enrollments WHERE user_id = ? AND course_id = ?',
        (current_user.id, course_id)
    ).fetchone()
    conn.close()
    
    return render_template('student/watch_course.html', 
                         course=course, 
                         contents=contents,
                         enrollment=enrollment)

@student_bp.route('/download/<int:content_id>')
@login_required
def download_content(content_id):
    """Download course content (PDFs, presentations)"""
    if current_user.is_admin:
        flash('Admin users cannot download content.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    content = Content.get_by_id(content_id)
    if not content:
        flash('Content not found.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # Check if user is enrolled in the course
    if not Enrollment.is_enrolled(current_user.id, content['course_id']):
        flash('You must be enrolled in this course to download content.', 'danger')
        return redirect(url_for('student.course_detail', course_id=content['course_id']))
    
    # Only allow download of PDFs and presentations
    if content['content_type'] not in ['pdf', 'presentation']:
        flash('This content type cannot be downloaded.', 'warning')
        return redirect(url_for('student.watch_course', course_id=content['course_id']))
    
    file_path = os.path.join(Config.UPLOAD_FOLDER, content['file_path'])
    
    if not os.path.exists(file_path):
        flash('File not found on server.', 'danger')
        return redirect(url_for('student.watch_course', course_id=content['course_id']))
    
    return send_file(file_path, as_attachment=True)

@student_bp.route('/cart')
@login_required
def cart():
    """View shopping cart"""
    if current_user.is_admin:
        flash('Admin users cannot use shopping cart.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    cart_items = Cart.get_items(current_user.id)
    total = Cart.get_cart_total(current_user.id)
    
    return render_template('student/cart.html', cart_items=cart_items, total=total)

@student_bp.route('/cart/add/<int:course_id>', methods=['POST'])
@login_required
def add_to_cart(course_id):
    """Add course to shopping cart"""
    if current_user.is_admin:
        flash('Admin users cannot add courses to cart.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    # Check if course exists
    course = Course.get_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('student.courses'))
    
    # Check if already enrolled
    if Enrollment.is_enrolled(current_user.id, course_id):
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('student.course_detail', course_id=course_id))
    
    # Add to cart
    result = Cart.add_item(current_user.id, course_id)
    if result:
        flash(f'"{course["title"]}" added to cart!', 'success')
    else:
        flash('This course is already in your cart.', 'info')
    
    return redirect(url_for('student.course_detail', course_id=course_id))

@student_bp.route('/cart/remove/<int:course_id>', methods=['POST'])
@login_required
def remove_from_cart(course_id):
    """Remove course from shopping cart"""
    if current_user.is_admin:
        flash('Admin users cannot use shopping cart.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    Cart.remove_item(current_user.id, course_id)
    flash('Course removed from cart.', 'success')
    return redirect(url_for('student.cart'))

@student_bp.route('/update-progress/<int:course_id>/<int:progress>', methods=['POST'])
@login_required
def update_progress(course_id, progress):
    """Update course progress"""
    if current_user.is_admin:
        return {'success': False, 'message': 'Admin cannot update progress'}, 403
    
    if not Enrollment.is_enrolled(current_user.id, course_id):
        return {'success': False, 'message': 'Not enrolled'}, 403
    
    # Validate progress (0-100)
    progress = max(0, min(100, progress))
    
    Enrollment.update_progress(current_user.id, course_id, progress)
    return {'success': True, 'progress': progress}
