from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from flask_login import login_required, current_user
from services import firebase_service as fb
from datetime import datetime
import json
import os

cyberlog_bp = Blueprint('cyberlog', __name__)

@cyberlog_bp.before_request
@login_required
def require_login():
    pass

@cyberlog_bp.route('/cyberlog')
@login_required
def index():
    search = request.args.get('search', '').strip()
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    channel_filter = request.args.get('channel', '')
    sort_by = request.args.get('sort', 'newest')

    incidents = fb.list_incidents(
        user_email=current_user.email,
        search=search,
        status=status_filter,
        category=category_filter,
    )
    if channel_filter:
        incidents = [i for i in incidents if i.submissions.first() and i.submissions.first().channel == channel_filter]

    if sort_by == 'oldest':
        incidents.sort(key=lambda i: i.created_at or datetime.min)
    elif sort_by == 'recently_updated':
        incidents.sort(key=lambda i: i.updated_at or datetime.min, reverse=True)
    elif sort_by == 'status':
        incidents.sort(key=lambda i: i.status or '')

    statuses = ['draft', 'ready', 'prepared', 'sent', 'failed', 'awaiting_confirmation',
                'submitted', 'under_investigation', 'evidence_requested', 'resolved', 'closed']
    categories = sorted(set(inc.category for inc in incidents))

    return render_template('cyberlog/index.html', incidents=incidents, statuses=statuses,
                           categories=categories, search=search, category_filter=category_filter,
                           status_filter=status_filter, channel_filter=channel_filter, sort_by=sort_by)

@cyberlog_bp.route('/cyberlog/<incident_id>')
@login_required
def detail(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident or incident.user_email != current_user.email:
        abort(404)
    submissions = incident.submissions
    evidence = incident.evidence
    comments = incident.comments

    # Parse stored metadata JSON into a human-readable list of (label, value)
    metadata_labels = {
        'incident_date': 'Incident Date',
        'incident_time': 'Incident Time',
        'platform': 'Platform / Service',
        'website_url': 'Website URL',
        'social_media_username': 'Social Media Username',
        'phone_involved': 'Phone Number Involved',
        'email_involved': 'Email Address Involved',
        'transaction_ref': 'Transaction Reference',
        'mobile_money_details': 'Mobile Money Details',
        'bank_provider': 'Bank / Payment Provider',
        'suspected_identifier': 'Suspected Scammer Identifier',
        'metadata_location': 'Location',
        'device': 'Device / Platform Involved',
    }
    metadata_rows = []
    if incident.additional_information:
        try:
            raw = json.loads(incident.additional_information)
            if isinstance(raw, dict):
                metadata_rows = [
                    (metadata_labels.get(k, k.replace('_', ' ').title()), v)
                    for k, v in raw.items()
                    if v not in (None, '')
                ]
        except (ValueError, TypeError):
            metadata_rows = [('Additional Information', incident.additional_information)]

    return render_template('cyberlog/detail.html', incident=incident, submissions=submissions,
                           evidence=evidence, metadata_rows=metadata_rows, comments=comments)

@cyberlog_bp.route('/cyberlog/<incident_id>/delete', methods=['POST'])
@login_required
def delete_incident(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident or incident.user_email != current_user.email or incident.status != 'draft':
        abort(404)
    # Remove evidence files from disk
    for ev in incident.evidence:
        if ev.storage_location and os.path.exists(ev.storage_location):
            try:
                os.remove(ev.storage_location)
            except OSError:
                pass
    fb.delete_incident(incident_id)
    fb.log_audit(current_user.email, 'incident_deleted', f'Draft incident {incident_id} deleted', request.remote_addr)
    flash('Draft deleted.', 'info')
    return redirect(url_for('cyberlog.index'))

@cyberlog_bp.route('/cyberlog/<incident_id>/export')
@login_required
def export_report(incident_id):
    incident = fb.get_incident(incident_id)
    if not incident or incident.user_email != current_user.email:
        abort(404)
    submissions = incident.submissions
    evidence = incident.evidence

    from services.export_service import export_to_pdf
    return export_to_pdf(incident, submissions, evidence, current_user)

@cyberlog_bp.route('/cyberlog/<incident_id>/evidence/<evidence_id>')
@login_required
def evidence_file(incident_id, evidence_id):
    """Serve an evidence file only if it belongs to the current user's incident."""
    incident = fb.get_incident(incident_id)
    if not incident or incident.user_email != current_user.email:
        abort(404)
    evidence = fb.get_evidence_for_incident(incident_id, evidence_id)
    if not evidence or not evidence.storage_location or not os.path.exists(evidence.storage_location):
        abort(404)
    return send_file(evidence.storage_location, as_attachment=False)