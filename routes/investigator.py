from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file
from flask_login import current_user
from services import firebase_service as fb
from routes.permissions import require_roles
from routes.admin import INVESTIGATOR_STATUS_OPTIONS

investigator_bp = Blueprint('investigator', __name__)

# Investigator console - accessible to investigators AND admins.
# Only reports assigned to the current user are shown/editable.
# Admins also see this console so they can act as investigators when needed.

@investigator_bp.before_request
@require_roles('investigator', 'admin')
def require_investigator():
    pass


@investigator_bp.route('/investigator')
def dashboard():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')

    incidents = fb.list_incidents(assigned_to=current_user.email, search=search, status=status)

    unassigned = fb.list_incidents(unassigned=True) if current_user.role == 'admin' else []

    return render_template('investigator/dashboard.html', incidents=incidents,
                           search=search, status=status, unassigned=len(unassigned),
                           statuses=INVESTIGATOR_STATUS_OPTIONS)


@investigator_bp.route('/investigator/<incident_id>')
def incident_detail(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident or incident.assigned_investigator_email != current_user.email:
        abort(404)
    return render_template('investigator/incident_detail.html', incident=incident,
                           evidence=incident.evidence, comments=incident.comments,
                           statuses=INVESTIGATOR_STATUS_OPTIONS)


@investigator_bp.route('/investigator/<incident_id>/status', methods=['POST'])
def update_status(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident or incident.assigned_investigator_email != current_user.email:
        abort(404)
    new_status = request.form.get('status', '')
    if new_status in INVESTIGATOR_STATUS_OPTIONS:
        fb.set_incident_status(incident_id, new_status)
        fb.create_notification(
            incident.user_email, 'status_update',
            'Case Update',
            f'Your report {incident.incident_id} status changed to {new_status}.'
        )
        fb.log_audit(current_user.email, 'case_status_updated',
                     f'{incident.incident_id} -> {new_status}', request.remote_addr)
        flash(f'Status updated to {new_status}.', 'success')
    else:
        flash('Invalid status.', 'error')
    return redirect(request.referrer or url_for('investigator.dashboard'))


@investigator_bp.route('/investigator/<incident_id>/comment', methods=['POST'])
def add_comment(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident or incident.assigned_investigator_email != current_user.email:
        abort(404)
    message = request.form.get('message', '').strip()
    if not message:
        flash('Comment cannot be empty.', 'error')
        return redirect(request.referrer or url_for('investigator.dashboard'))

    fb.add_comment(incident_id, current_user.email, message)
    fb.update_incident(incident_id)
    fb.create_notification(
        incident.user_email, 'investigator_message',
        'Message from Investigator',
        f'An investigator sent you a message about report {incident.incident_id}.'
    )
    fb.log_audit(current_user.email, 'comment_added', f'Comment on {incident.incident_id}', request.remote_addr)
    flash('Comment sent to the reporter.', 'success')
    return redirect(request.referrer or url_for('investigator.dashboard'))


@investigator_bp.route('/investigator/<incident_id>/evidence/<evidence_id>')
def evidence_file(incident_id, evidence_id):
    incident = fb.get_incident(incident_id)
    if not incident or incident.assigned_investigator_email != current_user.email:
        abort(404)
    import os
    evidence = fb.get_evidence_for_incident(incident_id, evidence_id)
    if not evidence or not evidence.storage_location or not os.path.exists(evidence.storage_location):
        abort(404)
    return send_file(evidence.storage_location, as_attachment=False)


@investigator_bp.route('/investigator/<incident_id>/claim', methods=['POST'])
def claim_incident(incident_id):
    """Admins can pick up an unassigned report directly from the console."""
    if current_user.role != 'admin':
        abort(403)
    incident = fb.get_incident(incident_id)
    if not incident:
        abort(404)
    if not incident.assigned_investigator_email:
        fb.assign_investigator(incident_id, current_user.email)
        fb.log_audit(current_user.email, 'incident_claimed',
                     f'{incident.incident_id} claimed by admin', request.remote_addr)
        flash('Report claimed.', 'success')
    return redirect(request.referrer or url_for('investigator.dashboard'))
