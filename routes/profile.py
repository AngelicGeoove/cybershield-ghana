from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from services import firebase_service as fb
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

@profile_bp.before_request
@login_required
def require_login():
    pass

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.organisation = request.form.get('organisation', current_user.organisation)
        current_user.location = request.form.get('location', current_user.location)
        age_str = request.form.get('age', '')
        try:
            current_user.age = int(age_str) if age_str else None
        except ValueError:
            pass
        current_user.updated_at = datetime.utcnow()
        fb.save_user(current_user)
        fb.log_audit(current_user.email, 'profile_updated', 'Profile information updated', request.remote_addr)
        flash('Profile updated.', 'success')
        return redirect(url_for('profile.index'))
    return render_template('profile/index.html', user=current_user)

@profile_bp.route('/profile/export-data')
@login_required
def export_data():
    from services.export_service import export_user_data
    content = export_user_data(current_user)
    filename = f"cybershield_user_data_{current_user.email}.txt"
    return Response(
        content,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@profile_bp.route('/profile/delete-account', methods=['POST'])
@login_required
def delete_account():
    fb.log_audit(current_user.email, 'account_deletion_request', 'User requested account deletion', request.remote_addr)
    fb.delete_user(current_user.email)
    from flask_login import logout_user
    logout_user()
    flash('Your account has been deleted.', 'info')
    return redirect(url_for('auth.index'))