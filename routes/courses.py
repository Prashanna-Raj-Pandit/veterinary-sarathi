from flask import Blueprint, render_template, request
from models import Course
from forms import SearchForm

courses_bp = Blueprint('courses', __name__, url_prefix='/courses')

@courses_bp.route('/')
def index():
    """Public course catalog page"""
    form = SearchForm()
    
    # Get search and filter parameters
    search_query = request.args.get('query', '').strip()
    category_filter = request.args.get('category', '').strip()
    
    # Fetch courses based on filters
    if search_query:
        courses = Course.search(search_query)
    elif category_filter:
        courses = Course.get_by_category(category_filter)
    else:
        courses = Course.get_all()
    
    return render_template('courses/index.html', courses=courses, form=form)

@courses_bp.route('/<int:course_id>')
def detail(course_id):
    """Public course detail page"""
    course = Course.get_by_id(course_id)
    if not course:
        return render_template('404.html'), 404
    
    return render_template('courses/detail.html', course=course)

@courses_bp.route('/category/<category>')
def by_category(category):
    """Filter courses by category"""
    courses = Course.get_by_category(category)
    form = SearchForm()
    
    return render_template('courses/index.html', courses=courses, form=form, selected_category=category)
