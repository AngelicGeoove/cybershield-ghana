"""Firestore data layer for CyberShield Ghana (desktop app).

All persistence goes through this module. The lightweight model classes in
models.py are hydrated from Firestore documents.

Firestore layout
----------------
users/{email}                      -> profile + role + legacy bcrypt hash
incidents/{incident_id}            -> incident fields
incidents/{id}/evidence/{eid}      -> evidence metadata (files stay local)
incidents/{id}/submissions/{sid}   -> channel submission attempts
incidents/{id}/comments/{cid}      -> investigator <-> reporter messages
notifications/{nid}                -> per-user notifications
audit_logs/{aid}                   -> security-relevant actions
reporting_channels/{slug}          -> configured CSA channels
"""
import os
import sys
import uuid
import requests
from datetime import datetime, date

from firebase_admin import credentials, firestore, auth as admin_auth, initialize_app, get_app

from models import (
    User, Incident, Evidence, Submission, Notification,
    AuditLog, ReportingChannel, InvestigatorComment,
)

CREDENTIALS_FILE = 'firebase-adminsdk.json'
# Public Firebase Web API key (safe to ship - used for the Auth REST endpoint)
WEB_API_KEY = os.environ.get('FIREBASE_WEB_API_KEY', 'AIzaSyBefRp77pRx93GvbhUQ9AZ0a4oX9hlZ7Tc')

_firestore = None


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def _find_credentials():
    """Locate the service-account JSON in several sensible places.

    Order: FIREBASE_CREDENTIALS env var -> next to the exe -> project root
    -> bundled inside the PyInstaller archive.
    """
    env_path = os.environ.get('FIREBASE_CREDENTIALS')
    if env_path and os.path.exists(env_path):
        return env_path

    candidates = []
    if hasattr(sys, 'frozen'):
        candidates.append(os.path.join(os.path.dirname(sys.executable), CREDENTIALS_FILE))
    candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', CREDENTIALS_FILE))
    if hasattr(sys, '_MEIPASS'):
        candidates.append(os.path.join(sys._MEIPASS, CREDENTIALS_FILE))
    for c in candidates:
        if os.path.exists(c):
            return os.path.normpath(c)
    return None


def init_firebase():
    """Initialize the Firebase Admin SDK once. Safe to call multiple times."""
    global _firestore
    if _firestore is not None:
        return _firestore
    cred_path = _find_credentials()
    if not cred_path:
        raise RuntimeError(
            f'Firebase credentials file not found: {CREDENTIALS_FILE}\n'
            'Download the service account key from Firebase console -> '
            'Project Settings -> Service accounts -> Generate new private key, '
            f'and save it next to the app as {CREDENTIALS_FILE} '
            '(or set FIREBASE_CREDENTIALS to its path).'
        )
    try:
        initialize_app(credentials.Certificate(cred_path))
    except ValueError:
        pass  # Already initialized
    _firestore = firestore.client()
    return _firestore


def _db():
    return _firestore or init_firebase()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_id():
    return uuid.uuid4().hex


def _slugify(name):
    return name.strip().lower().replace(' ', '-').replace('/', '-').replace('@', '-at-')


def _to_iso_date(d):
    """Serialize a date to 'YYYY-MM-DD' (Firestore has no date type)."""
    if d is None:
        return None
    if isinstance(d, str):
        return d
    return d.isoformat() if hasattr(d, 'isoformat') else str(d)


def _parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(str(s))
    except (ValueError, TypeError):
        return None


def _find_user(email):
    """Fetch a User by email, or None."""
    email = (email or '').lower()
    if not email:
        return None
    doc = _db().collection('users').document(email).get()
    if not doc.exists:
        return None
    return _user_from_doc(doc)


def _user_from_doc(doc):
    d = doc.to_dict() or {}
    u = User(
        id=d.get('legacy_id'),
        email=doc.id,
        full_name=d.get('full_name', ''),
        phone=d.get('phone', ''),
        organisation=d.get('organisation', ''),
        location=d.get('location', ''),
        age=d.get('age'),
        role=d.get('role', 'user'),
        email_verified=d.get('email_verified', False),
        account_status=d.get('account_status', 'active'),
        password_hash=d.get('password_hash', ''),
        auth_uid=d.get('auth_uid'),
        created_at=d.get('created_at') or datetime.utcnow(),
        updated_at=d.get('updated_at') or datetime.utcnow(),
    )
    return u


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def get_user(email):
    return _find_user(email)


