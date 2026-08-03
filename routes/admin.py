from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import current_user
from services import firebase_service as fb
from datetime import datetime
from routes.permissions import require_roles
import os
from flask import jsonify
from services import threat_intel

admin_bp = Blueprint('admin', __name__)

# Submission pipeline statuses + investigation/case statuses.
# The investigation statuses match the production spec:
#   submitted -> under_investigation -> evidence_requested -> resolved
STATUS_OPTIONS = [
    'draft', 'ready', 'prepared', 'sent', 'failed', 'awaiting_confirmation',
    'submitted', 'under_investigation', 'evidence_requested', 'resolved', 'closed'
]

# All statuses an investigator may set (excludes admin-only lifecycle states)
INVESTIGATOR_STATUS_OPTIONS = [
    'submitted', 'under_investigation', 'evidence_requested', 'resolved'
]

# Every route in this blueprint is ADMIN ONLY.
# The browser (GitHub Pages) version will never include this blueprint; the
# Firestore security rules will deny the equivalent operations client-side.
@admin_bp.before_request
@require_roles('admin')
def require_admin():
    pass

@admin_bp.route('/admin')
def dashboard():
    users = fb.list_users()
    channels = fb.list_channels()
    investigators = fb.list_investigators()

    # Filters
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')
    category = request.args.get('category', '')

    incidents = fb.list_incidents(search=search, status=status, category=category)
    categories = sorted({inc.category for inc in fb.list_incidents() if inc.category})

    return render_template('admin/dashboard.html', users=users, incidents=incidents,
                           channels=channels, search=search, status=status,
                           category=category, categories=categories, statuses=STATUS_OPTIONS,
                           investigators=investigators)

@admin_bp.route('/admin/incident/<incident_id>')
def incident_detail(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident:
        abort(404)
    investigators = fb.list_investigators()
    return render_template('admin/incident_detail.html', incident=incident,
                           submissions=incident.submissions, evidence=incident.evidence,
                           statuses=STATUS_OPTIONS, comments=incident.comments,
                           investigators=investigators)

@admin_bp.route('/admin/incident/<incident_id>/status', methods=['POST'])
def update_status(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident:
        abort(404)
    new_status = request.form.get('status', '')
    if new_status in STATUS_OPTIONS:
        fb.set_incident_status(incident_id, new_status)
        fb.create_notification(
            incident.user_email, 'status_update',
            'Report Status Updated',
            f'Your report {incident.incident_id} status changed to {new_status}.'
        )
        fb.log_audit(current_user.email, 'incident_status_updated',
                     f'{incident.incident_id} -> {new_status}', request.remote_addr)
        flash(f'Status updated to {new_status}.', 'success')
    else:
        flash('Invalid status.', 'error')
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/admin/incident/<incident_id>/comment', methods=['POST'])
def add_comment(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident:
        abort(404)
    message = request.form.get('message', '').strip()
    if not message:
        flash('Comment cannot be empty.', 'error')
        return redirect(request.referrer or url_for('admin.dashboard'))
    fb.add_comment(incident_id, current_user.email, message)
    fb.update_incident(incident_id)
    fb.create_notification(
        incident.user_email, 'investigator_message',
        'Message from Investigator',
        f'An investigator sent you a message about report {incident.incident_id}.'
    )
    fb.log_audit(current_user.email, 'comment_added', f'Comment on {incident.incident_id}', request.remote_addr)
    flash('Comment sent to the reporter.', 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/admin/incident/<incident_id>/assign', methods=['POST'])
def assign_investigator(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident:
        abort(404)
    investigator_email = request.form.get('investigator_email', '').strip().lower()
    if investigator_email:
        investigator = fb.get_user(investigator_email)
        if investigator and investigator.role in ('investigator', 'admin'):
            fb.assign_investigator(incident_id, investigator_email)
            fb.log_audit(current_user.email, 'incident_assigned',
                         f'{incident.incident_id} assigned to {investigator.full_name}', request.remote_addr)
            flash(f'Report assigned to {investigator.full_name}.', 'success')
        else:
            flash('Invalid investigator.', 'error')
    else:
        fb.assign_investigator(incident_id, None)
        flash('Assignment cleared.', 'info')
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/admin/incident/<incident_id>/delete', methods=['POST'])
def delete_incident(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident:
        abort(404)
    for ev in incident.evidence:
        if ev.storage_location and os.path.exists(ev.storage_location):
            try:
                os.remove(ev.storage_location)
            except OSError:
                pass
    fb.log_audit(current_user.email, 'incident_deleted', f'Admin deleted report {incident_id}', request.remote_addr)
    fb.delete_incident(incident_id)
    flash(f'Report {incident_id} deleted.', 'info')
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/admin/evidence/<evidence_id>')
def evidence_file(evidence_id):
    ev = fb.get_evidence(evidence_id)
    if not ev or not ev.storage_location or not os.path.exists(ev.storage_location):
        abort(404)
    return send_file(ev.storage_location)

@admin_bp.route('/admin/audit-log')
def audit_log():
    action = request.args.get('action', '')
    user_email = request.args.get('user_email', '')
    period = request.args.get('period', 'all')

    logs = fb.query_audit_logs(action=action, user_email=user_email, period=period, limit=200)
    actions = fb.audit_actions()
    log_users = [u for u in fb.list_users() if any(l.user_email == u.email for l in fb.query_audit_logs(limit=10000))]

    return render_template('admin/audit_log.html', logs=logs, actions=actions,
                           log_users=log_users, action=action, user_email=user_email, period=period)

@admin_bp.route('/admin/user/<email>/role', methods=['POST'])
def update_user_role(email):
    target = fb.get_user(email)
    if not target:
        abort(404)
    role = request.form.get('role', '')
    if role in ('user', 'investigator', 'admin'):
        old_role = target.role
        target.role = role
        fb.save_user(target)
        fb.log_audit(current_user.email, 'role_changed',
                     f'{target.email}: {old_role} -> {role}', request.remote_addr)
        flash(f'{target.full_name} role updated to {role}.', 'success')
    else:
        flash('Invalid role.', 'error')
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin_bp.route('/admin/add-channel', methods=['POST'])
def add_channel():
    name = request.form.get('channel_name', '').strip()
    destination = request.form.get('destination', '').strip()
    url = request.form.get('official_url', '').strip()
    if name and destination:
        fb.save_channel(name, destination, url or None, active=True)
        fb.log_audit(current_user.email, 'channel_added', f'Added channel: {name}', request.remote_addr)
        flash('Channel added.', 'success')
    else:
        flash('Channel name and destination are required.', 'error')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/admin/toggle-channel/<channel_id>', methods=['POST'])
def toggle_channel(channel_id):
    fb.toggle_channel(channel_id)
    flash('Channel updated.', 'info')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/admin/purge-urlhaus-cache', methods=['POST'])
def purge_urlhaus_cache():
    """Admin-only endpoint to purge the local URLhaus cache file."""
    path = os.path.join(os.path.dirname(__file__), '..', threat_intel.CACHE_FILENAME)
    path = os.path.abspath(path)
    try:
        if os.path.exists(path):
            os.remove(path)
        flash('URLhaus cache purged.', 'success')
        return jsonify({'success': True})
    except Exception:
        flash('Failed to purge cache.', 'error')
        return jsonify({'success': False}), 500