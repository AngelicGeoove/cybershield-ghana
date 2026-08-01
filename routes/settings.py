from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services import firebase_service as fb

settings_bp = Blueprint('settings', __name__)

@settings_bp.before_request
@login_required
def require_login():
    pass

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        csa_form_url = request.form.get('csa_form_url', '')
        csa_email = request.form.get('csa_email', '')
        csa_whatsapp = request.form.get('csa_whatsapp', '')
        if csa_form_url:
            fb.save_channel('CSA Online Form', csa_form_url, csa_form_url, True)
        if csa_email:
            fb.save_channel('CSA Email', csa_email, None, True)
        if csa_whatsapp:
            fb.save_channel('CSA WhatsApp', csa_whatsapp, csa_whatsapp, True)
        fb.log_audit(current_user.email, 'settings_updated', 'Reporting channel settings updated', request.remote_addr)
        flash('Settings updated.', 'success')
        return redirect(url_for('settings.index'))

    channels = fb.list_channels()
    return render_template('settings/index.html', channels=channels)