def list_users():
    docs = _db().collection('users').stream()
    users = [_user_from_doc(d) for d in docs]
    users.sort(key=lambda u: u.created_at or datetime.min, reverse=True)
    return users


def list_investigators():
    return [u for u in list_users() if u.role in ('investigator', 'admin')]


def save_user(user):
    """Upsert a user document from a User object."""
    data = {
        'email': user.email,
        'legacy_id': user.id,
        'full_name': user.full_name,
        'phone': user.phone,
        'organisation': user.organisation,
        'location': user.location,
        'age': user.age,
        'role': user.role,
        'email_verified': user.email_verified,
        'account_status': user.account_status,
        'password_hash': user.password_hash,
        'auth_uid': user.auth_uid,
        'created_at': user.created_at or datetime.utcnow(),
        'updated_at': datetime.utcnow(),
    }
    _db().collection('users').document(user.email).set(data, merge=True)


def delete_user(email):
    _db().collection('users').document(email.lower()).delete()


# ---------------------------------------------------------------------------
# Auth (Firebase Authentication via Admin SDK + REST fallback)
# ---------------------------------------------------------------------------

def create_auth_account(email, password):
    """Create a Firebase Auth account (email/password) via Admin SDK."""
    try:
        return admin_auth.create_user(email=email, password=password)
    except admin_auth.EmailAlreadyExistsError:
        return admin_auth.get_user_by_email(email)
    except Exception:
        # Missing/disabled Email/Password provider or other transient issue
        return None


def get_auth_user(email):
    try:
        return admin_auth.get_user_by_email(email)
    except Exception:
        return None


def verify_password_with_auth(email, password):
    """Verify credentials against Firebase Auth's REST endpoint.

    Returns the Firebase Auth UID on success, else None.
    """
    try:
        resp = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={WEB_API_KEY}',
            json={'email': email, 'password': password, 'returnSecureToken': True},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json().get('localId')
    except requests.RequestException:
        pass
    return None


# ---------------------------------------------------------------------------
# Incidents
# ---------------------------------------------------------------------------

def _incident_dict(incident):
    return {
        'legacy_id': incident.id,
        'user_email': incident.user_email,
        'assigned_investigator_email': incident.assigned_investigator_email or '',
        'category': incident.category,
        'incident_date': _to_iso_date(incident.incident_date),
        'incident_time': incident.incident_time,
        'platform': incident.platform,
        'description': incident.description,
        'message': incident.message,
        'additional_information': incident.additional_information,
        'status': incident.status,
        'created_at': incident.created_at or datetime.utcnow(),
        'updated_at': incident.updated_at or datetime.utcnow(),
    }


def _incident_from_doc(doc):
    d = doc.to_dict() or {}
    inc = Incident(
        id=d.get('legacy_id'),
        incident_id=doc.id,
        user_email=d.get('user_email', ''),
        assigned_investigator_email=d.get('assigned_investigator_email') or None,
        category=d.get('category', ''),
        incident_date=_parse_date(d.get('incident_date')),
        incident_time=d.get('incident_time', ''),
        platform=d.get('platform', ''),
        description=d.get('description', ''),
        message=d.get('message', ''),
        additional_information=d.get('additional_information', ''),
        status=d.get('status', 'draft'),
        created_at=d.get('created_at') or datetime.utcnow(),
        updated_at=d.get('updated_at') or datetime.utcnow(),
    )
    # Hydrate reporter + assigned investigator (lightweight: no subcollection load here)
    inc.user = _find_user(inc.user_email)
    if inc.assigned_investigator_email:
        inc.assigned_investigator = _find_user(inc.assigned_investigator_email)
    return inc


def _hydrate_incident(inc):
    """Load evidence, submissions and comments into an Incident object."""
    inc_id = inc.incident_id
    inc.evidence = _Rel_from(_list_evidence(inc_id))
    inc.submissions = _Rel_from(_list_submissions(inc_id))
    inc.comments = _Rel_from(_list_comments(inc_id))
    return inc


def _Rel_from(items):
    from models import _Rel
    r = _Rel()
    r.extend(items)
    return r


