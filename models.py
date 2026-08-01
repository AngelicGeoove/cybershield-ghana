"""Lightweight data models backed by Firestore (via services.firebase_service).

These classes carry the same attribute names the templates expect so the
Jinja2 layer is largely unchanged. They are plain Python objects -- all
persistence lives in services/firebase_service.py.
"""
from datetime import datetime
from flask_login import UserMixin
import bcrypt


class _Rel(list):
    """A list that mimics the small slice of the SQLAlchemy relationship API
    used by the templates (.all / .first / .count / .filter_by)."""

    def all(self):
        return self

    def first(self):
        return self[0] if self else None

    def count(self):
        return len(self)

    def filter_by(self, **kw):
        return _Rel(
            o for o in self
            if all(getattr(o, k, None) == v for k, v in kw.items())
        )


class User(UserMixin):
    def __init__(self, **kw):
        # 'id' is the legacy SQLite int id (None for accounts created after migration)
        self.id = kw.get('id')
        self.email = (kw.get('email') or '').lower()
        self.full_name = kw.get('full_name', '')
        self.phone = kw.get('phone', '')
        self.organisation = kw.get('organisation', '')
        self.location = kw.get('location', '')
        self.age = kw.get('age')
        self.role = kw.get('role', 'user')
        self.email_verified = kw.get('email_verified', False)
        self.account_status = kw.get('account_status', 'active')
        self.password_hash = kw.get('password_hash', '')
        self.auth_uid = kw.get('auth_uid')
        self.created_at = kw.get('created_at') or datetime.utcnow()
        self.updated_at = kw.get('updated_at') or datetime.utcnow()
        self.notifications = _Rel()
        self.incidents = _Rel()
        self.assigned_incidents = _Rel()

    def get_id(self):
        """Flask-Login: the user's stable identifier is their email."""
        return self.email

    @property
    def role_label(self):
        return {'user': 'User', 'investigator': 'Investigator', 'admin': 'Admin'}.get(self.role, 'User')

    def is_admin(self):
        return self.role == 'admin'

    def is_investigator(self):
        return self.role in ('investigator', 'admin')

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        if not self.password_hash:
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
        except (ValueError, TypeError):
            return False


class Incident:
    def __init__(self, **kw):
        self.id = kw.get('id')
        self.incident_id = kw.get('incident_id', '')
        self.user_id = kw.get('user_id')
        self.user_email = (kw.get('user_email') or '').lower()
        self.assigned_investigator_id = kw.get('assigned_investigator_id')
        self.assigned_investigator_email = (kw.get('assigned_investigator_email') or '').lower() or None
        self.category = kw.get('category', '')
        self.incident_date = kw.get('incident_date')
        self.incident_time = kw.get('incident_time', '')
        self.platform = kw.get('platform', '')
        self.description = kw.get('description', '')
        self.message = kw.get('message', '')
        self.additional_information = kw.get('additional_information', '')
        self.status = kw.get('status', 'draft')
        self.created_at = kw.get('created_at') or datetime.utcnow()
        self.updated_at = kw.get('updated_at') or datetime.utcnow()
        self.user = kw.get('user')
        self.assigned_investigator = kw.get('assigned_investigator')
        self.evidence = _Rel()
        self.submissions = _Rel()
        self.comments = _Rel()
        self.versions = _Rel()


class Evidence:
    def __init__(self, **kw):
        self.id = kw.get('id', '')
        self.incident_id = kw.get('incident_id', '')
        self.file_name = kw.get('file_name', '')
        self.file_type = kw.get('file_type', '')
        self.file_size = kw.get('file_size', 0)
        self.storage_location = kw.get('storage_location', '')
        self.checksum_hash = kw.get('checksum_hash', '')
        self.uploaded_at = kw.get('uploaded_at') or datetime.utcnow()


class Submission:
    def __init__(self, **kw):
        self.id = kw.get('id', '')
        self.incident_id = kw.get('incident_id', '')
        self.channel = kw.get('channel', '')
        self.attempted_at = kw.get('attempted_at')
        self.submitted_at = kw.get('submitted_at')
        self.status = kw.get('status', 'prepared')
        self.external_reference = kw.get('external_reference')
        self.error_message = kw.get('error_message')


class Notification:
    def __init__(self, **kw):
        self.id = kw.get('id', '')
        self.user_email = (kw.get('user_email') or '').lower()
        self.type = kw.get('type', '')
        self.title = kw.get('title', '')
        self.message = kw.get('message', '')
        self.read_status = kw.get('read_status', False)
        self.created_at = kw.get('created_at') or datetime.utcnow()


class AuditLog:
    def __init__(self, **kw):
        self.id = kw.get('id', '')
        self.user_email = (kw.get('user_email') or '').lower()
        self.action = kw.get('action', '')
        self.details = kw.get('details', '')
        self.ip_address = kw.get('ip_address')
        self.created_at = kw.get('created_at') or datetime.utcnow()
        self.user = kw.get('user')


class ReportingChannel:
    def __init__(self, **kw):
        self.id = kw.get('id', '')
        self.channel_name = kw.get('channel_name', '')
        self.destination = kw.get('destination', '')
        self.official_url = kw.get('official_url')
        self.active = kw.get('active', True)
        self.last_verified = kw.get('last_verified')


class InvestigatorComment:
    def __init__(self, **kw):
        self.id = kw.get('id', '')
        self.incident_id = kw.get('incident_id', '')
        self.author_email = (kw.get('author_email') or '').lower()
        self.author = kw.get('author')
        self.message = kw.get('message', '')
        self.created_at = kw.get('created_at') or datetime.utcnow()


class IncidentVersion:
    def __init__(self, **kw):
        self.id = kw.get('id', '')
        self.incident_id = kw.get('incident_id', '')
        self.version_number = kw.get('version_number', 1)
        self.changed_fields = kw.get('changed_fields', '')
        self.reason = kw.get('reason', '')
        self.created_at = kw.get('created_at') or datetime.utcnow()


class Setting:
    def __init__(self, **kw):
        self.id = kw.get('id', '')
        self.key = kw.get('key', '')
        self.value = kw.get('value', '')
        self.description = kw.get('description', '')