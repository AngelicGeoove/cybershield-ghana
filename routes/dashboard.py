from flask import Blueprint, render_template
from flask_login import login_required, current_user
from services import firebase_service as fb

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.before_request
@login_required
def require_login():
    pass

@dashboard_bp.route('/dashboard')
def index():
    incidents = fb.list_incidents(user_email=current_user.email)

    total = len(incidents)
    await_confirm = sum(1 for i in incidents if i.status == 'prepared')
    successful = sum(1 for i in incidents if i.status == 'sent')
    drafts = sum(1 for i in incidents if i.status == 'draft')
    recent = incidents[0] if incidents else None

    notifications = fb.list_notifications(current_user.email)
    notifications_count = sum(1 for n in notifications if not n.read_status)

    # Status breakdown for the dashboard chart
    status_order = ['draft', 'prepared', 'sent', 'failed', 'awaiting_confirmation', 'closed']
    status_labels = {
        'draft': 'Draft',
        'prepared': 'Prepared',
        'sent': 'Sent',
        'failed': 'Failed',
        'awaiting_confirmation': 'Awaiting Confirmation',
        'closed': 'Closed',
    }
    status_counts = []
    for s in status_order:
        count = sum(1 for i in incidents if i.status == s)
        if count > 0:
            status_counts.append({'label': status_labels.get(s, s.title()), 'count': count})

    stats = {
        'total': total,
        'await_confirm': await_confirm,
        'successful': successful,
        'drafts': drafts,
        'recent': recent
    }
    return render_template('dashboard/index.html', stats=stats, notifications_count=notifications_count,
                           status_counts=status_counts)