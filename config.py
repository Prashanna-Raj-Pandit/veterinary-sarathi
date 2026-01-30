import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Detect if running on Vercel
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None

class Config:
    """Base configuration class with all settings"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY and os.environ.get('FLASK_ENV') == 'production':
        raise ValueError("SECRET_KEY must be set in production environment")
    SECRET_KEY = SECRET_KEY or 'dev-secret-key-change-in-production'
    
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'development'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'
    
    # Database Configuration - use /tmp on Vercel
    if IS_VERCEL:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:////tmp/veterinary_sarathi.db'
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///veterinary_sarathi.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Configuration - use /tmp on Vercel
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 524288000))  # 500MB default
    
    if IS_VERCEL:
        UPLOAD_FOLDER = '/tmp/uploads'
    else:
        UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                      os.environ.get('UPLOAD_FOLDER', 'uploads'))
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf'}
    ALLOWED_PRESENTATION_EXTENSIONS = {'ppt', 'pptx'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Admin Configuration
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@swasthikloksewa.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'changeme123')
    
    # eSewa Payment Gateway Configuration (Nepal)
    ESEWA_MERCHANT_ID = os.environ.get('ESEWA_MERCHANT_ID', '')
    ESEWA_SECRET_KEY = os.environ.get('ESEWA_SECRET_KEY', '')
    ESEWA_SUCCESS_URL = os.environ.get('ESEWA_SUCCESS_URL', 'http://localhost:5000/payment/success')
    ESEWA_FAILURE_URL = os.environ.get('ESEWA_FAILURE_URL', 'http://localhost:5000/payment/failure')
    ESEWA_API_URL = os.environ.get('ESEWA_API_URL', 'https://uat.esewa.com.np/epay/main')  # Use UAT for testing
    
    # Email Configuration (for future implementation)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour in seconds
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
