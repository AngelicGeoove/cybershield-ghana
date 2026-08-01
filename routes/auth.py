from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from services import firebase_service as fb

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/<page>')
def static_page(page):
    if page in ('privacy', 'terms'):
        return render_template(f'{page}.html')
    flash('Page not found.', 'error')
    return redirect(url_for('auth.index'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = fb.get_user(email)
        auth_ok = False
        if user:
            # 1) Verify against Firebase Authentication (source of truth).
            uid = fb.verify_password_with_auth(email, password)
            if uid:
                auth_ok = True
                if not user.auth_uid:
                    user.auth_uid = uid
                    fb.save_user(user)
            else:
                # 2) Fallback: legacy bcrypt hash (accounts created before migration).
                if user.check_password(password):
                    auth_ok = True
                    # Self-heal: ensure a Firebase Auth account exists for this email.
                    fb.create_auth_account(email, password)
        if auth_ok:
            login_user(user)
            fb.log_audit(user.email, 'login', 'User logged in', request.remote_addr)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard.index'))
        flash('Invalid email or password.', 'error')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        organisation = request.form.get('organisation', '').strip()
        location = request.form.get('location', '').strip()
        age_str = request.form.get('age', '')

        if not full_name or not email or not password:
            flash('Full name, email, and password are required.', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters.', 'error')
            return render_template('auth/register.html')

        if fb.get_user(email):
            flash('An account with this email already exists.', 'error')
            return render_template('auth/register.html')

        user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            organisation=organisation,
            location=location,
            age=int(age_str) if age_str else None
        )
        user.set_password(password)
        # Create the Firebase Auth account so the same credentials work on the web version.
        auth_record = fb.create_auth_account(email, password)
        if auth_record:
            user.auth_uid = auth_record.uid
        fb.save_user(user)
        fb.log_audit(user.email, 'account_created', 'User account created', request.remote_addr)
        flash('Account created successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    fb.log_audit(current_user.email, 'logout', 'User logged out', request.remote_addr)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.index'))