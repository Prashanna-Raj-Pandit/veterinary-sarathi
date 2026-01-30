import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import os

# Detect Vercel environment
IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None

# Database file path - use /tmp on Vercel
if IS_VERCEL:
    DB_PATH = '/tmp/veterinary_sarathi.db'
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'veterinary_sarathi.db')

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with all required tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category TEXT,
            thumbnail TEXT,
            instructor_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (instructor_id) REFERENCES users (id)
        )
    ''')
    
    # Content table (videos, PDFs, presentations)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
        )
    ''')
    
    # Enrollments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progress REAL DEFAULT 0.0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            UNIQUE(user_id, course_id)
        )
    ''')
    
    # Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            transaction_id TEXT UNIQUE,
            status TEXT DEFAULT 'pending',
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (id)
        )
    ''')
    
    # Cart table for shopping cart functionality
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            course_id INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (course_id) REFERENCES courses (id),
            UNIQUE(user_id, course_id)
        )
    ''')
    
    conn.commit()
    conn.close()

class User(UserMixin):
    """User model for authentication and user management"""
    
    def __init__(self, id, username, email, password_hash, is_admin, created_at):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = is_admin
        self.created_at = created_at
    
    @staticmethod
    def create(username, email, password, is_admin=False):
        """Create a new user"""
        conn = get_db_connection()
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                (username, email, password_hash, 1 if is_admin else 0)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def get_by_id(user_id):
        """Get user by ID"""
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_admin=user_data['is_admin'],
                created_at=user_data['created_at']
            )
        return None
    
    @staticmethod
    def get_by_email(email):
        """Get user by email"""
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_admin=user_data['is_admin'],
                created_at=user_data['created_at']
            )
        return None
    
    @staticmethod
    def get_by_username(username):
        """Get user by username"""
        conn = get_db_connection()
        user_data = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash'],
                is_admin=user_data['is_admin'],
                created_at=user_data['created_at']
            )
        return None
    
    def check_password(self, password):
        """Check if provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get_all_students():
        """Get all non-admin users"""
        conn = get_db_connection()
        students = conn.execute('SELECT * FROM users WHERE is_admin = 0 ORDER BY created_at DESC').fetchall()
        conn.close()
        return students
    
    @staticmethod
    def get_student_count():
        """Get total number of students"""
        conn = get_db_connection()
        count = conn.execute('SELECT COUNT(*) FROM users WHERE is_admin = 0').fetchone()[0]
        conn.close()
        return count

class Course:
    """Course model for managing courses"""
    
    @staticmethod
    def create(title, description, price, category, thumbnail=None, instructor_id=None):
        """Create a new course"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO courses (title, description, price, category, thumbnail, instructor_id) VALUES (?, ?, ?, ?, ?, ?)',
            (title, description, price, category, thumbnail, instructor_id)
        )
        conn.commit()
        course_id = cursor.lastrowid
        conn.close()
        return course_id
    
    @staticmethod
    def get_by_id(course_id):
        """Get course by ID"""
        conn = get_db_connection()
        course = conn.execute('SELECT * FROM courses WHERE id = ?', (course_id,)).fetchone()
        conn.close()
        return course
    
    @staticmethod
    def get_all():
        """Get all courses"""
        conn = get_db_connection()
        courses = conn.execute('SELECT * FROM courses ORDER BY created_at DESC').fetchall()
        conn.close()
        return courses
    
    @staticmethod
    def get_by_category(category):
        """Get courses by category"""
        conn = get_db_connection()
        courses = conn.execute('SELECT * FROM courses WHERE category = ? ORDER BY created_at DESC', (category,)).fetchall()
        conn.close()
        return courses
    
    @staticmethod
    def update(course_id, title, description, price, category, thumbnail=None):
        """Update course details"""
        conn = get_db_connection()
        if thumbnail:
            conn.execute(
                'UPDATE courses SET title = ?, description = ?, price = ?, category = ?, thumbnail = ? WHERE id = ?',
                (title, description, price, category, thumbnail, course_id)
            )
        else:
            conn.execute(
                'UPDATE courses SET title = ?, description = ?, price = ?, category = ? WHERE id = ?',
                (title, description, price, category, course_id)
            )
        conn.commit()
        conn.close()
    
    @staticmethod
    def delete(course_id):
        """Delete a course"""
        conn = get_db_connection()
        conn.execute('DELETE FROM courses WHERE id = ?', (course_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def search(query):
        """Search courses by title or description"""
        conn = get_db_connection()
        search_term = f'%{query}%'
        courses = conn.execute(
            'SELECT * FROM courses WHERE title LIKE ? OR description LIKE ? ORDER BY created_at DESC',
            (search_term, search_term)
        ).fetchall()
        conn.close()
        return courses

class Content:
    """Content model for managing course materials"""
    
    @staticmethod
    def create(course_id, title, content_type, file_path, display_order=0):
        """Create new content"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO content (course_id, title, content_type, file_path, display_order) VALUES (?, ?, ?, ?, ?)',
            (course_id, title, content_type, file_path, display_order)
        )
        conn.commit()
        content_id = cursor.lastrowid
        conn.close()
        return content_id
    
    @staticmethod
    def get_by_course(course_id):
        """Get all content for a specific course"""
        conn = get_db_connection()
        contents = conn.execute(
            'SELECT * FROM content WHERE course_id = ? ORDER BY display_order, created_at',
            (course_id,)
        ).fetchall()
        conn.close()
        return contents
    
    @staticmethod
    def get_by_id(content_id):
        """Get content by ID"""
        conn = get_db_connection()
        content = conn.execute('SELECT * FROM content WHERE id = ?', (content_id,)).fetchone()
        conn.close()
        return content
    
    @staticmethod
    def delete(content_id):
        """Delete content"""
        conn = get_db_connection()
        conn.execute('DELETE FROM content WHERE id = ?', (content_id,))
        conn.commit()
        conn.close()

class Enrollment:
    """Enrollment model for managing student enrollments"""
    
    @staticmethod
    def create(user_id, course_id):
        """Enroll a user in a course"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
                (user_id, course_id)
            )
            conn.commit()
            enrollment_id = cursor.lastrowid
            conn.close()
            return enrollment_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def get_by_user(user_id):
        """Get all enrollments for a user"""
        conn = get_db_connection()
        enrollments = conn.execute(
            '''SELECT e.*, c.title, c.description, c.thumbnail, c.category
               FROM enrollments e
               JOIN courses c ON e.course_id = c.id
               WHERE e.user_id = ?
               ORDER BY e.enrolled_at DESC''',
            (user_id,)
        ).fetchall()
        conn.close()
        return enrollments
    
    @staticmethod
    def is_enrolled(user_id, course_id):
        """Check if user is enrolled in a course"""
        conn = get_db_connection()
        enrollment = conn.execute(
            'SELECT * FROM enrollments WHERE user_id = ? AND course_id = ?',
            (user_id, course_id)
        ).fetchone()
        conn.close()
        return enrollment is not None
    
    @staticmethod
    def update_progress(user_id, course_id, progress):
        """Update course progress for a user"""
        conn = get_db_connection()
        conn.execute(
            'UPDATE enrollments SET progress = ? WHERE user_id = ? AND course_id = ?',
            (progress, user_id, course_id)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_enrollment_count():
        """Get total number of enrollments"""
        conn = get_db_connection()
        count = conn.execute('SELECT COUNT(*) FROM enrollments').fetchone()[0]
        conn.close()
        return count
    
    @staticmethod
    def get_recent_enrollments(limit=10):
        """Get recent enrollments"""
        conn = get_db_connection()
        enrollments = conn.execute(
            '''SELECT e.*, u.username, c.title as course_title
               FROM enrollments e
               JOIN users u ON e.user_id = u.id
               JOIN courses c ON e.course_id = c.id
               ORDER BY e.enrolled_at DESC
               LIMIT ?''',
            (limit,)
        ).fetchall()
        conn.close()
        return enrollments

class Payment:
    """Payment model for managing transactions"""
    
    @staticmethod
    def create(user_id, course_id, amount, transaction_id=None, status='pending'):
        """Create a new payment record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO payments (user_id, course_id, amount, transaction_id, status) VALUES (?, ?, ?, ?, ?)',
            (user_id, course_id, amount, transaction_id, status)
        )
        conn.commit()
        payment_id = cursor.lastrowid
        conn.close()
        return payment_id
    
    @staticmethod
    def update_status(payment_id, status, transaction_id=None):
        """Update payment status"""
        conn = get_db_connection()
        if transaction_id:
            conn.execute(
                'UPDATE payments SET status = ?, transaction_id = ? WHERE id = ?',
                (status, transaction_id, payment_id)
            )
        else:
            conn.execute(
                'UPDATE payments SET status = ? WHERE id = ?',
                (status, payment_id)
            )
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_user(user_id):
        """Get all payments by a user"""
        conn = get_db_connection()
        payments = conn.execute(
            '''SELECT p.*, c.title as course_title
               FROM payments p
               JOIN courses c ON p.course_id = c.id
               WHERE p.user_id = ?
               ORDER BY p.payment_date DESC''',
            (user_id,)
        ).fetchall()
        conn.close()
        return payments
    
    @staticmethod
    def get_by_transaction_id(transaction_id):
        """Get payment by transaction ID"""
        conn = get_db_connection()
        payment = conn.execute('SELECT * FROM payments WHERE transaction_id = ?', (transaction_id,)).fetchone()
        conn.close()
        return payment
    
    @staticmethod
    def get_total_revenue():
        """Get total revenue from successful payments"""
        conn = get_db_connection()
        result = conn.execute("SELECT SUM(amount) FROM payments WHERE status = 'success'").fetchone()
        conn.close()
        return result[0] if result[0] else 0
    
    @staticmethod
    def get_all():
        """Get all payments"""
        conn = get_db_connection()
        payments = conn.execute(
            '''SELECT p.*, u.username, c.title as course_title
               FROM payments p
               JOIN users u ON p.user_id = u.id
               JOIN courses c ON p.course_id = c.id
               ORDER BY p.payment_date DESC'''
        ).fetchall()
        conn.close()
        return payments

class Cart:
    """Cart model for shopping cart functionality"""
    
    @staticmethod
    def add_item(user_id, course_id):
        """Add course to cart"""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO cart (user_id, course_id) VALUES (?, ?)',
                (user_id, course_id)
            )
            conn.commit()
            cart_id = cursor.lastrowid
            conn.close()
            return cart_id
        except sqlite3.IntegrityError:
            conn.close()
            return None
    
    @staticmethod
    def remove_item(user_id, course_id):
        """Remove course from cart"""
        conn = get_db_connection()
        conn.execute('DELETE FROM cart WHERE user_id = ? AND course_id = ?', (user_id, course_id))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_items(user_id):
        """Get all items in user's cart"""
        conn = get_db_connection()
        items = conn.execute(
            '''SELECT c.*, co.title, co.description, co.price, co.thumbnail, co.category
               FROM cart c
               JOIN courses co ON c.course_id = co.id
               WHERE c.user_id = ?
               ORDER BY c.added_at DESC''',
            (user_id,)
        ).fetchall()
        conn.close()
        return items
    
    @staticmethod
    def clear_cart(user_id):
        """Clear all items from user's cart"""
        conn = get_db_connection()
        conn.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_cart_total(user_id):
        """Get total price of items in cart"""
        conn = get_db_connection()
        result = conn.execute(
            '''SELECT SUM(co.price)
               FROM cart c
               JOIN courses co ON c.course_id = co.id
               WHERE c.user_id = ?''',
            (user_id,)
        ).fetchone()
        conn.close()
        return result[0] if result[0] else 0
