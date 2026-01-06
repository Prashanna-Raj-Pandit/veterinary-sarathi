# Veterinary Sarathi - Educational Platform

A comprehensive web-based educational platform for veterinary science courses with eSewa payment integration for Nepal.

## Features

### 🎓 Student Features
- User registration and authentication with secure password hashing
- Browse comprehensive course catalog with search and filtering
- Course details with curriculum preview
- Shopping cart functionality
- Secure eSewa payment gateway integration
- Personal dashboard with enrolled courses
- Video player for course lectures
- Download PDF notes and PowerPoint presentations
- Course progress tracking
- Payment history

### 👨‍💼 Admin Features
- Secure admin dashboard
- Student management and analytics
- Course creation and management (CRUD operations)
- Content upload (videos, PDFs, presentations)
- Revenue tracking and analytics
- View enrollment statistics
- Manage course pricing and categories

### 🔒 Security Features
- Password hashing using Werkzeug
- CSRF protection
- Session management
- Secure file uploads with validation
- Admin role-based access control
- SQL injection prevention

## Technology Stack

- **Backend:** Flask (Python)
- **Database:** SQLite
- **Authentication:** Flask-Login
- **Forms:** Flask-WTF, WTForms
- **Payment Gateway:** eSewa (Nepal)
- **Frontend:** HTML5, CSS3, JavaScript
- **Styling:** Custom CSS with responsive design

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/Prashanna-Raj-Pandit/veterinary-sarathi.git
cd veterinary-sarathi
```

### Step 2: Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Create a `.env` file in the root directory by copying `.env.example`:
```bash
cp .env.example .env
```

Edit `.env` file with your configuration:
```
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=True

# Admin Credentials (change these!)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@veterinarysarathi.com
ADMIN_PASSWORD=changeme123

# eSewa Configuration
ESEWA_MERCHANT_ID=your-esewa-merchant-id
ESEWA_SECRET_KEY=your-esewa-secret-key
ESEWA_SUCCESS_URL=http://localhost:5000/payment/success
ESEWA_FAILURE_URL=http://localhost:5000/payment/failure
ESEWA_API_URL=https://uat.esewa.com.np/epay/main
```

### Step 5: Initialize the Application
```bash
python app.py
```

The application will:
- Create the SQLite database
- Initialize all required tables
- Create the default admin user
- Set up upload directories

### Step 6: Access the Application
Open your web browser and navigate to:
```
http://localhost:5000
```

## Default Admin Credentials
```
Email: admin@veterinarysarathi.com
Password: changeme123
```
**⚠️ IMPORTANT: Change these credentials immediately after first login!**

## Project Structure
```
veterinary-sarathi/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── models.py                   # Database models
├── forms.py                    # WTForms for validation
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (create from .env.example)
├── .gitignore                  # Git ignore file
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # Authentication routes
│   ├── student.py              # Student portal routes
│   ├── admin.py                # Admin dashboard routes
│   ├── payment.py              # eSewa payment routes
│   └── courses.py              # Course management routes
├── templates/
│   ├── base.html               # Base template
│   ├── index.html              # Landing page
│   ├── auth/                   # Authentication templates
│   ├── student/                # Student portal templates
│   ├── admin/                  # Admin dashboard templates
│   ├── payment/                # Payment templates
│   └── courses/                # Course catalog templates
├── static/
│   ├── css/
│   │   └── style.css           # Main stylesheet
│   ├── js/
│   │   └── main.js             # JavaScript functionality
│   └── images/                 # Static images
└── uploads/                    # User uploaded content
    ├── videos/
    ├── notes/
    └── presentations/