def create_incident(user_email, **fields):
    incident_id = fields.get('incident_id') or _new_id()
    now = datetime.utcnow()
    inc = Incident(
        incident_id=incident_id,
        user_email=user_email,
        category=fields.get('category', ''),
        incident_date=fields.get('incident_date'),
        incident_time=fields.get('incident_time', ''),
        platform=fields.get('platform', ''),
        description=fields.get('description', ''),
        message=fields.get('message', ''),
        additional_information=fields.get('additional_information', ''),
        status=fields.get('status', 'draft'),
        created_at=fields.get('created_at', now),
        updated_at=fields.get('updated_at', now),
    )
    _db().collection('incidents').document(incident_id).set(_incident_dict(inc))
    inc.user = _find_user(user_email)
    return inc


def get_incident(incident_id):
    doc = _db().collection('incidents').document(incident_id).get()
    if not doc.exists:
        return None
    return _hydrate_incident(_incident_from_doc(doc))


def update_incident(incident_id, **fields):
    """Update fields on an incident. Returns the hydrated Incident or None."""
    doc = _db().collection('incidents').document(incident_id)
    snapshot = doc.get()
    if not snapshot.exists:
        return None
    existing = snapshot.to_dict() or {}
    data = {
        'assigned_investigator_email': fields.get('assigned_investigator_email', existing.get('assigned_investigator_email', '')),
        'category': fields.get('category', existing.get('category', '')),
        'incident_date': _to_iso_date(fields.get('incident_date', _parse_date(existing.get('incident_date')))),
        'incident_time': fields.get('incident_time', existing.get('incident_time', '')),
        'platform': fields.get('platform', existing.get('platform', '')),
        'description': fields.get('description', existing.get('description', '')),
        'message': fields.get('message', existing.get('message', '')),
        'additional_information': fields.get('additional_information', existing.get('additional_information', '')),
        'status': fields.get('status', existing.get('status', 'draft')),
        'updated_at': datetime.utcnow(),
    }
    doc.set(data, merge=True)
    return get_incident(incident_id)


def set_incident_status(incident_id, status):
    return update_incident(incident_id, status=status)


def assign_investigator(incident_id, investigator_email):
    return update_incident(incident_id, assigned_investigator_email=investigator_email or '')


def delete_incident(incident_id):
    ref = _db().collection('incidents').document(incident_id)
    for sub in _list_submissions(incident_id):
        ref.collection('submissions').document(sub.id).delete()
    for ev in _list_evidence(incident_id):
        ref.collection('evidence').document(ev.id).delete()
    for cm in _list_comments(incident_id):
        ref.collection('comments').document(cm.id).delete()
    ref.delete()


def list_incidents(user_email=None, assigned_to=None, unassigned=False,
                   search='', status='', category=''):
    """Fetch incidents, filtering in Python to avoid composite index errors."""
    query = _db().collection('incidents')
    incidents = [_incident_from_doc(d) for d in query.stream()]

    if user_email:
        incidents = [i for i in incidents if i.user_email == user_email.lower()]
    if assigned_to:
        incidents = [i for i in incidents if i.assigned_investigator_email == assigned_to.lower()]
    if unassigned:
        incidents = [i for i in incidents if not i.assigned_investigator_email]
    if status:
        incidents = [i for i in incidents if i.status == status]
    if category:
        incidents = [i for i in incidents if i.category == category]
    if search:
        s = search.lower()
        incidents = [
            i for i in incidents
            if s in i.incident_id.lower()
            or s in (i.category or '').lower()
            or s in (i.description or '').lower()
            or s in (i.user.full_name or '').lower() if i.user
            or s in (i.user.email or '').lower() if i.user
        ]
    incidents.sort(key=lambda i: i.created_at or datetime.min, reverse=True)
    return incidents


def incident_count(user_email=None, status=None):
    incidents = list_incidents(user_email=user_email)
    if status:
        incidents = [i for i in incidents if i.status == status]
    return len(incidents)


# ---------------------------------------------------------------------------
# Evidence (metadata only - files stay in the local uploads/ folder)
# ---------------------------------------------------------------------------

def _evidence_from_doc(incident_id, doc):
    d = doc.to_dict() or {}
    return Evidence(
        id=doc.id,
        incident_id=incident_id,
        file_name=d.get('file_name', ''),
        file_type=d.get('file_type', ''),
        file_size=d.get('file_size', 0),
        storage_location=d.get('storage_location', ''),
        checksum_hash=d.get('checksum_hash', ''),
        uploaded_at=d.get('uploaded_at') or datetime.utcnow(),
    )


