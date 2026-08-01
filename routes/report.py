import uuid
import json
import os
import sys
import hashlib
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, send_file, abort
from flask_login import login_required, current_user
from services import firebase_service as fb
from config import Config
from extensions import csrf
from services.submission_service import prepare_report_content, submit_to_channel

report_bp = Blueprint('report', __name__)

CATEGORY_LIST = [
    'Online Fraud', 'Phishing', "Unauthorised Access / Account Compromise",
    'Cyberbullying', 'Online Blackmail', 'Identity Theft / Impersonation',
    'Malware', 'Ransomware', 'Social Media Abuse', 'Mobile Money Fraud',
    'Online Shopping Fraud', 'Investment Scam', 'Sextortion / Non-consensual intimate-image abuse',
    'Website Defacement', 'Data Breach', 'Suspected Cybersecurity Vulnerability', 'Other'
]

def get_or_init_draft():
    draft = session.get('draft_report')
    if draft is None:
        draft = {
            'reporter': {}, 'category': '', 'description': '',
            'metadata': {}, 'evidence_files': [], 'channel': '', 'reviewed': False
        }
    return draft

def save_draft(data):
    session['draft_report'] = data

def log_audit(user_id, action, details):
    try:
        fb.log_audit(user_id, action, details, request.remote_addr)
    except Exception:
        pass

@report_bp.route('/report', methods=['GET'])
@login_required
def start_report():
    data = get_or_init_draft()
    if not data.get('reporter'):
        data['reporter'] = {
            'full_name': current_user.full_name,
            'organisation': current_user.organisation or '',
            'email': current_user.email,
            'phone': current_user.phone or '',
            'location': current_user.location or '',
            'age': str(current_user.age) if current_user.age else ''
        }
        save_draft(data)
    return redirect(url_for('report.report_step', step=1))

@report_bp.route('/report/step/<int:step>', methods=['GET', 'POST'])
@login_required
def report_step(step):
    data = get_or_init_draft()
    categories = json.loads(os.environ.get('CSA_CATEGORIES', json.dumps(CATEGORY_LIST)))

    if request.method == 'POST':
        if step == 1:
            data['reporter'] = {
                'full_name': request.form.get('full_name', current_user.full_name),
                'organisation': request.form.get('organisation', current_user.organisation or ''),
                'email': request.form.get('email', current_user.email),
                'phone': request.form.get('phone', current_user.phone or ''),
                'location': request.form.get('location', current_user.location or ''),
                'age': request.form.get('age', str(current_user.age) if current_user.age else '')
            }
        elif step == 2:
            data['category'] = request.form.get('category', '')
        elif step == 3:
            use_guided = request.form.get('use_guided') == 'on'
            manual_desc = request.form.get('description', '')
            data['use_guided'] = use_guided
            if use_guided:
                guided = {
                    'what': request.form.get('guided_what', ''),
                    'when': request.form.get('guided_when', ''),
                    'who': request.form.get('guided_who', ''),
                    'platform': request.form.get('guided_platform', ''),
                    'asked_to_do': request.form.get('guided_asked_to_do', ''),
                    'happened_after': request.form.get('guided_happened_after', '')
                }
                # Persist guided answers so they survive navigating back to this step
                data.update({f'guided_{k}': v for k, v in guided.items()})
                guided_desc = build_guided_desc(guided)
                # Prefer guided output, but never clobber a manual description
                # with an empty string if the user checked the box but filled
                # nothing in the questionnaire.
                data['description'] = guided_desc or manual_desc
            else:
                data['description'] = manual_desc
        elif step == 4:
            data['metadata'] = {
                'incident_date': request.form.get('incident_date', ''),
                'incident_time': request.form.get('incident_time', ''),
                'platform': request.form.get('platform', ''),
                'website_url': request.form.get('website_url', ''),
                'social_media_username': request.form.get('social_media_username', ''),
                'phone_involved': request.form.get('phone_involved', ''),
                'email_involved': request.form.get('email_involved', ''),
                'transaction_ref': request.form.get('transaction_ref', ''),
                'mobile_money_details': request.form.get('mobile_money_details', ''),
                'bank_provider': request.form.get('bank_provider', ''),
                'suspected_identifier': request.form.get('suspected_identifier', ''),
                'metadata_location': request.form.get('metadata_location', ''),
                'device': request.form.get('device', '')
            }
        elif step == 5:
            pass
        elif step == 6:
            data['channel'] = request.form.get('channel', '')
            data['reviewed'] = True
            save_draft(data)
            return redirect(url_for('report.review'))

        save_draft(data)
        flash(f'Step {step} saved.', 'success')
        if step < 6:
            return redirect(url_for('report.report_step', step=step + 1))
        return redirect(url_for('report.confirmation'))

    return render_template(f'report/step_{step}.html', step=step, categories=categories, data=data)

