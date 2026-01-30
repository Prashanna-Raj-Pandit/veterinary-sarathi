from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import User, init_db
import os

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.get_by_id(int(user_id))

# Register blueprints
from routes.auth import auth_bp
from routes.student import student_bp
from routes.admin import admin_bp
from routes.payment import payment_bp
from routes.courses import courses_bp

app.register_blueprint(auth_bp)
app.register_blueprint(student_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(courses_bp)

# Main routes
@app.route('/')
def index():
    """Landing page"""
    from models import Course
    featured_courses = Course.get_all()[:6]  # Show first 6 courses
    return render_template('index.html', featured_courses=featured_courses)

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """Contact page"""
    return render_template('contact.html')

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    return render_template('403.html'), 403

# Create upload directories if they don't exist
def create_upload_directories():
    """Ensure all upload directories exist"""
    try:
        directories = [
            Config.UPLOAD_FOLDER,
            os.path.join(Config.UPLOAD_FOLDER, 'videos'),
            os.path.join(Config.UPLOAD_FOLDER, 'notes'),
            os.path.join(Config.UPLOAD_FOLDER, 'presentations'),
            os.path.join(Config.UPLOAD_FOLDER, 'images')
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            # Create .gitkeep file to preserve directory structure
            gitkeep_path = os.path.join(directory, '.gitkeep')
            if not os.path.exists(gitkeep_path):
                open(gitkeep_path, 'a').close()
        print(f"Upload directories created at: {Config.UPLOAD_FOLDER}")
    except Exception as e:
        print(f"Warning: Could not create upload directories: {e}")
        # Continue anyway - directories might be read-only on serverless

def create_admin_user():
    """Create default admin user if it doesn't exist"""
    try:
        admin = User.get_by_email(Config.ADMIN_EMAIL)
        if not admin:
            User.create(
                username=Config.ADMIN_USERNAME,
                email=Config.ADMIN_EMAIL,
                password=Config.ADMIN_PASSWORD,
                is_admin=True
            )
            print(f"Admin user created: {Config.ADMIN_EMAIL}")
    except Exception as e:
        print(f"Warning: Could not create admin user: {e}")

# Initialize application
def initialize_app():
    """Initialize database and create necessary directories"""
    try:
        init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Warning: Database initialization error: {e}")
    
    create_upload_directories()
    create_admin_user()
    print("Application initialization completed!")

# Template filters
@app.template_filter('currency')
def currency_filter(value):
    """Format currency in NPR"""
    return f"NPR {value:,.2f}"

# Context processor to make certain variables available in all templates
@app.context_processor
def inject_user():
    """Inject current_user into all templates"""
    return dict(current_user=current_user)

# Initialize the app with error handling
try:
    initialize_app()
except Exception as e:
    print(f"Warning: Initialization error: {e}")
    # Continue anyway for serverless

# Local development entry point
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

# Vercel uses the 'app' variable automatically
