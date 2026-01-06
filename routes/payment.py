from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Course, Payment, Enrollment, Cart, get_db_connection
from config import Config
import hashlib
import uuid

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

def generate_transaction_id():
    """Generate a unique transaction ID"""
    return str(uuid.uuid4())

def verify_esewa_signature(params):
    """
    Verify eSewa payment signature for security
    
    IMPORTANT: In production, this must verify the payment with eSewa's server
    by making an API call to their verification endpoint with the transaction details.
    
    For development/testing, this performs basic validation only.
    """
    # Check required parameters are present
    required_params = ['oid', 'amt', 'refId']
    for param in required_params:
        if param not in params:
            return False
    
    # TODO: In production, implement actual eSewa signature verification
    # Example:
    # 1. Construct verification request with transaction details
    # 2. Make POST request to eSewa verification endpoint
    # 3. Parse and validate response
    # 4. Return True only if eSewa confirms the payment
    
    # For now, return True for development (MUST BE FIXED FOR PRODUCTION)
    return True

@payment_bp.route('/initiate/<int:course_id>', methods=['POST'])
@login_required
def initiate_payment(course_id):
    """Initiate eSewa payment for a single course"""
    if current_user.is_admin:
        flash('Admin users cannot make purchases.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    course = Course.get_by_id(course_id)
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('student.courses'))
    
    # Check if already enrolled
    if Enrollment.is_enrolled(current_user.id, course_id):
        flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('student.dashboard'))
    
    # Create payment record
    transaction_id = generate_transaction_id()
    payment_id = Payment.create(
        user_id=current_user.id,
        course_id=course_id,
        amount=course['price'],
        transaction_id=transaction_id,
        status='pending'
    )
    
    # Prepare eSewa payment data
    esewa_data = {
        'amt': course['price'],
        'psc': 0,  # Service charge
        'pdc': 0,  # Delivery charge
        'txAmt': 0,  # Tax amount
        'tAmt': course['price'],  # Total amount
        'pid': transaction_id,  # Product/Transaction ID
        'scd': Config.ESEWA_MERCHANT_ID,  # Merchant ID
        'su': Config.ESEWA_SUCCESS_URL,  # Success URL
        'fu': Config.ESEWA_FAILURE_URL   # Failure URL
    }
    
    return render_template('payment/esewa_redirect.html', 
                         esewa_data=esewa_data,
                         esewa_url=Config.ESEWA_API_URL,
                         course=course)

@payment_bp.route('/initiate-cart', methods=['POST'])
@login_required
def initiate_cart_payment():
    """Initiate eSewa payment for all items in cart"""
    if current_user.is_admin:
        flash('Admin users cannot make purchases.', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    cart_items = Cart.get_items(current_user.id)
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('student.cart'))
    
    total_amount = Cart.get_cart_total(current_user.id)
    
    # Create payment records for each course in cart
    transaction_id = generate_transaction_id()
    
    for item in cart_items:
        # Check if already enrolled (shouldn't happen, but safety check)
        if not Enrollment.is_enrolled(current_user.id, item['course_id']):
            Payment.create(
                user_id=current_user.id,
                course_id=item['course_id'],
                amount=item['price'],
                transaction_id=transaction_id,
                status='pending'
            )
    
    # Prepare eSewa payment data
    esewa_data = {
        'amt': total_amount,
        'psc': 0,
        'pdc': 0,
        'txAmt': 0,
        'tAmt': total_amount,
        'pid': transaction_id,
        'scd': Config.ESEWA_MERCHANT_ID,
        'su': Config.ESEWA_SUCCESS_URL,
        'fu': Config.ESEWA_FAILURE_URL
    }
    
    return render_template('payment/esewa_redirect.html', 
                         esewa_data=esewa_data,
                         esewa_url=Config.ESEWA_API_URL,
                         cart_items=cart_items,
                         total=total_amount)

@payment_bp.route('/success')
@login_required
def payment_success():
    """Handle successful payment callback from eSewa"""
    # Get parameters from eSewa
    oid = request.args.get('oid')  # Transaction ID
    amt = request.args.get('amt')  # Amount
    refId = request.args.get('refId')  # eSewa reference ID
    
    if not oid or not amt or not refId:
        flash('Invalid payment response. Please contact support.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # CRITICAL: Verify payment with eSewa server
    # WARNING: This is a development version. In production, you MUST:
    # 1. Make a server-to-server call to eSewa verification endpoint
    # 2. Verify the signature and transaction details
    # 3. Only process enrollment if eSewa confirms the payment
    
    # For development: Add warning log
    import logging
    logging.warning(f"Payment callback received without server verification for transaction {oid}. "
                   "This MUST be implemented before production deployment!")
    
    # Verify payment (in production, verify with eSewa server)
    verification_params = {'oid': oid, 'amt': amt, 'refId': refId}
    if not verify_esewa_signature(verification_params):
        flash('Payment verification failed. Please contact support.', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # Update payment status
    conn = get_db_connection()
    payments = conn.execute(
        'SELECT * FROM payments WHERE transaction_id = ? AND status = ?',
        (oid, 'pending')
    ).fetchall()
    
    if not payments:
        conn.close()
        flash('Payment record not found or already processed.', 'warning')
        return redirect(url_for('student.dashboard'))
    
    # Process each payment in the transaction
    for payment in payments:
        # Update payment status
        conn.execute(
            'UPDATE payments SET status = ?, transaction_id = ? WHERE id = ?',
            ('success', f"{oid}_{refId}", payment['id'])
        )
        
        # Enroll user in course
        Enrollment.create(payment['user_id'], payment['course_id'])
        
        # Remove from cart if exists
        Cart.remove_item(payment['user_id'], payment['course_id'])
    
    conn.commit()
    conn.close()
    
    flash('Payment successful! You have been enrolled in the course(s).', 'success')
    return redirect(url_for('student.dashboard'))

@payment_bp.route('/failure')
@login_required
def payment_failure():
    """Handle failed payment callback from eSewa"""
    # Get transaction ID if available
    pid = request.args.get('pid')
    
    if pid:
        # Update payment status to failed
        conn = get_db_connection()
        conn.execute(
            'UPDATE payments SET status = ? WHERE transaction_id = ?',
            ('failed', pid)
        )
        conn.commit()
        conn.close()
    
    flash('Payment failed or was cancelled. Please try again.', 'danger')
    return redirect(url_for('student.cart'))

@payment_bp.route('/verify', methods=['POST'])
def verify_payment():
    """Verify payment with eSewa server (webhook/callback)"""
    # This endpoint would be used for server-to-server verification
    # In production, implement proper eSewa payment verification API call
    
    # Get payment details from eSewa
    data = request.form or request.json
    
    if not data:
        return {'success': False, 'message': 'No data received'}, 400
    
    # Extract and verify payment details
    amt = data.get('amt')
    rid = data.get('rid')  # Reference ID from eSewa
    pid = data.get('pid')  # Product/Transaction ID
    
    if not all([amt, rid, pid]):
        return {'success': False, 'message': 'Missing parameters'}, 400
    
    # In production, verify with eSewa server using their verification API
    # For now, return success
    
    return {'success': True, 'message': 'Payment verified'}

@payment_bp.route('/history')
@login_required
def payment_history():
    """View payment history for current user"""
    if current_user.is_admin:
        # Admin views all payments
        payments = Payment.get_all()
    else:
        # Student views their own payments
        payments = Payment.get_by_user(current_user.id)
    
    return render_template('payment/history.html', payments=payments)