def _list_evidence(incident_id):
    docs = _db().collection('incidents').document(incident_id).collection('evidence').stream()
    return sorted((_evidence_from_doc(incident_id, d) for d in docs), key=lambda e: e.uploaded_at or datetime.min)


def add_evidence(incident_id, file_name, file_type, file_size, storage_location, checksum_hash):
    eid = _new_id()
    ref = _db().collection('incidents').document(incident_id).collection('evidence').document(eid)
    ref.set({
        'file_name': file_name,
        'file_type': file_type,
        'file_size': file_size,
        'storage_location': storage_location,
        'checksum_hash': checksum_hash,
        'uploaded_at': datetime.utcnow(),
    })
    return eid


def get_evidence(evidence_id):
    """Find an evidence doc by its id across incidents (used by serving routes)."""
    # Evidence docs live in subcollections; scan incidents for the match.
    for inc_snap in _db().collection('incidents').stream():
        doc = inc_snap.reference.collection('evidence').document(evidence_id).get()
        if doc.exists:
            return _evidence_from_doc(inc_snap.id, doc)
    return None


def get_evidence_for_incident(incident_id, evidence_id):
    doc = _db().collection('incidents').document(incident_id).collection('evidence').document(evidence_id).get()
    if not doc.exists:
        return None
    return _evidence_from_doc(incident_id, doc)


def remove_evidence(incident_id, evidence_id):
    _db().collection('incidents').document(incident_id).collection('evidence').document(evidence_id).delete()


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------

def _submission_from_doc(incident_id, doc):
    d = doc.to_dict() or {}
    return Submission(
        id=doc.id,
        incident_id=incident_id,
        channel=d.get('channel', ''),
        attempted_at=d.get('attempted_at'),
        submitted_at=d.get('submitted_at'),
        status=d.get('status', 'prepared'),
        external_reference=d.get('external_reference'),
        error_message=d.get('error_message'),
    )


def _list_submissions(incident_id):
    docs = _db().collection('incidents').document(incident_id).collection('submissions').stream()
    return sorted((_submission_from_doc(incident_id, d) for d in docs),
                  key=lambda s: s.attempted_at or datetime.min)


def add_submission(incident_id, channel, status='prepared', **extra):
    sid = _new_id()
    data = {
        'channel': channel,
        'attempted_at': datetime.utcnow(),
        'submitted_at': extra.get('submitted_at'),
        'status': status,
        'external_reference': extra.get('external_reference'),
        'error_message': extra.get('error_message'),
    }
    _db().collection('incidents').document(incident_id).collection('submissions').document(sid).set(data)
    return sid


def update_submission(incident_id, submission_id, **fields):
    ref = _db().collection('incidents').document(incident_id).collection('submissions').document(submission_id)
    ref.set(fields, merge=True)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------

def _comment_from_doc(incident_id, doc):
    d = doc.to_dict() or {}
    c = InvestigatorComment(
        id=doc.id,
        incident_id=incident_id,
        author_email=d.get('author_email', ''),
        message=d.get('message', ''),
        created_at=d.get('created_at') or datetime.utcnow(),
    )
    c.author = _find_user(c.author_email)
    return c


def _list_comments(incident_id):
    docs = _db().collection('incidents').document(incident_id).collection('comments').stream()
    return sorted((_comment_from_doc(incident_id, d) for d in docs), key=lambda c: c.created_at or datetime.min)


def add_comment(incident_id, author_email, message):
    cid = _new_id()
    ref = _db().collection('incidents').document(incident_id).collection('comments').document(cid)
    ref.set({
        'author_email': author_email.lower(),
        'message': message,
        'created_at': datetime.utcnow(),
    })
    return cid


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def _notification_from_doc(doc):
    d = doc.to_dict() or {}
    return Notification(
        id=doc.id,
        user_email=d.get('user_email', ''),
        type=d.get('type', ''),
        title=d.get('title', ''),
        message=d.get('message', ''),
        read_status=d.get('read_status', False),
        created_at=d.get('created_at') or datetime.utcnow(),
    )


