from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from forms import RegistrationForm, LoginForm, ProfileUpdateForm, PasswordChangeForm
from models import User, get_db_connection

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.get_by_email(form.email.data):
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('auth/register.html', form=form)
        
        if User.get_by_username(form.username.data):
            flash('Username already taken. Please choose a different username.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Create new user
        user_id = User.create(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        
        if user_id:
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login route"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_email(form.email.data)
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            
            # Redirect based on user role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.is_admin:
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management route"""
    profile_form = ProfileUpdateForm()
    password_form = PasswordChangeForm()
    
    if request.method == 'GET':
        # Pre-fill form with current user data
        profile_form.username.data = current_user.username
        profile_form.email.data = current_user.email
    
    if profile_form.validate_on_submit() and 'update_profile' in request.form:
        # Check if username is taken by another user
        existing_user = User.get_by_username(profile_form.username.data)
        if existing_user and existing_user.id != current_user.id:
            flash('Username already taken by another user.', 'danger')
            return render_template('auth/profile.html', profile_form=profile_form, password_form=password_form)
        
        # Check if email is taken by another user
        existing_user = User.get_by_email(profile_form.email.data)
        if existing_user and existing_user.id != current_user.id:
            flash('Email already registered to another user.', 'danger')
            return render_template('auth/profile.html', profile_form=profile_form, password_form=password_form)
        
        # Update user profile
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET username = ?, email = ? WHERE id = ?',
            (profile_form.username.data, profile_form.email.data, current_user.id)
        )
        conn.commit()
        conn.close()
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    if password_form.validate_on_submit() and 'change_password' in request.form:
        # Verify current password
        if not current_user.check_password(password_form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return render_template('auth/profile.html', profile_form=profile_form, password_form=password_form)
        
        # Update password
        new_password_hash = generate_password_hash(password_form.new_password.data)
        conn = get_db_connection()
        conn.execute(
            'UPDATE users SET password_hash = ? WHERE id = ?',
            (new_password_hash, current_user.id)
        )
        conn.commit()
        conn.close()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', profile_form=profile_form, password_form=password_form)
