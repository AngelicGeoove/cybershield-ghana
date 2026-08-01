from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required
from services import firebase_service as fb

channels_bp = Blueprint('channels', __name__)

@channels_bp.before_request
@login_required
def require_login():
    pass

@channels_bp.route('/channels')
@login_required
def index():
    channels = fb.list_channels(active_only=True)
    return render_template('channels/index.html', channels=channels)

@channels_bp.route('/channels/report-email', methods=['POST'])
@login_required
def report_via_email():
    data = get_draft_data()
    channel = data.get('channel', 'email')
    return redirect(url_for('report.submit_report'))

@channels_bp.route('/channels/report-whatsapp', methods=['POST'])
@login_required
def report_via_whatsapp():
    data = get_draft_data()
    channel = data.get('channel', 'whatsapp')
    return redirect(url_for('report.submit_report'))

def get_draft_data():
    return session.get('draft_report', {})