def create_notification(user_email, notif_type, title, message):
    nid = _new_id()
    _db().collection('notifications').document(nid).set({
        'user_email': user_email.lower(),
        'type': notif_type,
        'title': title,
        'message': message,
        'read_status': False,
        'created_at': datetime.utcnow(),
    })
    return nid


def list_notifications(user_email, unread_only=False):
    docs = _db().collection('notifications').stream()
    items = [_notification_from_doc(d) for d in docs if d.to_dict().get('user_email') == user_email.lower()]
    if unread_only:
        items = [n for n in items if not n.read_status]
    items.sort(key=lambda n: n.created_at or datetime.min, reverse=True)
    return items


def unread_notification_count(user_email):
    return len(list_notifications(user_email, unread_only=True))


def mark_notification_read(notification_id):
    _db().collection('notifications').document(notification_id).set({'read_status': True}, merge=True)


# ---------------------------------------------------------------------------
# Audit logs
# ---------------------------------------------------------------------------

def _audit_from_doc(doc):
    d = doc.to_dict() or {}
    log = AuditLog(
        id=doc.id,
        user_email=d.get('user_email', ''),
        action=d.get('action', ''),
        details=d.get('details', ''),
        ip_address=d.get('ip_address'),
        created_at=d.get('created_at') or datetime.utcnow(),
    )
    log.user = _find_user(log.user_email) if log.user_email else None
    return log


def log_audit(user_email, action, details='', ip_address=None):
    aid = _new_id()
    _db().collection('audit_logs').document(aid).set({
        'user_email': (user_email or '').lower(),
        'action': action,
        'details': details,
        'ip_address': ip_address,
        'created_at': datetime.utcnow(),
    })


def query_audit_logs(action='', user_email='', period='all', limit=200):
    docs = _db().collection('audit_logs').stream()
    items = [_audit_from_doc(d) for d in docs]
    if action:
        items = [a for a in items if a.action == action]
    if user_email:
        items = [a for a in items if a.user_email == user_email.lower()]
    now = datetime.utcnow()
    if period == 'today':
        items = [a for a in items if a.created_at.date() == now.date()]
    elif period == '7d':
        items = [a for a in items if (now - a.created_at).days <= 7]
    elif period == '30d':
        items = [a for a in items if (now - a.created_at).days <= 30]
    items.sort(key=lambda a: a.created_at or datetime.min, reverse=True)
    return items[:limit]


def audit_actions():
    return sorted({a.action for a in query_audit_logs(limit=10000)})


# ---------------------------------------------------------------------------
# Reporting channels
# ---------------------------------------------------------------------------

def _channel_from_doc(doc):
    d = doc.to_dict() or {}
    return ReportingChannel(
        id=doc.id,
        channel_name=d.get('channel_name', ''),
        destination=d.get('destination', ''),
        official_url=d.get('official_url'),
        active=d.get('active', True),
        last_verified=d.get('last_verified'),
    )


def list_channels(active_only=False):
    docs = _db().collection('reporting_channels').stream()
    items = [_channel_from_doc(d) for d in docs]
    if active_only:
        items = [c for c in items if c.active]
    items.sort(key=lambda c: c.channel_name)
    return items


def save_channel(channel_name, destination='', official_url='', active=True):
    cid = _slugify(channel_name)
    _db().collection('reporting_channels').document(cid).set({
        'channel_name': channel_name,
        'destination': destination,
        'official_url': official_url,
        'active': active,
        'last_verified': datetime.utcnow(),
    }, merge=True)


def toggle_channel(channel_name):
    cid = _slugify(channel_name)
    doc = _db().collection('reporting_channels').document(cid).get()
    if not doc.exists:
        return
    current = doc.to_dict().get('active', True)
    _db().collection('reporting_channels').document(cid).set({'active': not current}, merge=True)


def seed_default_channels():
    if list_channels():
        return
    defaults = [
        ('CSA Online Form', 'https://www.csaghana.org/report', 'https://www.csaghana.org/report', True),
        ('CSA Email', 'report@csa.gov.gh', None, True),
        ('CSA WhatsApp', 'https://wa.me/233501603111', 'https://wa.me/233501603111', True),
        ('CSA Call', '+233-XXX-XXXX', None, False),
    ]
    for name, dest, url, active in defaults:
        save_channel(name, dest, url, active)