def build_guided_desc(guided):
    parts = []
    if guided.get('what'):
        parts.append(f"What happened: {guided['what']}")
    if guided.get('when'):
        parts.append(f"When: {guided['when']}")
    if guided.get('who'):
        parts.append(f"Who contacted you: {guided['who']}")
    if guided.get('platform'):
        parts.append(f"Platform: {guided['platform']}")
    if guided.get('asked_to_do'):
        parts.append(f"What they asked: {guided['asked_to_do']}")
    if guided.get('happened_after'):
        parts.append(f"What happened after: {guided['happened_after']}")
    return '\n\n'.join(parts)

@report_bp.route('/report/review', methods=['GET'])
@login_required
def review():
    data = get_or_init_draft()
    return render_template('report/step_review.html', data=data, step=6)

@report_bp.route('/report/confirmation', methods=['GET'])
@login_required
def confirmation():
    incident_id = request.args.get('incident_id')
    incident = None
    channel = 'N/A'
    if incident_id:
        incident = fb.get_incident(incident_id)
        if incident and incident.user_email != current_user.email:
            incident = None
    if incident:
        first_sub = incident.submissions.first()
        channel = first_sub.channel if first_sub else 'N/A'
    return render_template('report/confirmation.html', data={'channel': channel},
                           incident_id=incident_id, category=incident.category if incident else 'N/A')

@report_bp.route('/report/save-draft', methods=['POST'])
@login_required
@csrf.exempt
def save_draft_route():
    data = get_or_init_draft()
    incident = fb.create_incident(
        current_user.email,
        category=data.get('category', ''),
        description=data.get('description', ''),
        additional_information=json.dumps(data.get('metadata', {})),
        status='draft',
        message=data.get('description', '')
    )
    log_audit(current_user.email, 'report_saved_draft', f'Draft saved for incident {incident.incident_id}')
    return jsonify({'success': True, 'redirect': url_for('dashboard.index')})

@report_bp.route('/report/submit', methods=['POST'])
@login_required
def submit_report():
    data = get_or_init_draft()
    channel = data.get('channel', '')

    incident = fb.create_incident(
        current_user.email,
        category=data.get('category', ''),
        incident_date=_parse_date(data.get('metadata', {}).get('incident_date')),
        incident_time=data.get('metadata', {}).get('incident_time', ''),
        platform=data.get('metadata', {}).get('platform', ''),
        description=data.get('description', ''),
        message=data.get('description', ''),
        additional_information=json.dumps(data.get('metadata', {})),
        status='prepared'
    )
    log_audit(current_user.email, 'report_created', f'Incident {incident.incident_id} created')

    # Persist evidence metadata (files themselves stay in the local uploads folder)
    for fname, fmeta in data.get('evidence_files', []):
        fb.add_evidence(
            incident.incident_id,
            file_name=fmeta.get('name', fname),
            file_type=fmeta.get('type', ''),
            file_size=fmeta.get('size', 0),
            storage_location=fmeta.get('path', ''),
            checksum_hash=fmeta.get('hash', '')
        )

    submission_id = fb.add_submission(incident.incident_id, channel, status='prepared')

    content = prepare_report_content(data)
    result = submit_to_channel(channel, content, incident.incident_id)

    submitted_at = datetime.utcnow() if result.get('status') == 'sent' else None
    fb.update_submission(
        incident.incident_id, submission_id,
        status=result.get('status', 'failed'),
        submitted_at=submitted_at,
        error_message=result.get('error'),
        external_reference=result.get('external_ref')
    )

    final_status = result.get('status', 'failed')
    fb.update_incident(incident.incident_id, status=final_status)

    if final_status == 'sent':
        notif_type, title = 'submission_success', 'Report Submitted'
        message = f'Your report {incident.incident_id} was sent via {channel}.'
    else:
        notif_type, title = 'submission_failed', 'Submission Issue'
        message = f'Report prepared but could not be sent via {channel}.'
    fb.create_notification(current_user.email, notif_type, title, message)

    save_draft({
        'reporter': {}, 'category': '', 'description': '',
        'metadata': {}, 'evidence_files': [], 'channel': '', 'reviewed': False
    })

    return redirect(url_for('report.confirmation', incident_id=incident.incident_id))