```

## Database Models

### User
- id, username, email, password_hash, is_admin, created_at

### Course
- id, title, description, price, category, thumbnail, instructor_id, created_at

### Content
- id, course_id, title, content_type, file_path, display_order, created_at

### Enrollment
- id, user_id, course_id, enrolled_at, progress

### Payment
- id, user_id, course_id, amount, transaction_id, status, payment_date

### Cart
- id, user_id, course_id, added_at

## Usage Guide

### For Students

1. **Register/Login**
   - Create an account or log in
   - Verify your email (optional feature)

2. **Browse Courses**
   - Search and filter courses by category
   - View course details and curriculum

3. **Purchase Courses**
   - Add courses to cart
   - Proceed to checkout
   - Pay securely via eSewa

4. **Learn**
   - Access enrolled courses from dashboard
   - Watch video lectures
   - Download PDF notes and presentations
   - Track your progress

### For Administrators

1. **Login as Admin**
   - Use admin credentials
   - Access admin dashboard

2. **Manage Courses**
   - Create new courses
   - Edit course details
   - Set pricing and categories
   - Upload course thumbnails

3. **Upload Content**
   - Select course
   - Upload videos, PDFs, or presentations
   - Set display order

4. **Monitor Platform**
   - View student statistics
   - Track enrollments
   - Monitor revenue
   - View analytics

## eSewa Payment Integration

### Development/Testing
The application uses eSewa's UAT (User Acceptance Testing) environment by default. To test payments:

1. Use eSewa test credentials provided by eSewa
2. Test payments will not charge real money
3. Verify payment callbacks are working correctly

### Production Setup
1. Register for eSewa merchant account at https://esewa.com.np
2. Get production credentials (Merchant ID and Secret Key)
3. Update `.env` file with production credentials
4. Change `ESEWA_API_URL` to production URL
5. Test thoroughly before going live

## File Upload Limits
- Maximum file size: 500MB (configurable in `config.py`)
- Supported video formats: mp4, avi, mov, mkv, webm
- Supported document formats: pdf
- Supported presentation formats: ppt, pptx
- Supported image formats: png, jpg, jpeg, gif, webp

## Security Considerations

### For Production Deployment
1. **Change Default Admin Credentials** immediately after first login
2. **Use Strong SECRET_KEY** (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
3. **Enable HTTPS** with SSL/TLS certificate
4. **Set SESSION_COOKIE_SECURE = True** in config.py
5. **Use Environment Variables** for all sensitive data
6. **Regular Backups** of database
7. **Update Dependencies** regularly with `pip install --upgrade -r requirements.txt`
8. **Implement Rate Limiting** to prevent abuse
9. **Add Email Verification** for new user registrations
10. **Configure Proper File Permissions** (uploads directory should be 755 or more restrictive)

### ⚠️ CRITICAL: eSewa Payment Verification
**The current implementation includes development-only payment verification.**

Before deploying to production, you MUST implement proper eSewa payment verification:

1. **Server-to-Server Verification**: Make an API call to eSewa's verification endpoint
2. **Signature Validation**: Verify the payment signature using eSewa's secret key
3. **Amount Validation**: Confirm the payment amount matches the expected amount
4. **Status Check**: Only process enrollment if eSewa confirms payment success

See `routes/payment.py` lines 14-36 and 131-167 for implementation notes.

**Failure to implement proper verification opens the system to payment fraud.**

## Troubleshooting

### Database Issues
```bash
# Delete the database and reinitialize
rm veterinary_sarathi.db
python app.py
```

### Upload Issues
```bash
# Ensure upload directories exist and have proper permissions
mkdir -p uploads/videos uploads/notes uploads/presentations uploads/images
chmod -R 755 uploads/
```

### Dependency Issues
```bash
# Reinstall all dependencies
pip install --upgrade -r requirements.txt
```

## Development

### Running in Debug Mode
```bash
export FLASK_ENV=development  # Linux/macOS
set FLASK_ENV=development     # Windows

python app.py
```

### Adding New Features
1. Create new routes in appropriate route file
2. Add database models if needed in `models.py`
3. Create forms in `forms.py`
4. Add templates in appropriate template directory
5. Update CSS/JS as needed

## Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License
This project is licensed under the MIT License.

## Support
For support and inquiries:
- Email: info@veterinarysarathi.com
- GitHub Issues: [Create an issue](https://github.com/Prashanna-Raj-Pandit/veterinary-sarathi/issues)

## Acknowledgments
- Flask framework and community
- eSewa payment gateway
- All contributors to this project

## Version History
- **v1.0.0** (2024) - Initial release
  - User authentication system
  - Course management
  - eSewa payment integration
  - Admin dashboard
  - Student portal
  - Content management system

---
**Made with ❤️ for Veterinary Education in Nepal**
