from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, SelectField, FileField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from flask_wtf.file import FileAllowed
import re

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=50, message='Username must be between 3 and 50 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    
    def validate_username(self, username):
        """Custom validator to ensure username contains only alphanumeric and underscore"""
        if not re.match(r'^[a-zA-Z0-9_]+$', username.data):
            raise ValidationError('Username can only contain letters, numbers, and underscores')

class LoginForm(FlaskForm):
    """Form for user login"""
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])

class CourseForm(FlaskForm):
    """Form for creating/editing courses"""
    title = StringField('Course Title', validators=[
        DataRequired(),
        Length(min=5, max=200, message='Title must be between 5 and 200 characters')
    ])
    description = TextAreaField('Course Description', validators=[
        DataRequired(),
        Length(min=20, message='Description must be at least 20 characters')
    ])
    price = FloatField('Price (NPR)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Price cannot be negative')
    ])
    category = SelectField('Category', choices=[
        ('general', 'General Knowledge'),
        ('nepali', 'Nepali Language'),
        ('english', 'English Language'),
        ('math', 'Mathematics'),
        ('science', 'General Science'),
        ('constitution', 'Constitution & Law'),
        ('computer', 'Computer Knowledge'),
        ('current_affairs', 'Current Affairs'),
        ('aptitude', 'Aptitude & Reasoning'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    thumbnail = FileField('Course Thumbnail', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])

class ContentUploadForm(FlaskForm):
    """Form for uploading course content"""
    course_id = SelectField('Select Course', coerce=int, validators=[DataRequired()])
    title = StringField('Content Title', validators=[
        DataRequired(),
        Length(min=3, max=200, message='Title must be between 3 and 200 characters')
    ])
    content_type = SelectField('Content Type', choices=[
        ('video', 'Video'),
        ('pdf', 'PDF Notes'),
        ('presentation', 'PowerPoint Presentation')
    ], validators=[DataRequired()])
    file = FileField('Upload File', validators=[DataRequired()])
    display_order = IntegerField('Display Order', default=0, validators=[
        NumberRange(min=0, message='Order must be a positive number')
    ])

class ProfileUpdateForm(FlaskForm):
    """Form for updating user profile"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=50, message='Username must be between 3 and 50 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])

class PasswordChangeForm(FlaskForm):
    """Form for changing password"""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])

class SearchForm(FlaskForm):
    """Form for searching courses"""
    query = StringField('Search Course Content', validators=[
        Length(max=100, message='Search query is too long')
    ])
    category = SelectField('Filter by Category', choices=[
        ('', 'All Categories'),
        ('general', 'General Knowledge'),
        ('nepali', 'Nepali Language'),
        ('english', 'English Language'),
        ('math', 'Mathematics'),
        ('science', 'General Science'),
        ('constitution', 'Constitution & Law'),
        ('computer', 'Computer Knowledge'),
        ('current_affairs', 'Current Affairs'),
        ('aptitude', 'Aptitude & Reasoning'),
        ('other', 'Other')
    ])