@report_bp.route('/report/upload-evidence', methods=['POST'])
@login_required
def upload_evidence():
    data = get_or_init_draft()
    files = request.files.getlist('files')
    allowed = Config.ALLOWED_EXTENSIONS

    for f in files:
        if not f.filename:
            continue
        parts = f.filename.rsplit('.', 1)
        ext = parts[-1].lower() if len(parts) > 1 else ''
        if ext not in allowed:
            flash(f'File type not allowed: {f.filename}', 'error')
            continue
        fname = f.filename
        f.seek(0, os.SEEK_END)
        fsize = f.tell()
        f.seek(0)
        if fsize > 10 * 1024 * 1024:
            flash(f'File too large: {fname}', 'error')
            continue
        safe_name = str(uuid.uuid4()) + '_' + fname
        save_path = os.path.join(Config.UPLOAD_FOLDER, safe_name)
        f.save(save_path)
        with open(save_path, 'rb') as fh:
            file_hash = hashlib.sha256(fh.read()).hexdigest()
        # Files stay local for now; metadata is persisted to Firestore at submit time.
        meta = {
            'name': fname, 'type': ext, 'size': fsize,
            'path': save_path, 'hash': file_hash, 'id': uuid.uuid4().hex
        }
        ev_list = data.get('evidence_files', [])
        ev_list.append((fname, meta))

    save_draft(data)
    flash('Evidence uploaded.', 'success')
    return redirect(url_for('report.report_step', step=5))

@report_bp.route('/report/remove-evidence/<evidence_id>', methods=['POST'])
@login_required
def remove_evidence(evidence_id):
    data = get_or_init_draft()
    removed = False
    for fname, meta in data.get('evidence_files', []):
        if meta.get('id') == evidence_id and meta.get('path') and os.path.exists(meta['path']):
            try:
                os.remove(meta['path'])
            except OSError:
                pass
            removed = True
            break
    if removed:
        data['evidence_files'] = [
            (fn, m) for fn, m in data.get('evidence_files', [])
            if m.get('id') != evidence_id
        ]
        save_draft(data)
        flash('Evidence removed.', 'info')
    else:
        flash('Evidence not found in this draft.', 'error')
    return redirect(url_for('report.report_step', step=5))

@report_bp.route('/report/evidence/<evidence_id>')
@login_required
def evidence_preview(evidence_id):
    """Serve an evidence file during the wizard, only if it is in the current session's draft."""
    data = get_or_init_draft()
    for _, meta in data.get('evidence_files', []):
        if meta.get('id') == evidence_id:
            if meta.get('path') and os.path.exists(meta['path']):
                return send_file(meta['path'], as_attachment=False)
            abort(404)
    abort(404)

@report_bp.route('/report/guided-description', methods=['POST'])
@login_required
def guided_description():
    guided = {
        'what': request.form.get('guided_what', ''),
        'when': request.form.get('guided_when', ''),
        'who': request.form.get('guided_who', ''),
        'platform': request.form.get('guided_platform', ''),
        'asked_to_do': request.form.get('guided_asked_to_do', ''),
        'happened_after': request.form.get('guided_happened_after', '')
    }
    desc = build_guided_desc(guided)
    return jsonify({'description': desc})

def _parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None