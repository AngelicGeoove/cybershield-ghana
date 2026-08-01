"""One-time migration: import the old local SQLite database into Firestore.

Usage:
    python migrate_sqlite_to_firestore.py [path/to/cybershield.db]

Run this once after switching to the online (Firestore) version. Existing
accounts keep working: the bcrypt password hashes are stored in the user
documents, and login self-heals by creating the Firebase Auth account on
first successful sign-in.

After a successful migration the SQLite file is no longer used.
"""
import os
import sys
import sqlite3
import json
from datetime import datetime

from app import create_app
from models import User
from services import firebase_service as fb


def parse_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def main():
    db_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join('instance', 'cybershield.db')
    if not os.path.exists(db_path):
        print(f'No SQLite database found at {db_path}. Nothing to migrate.')
        return

    create_app()  # initializes Firebase
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    print(f'Migrating from {db_path} ...')

    # ---- Users ----
    migrated_users = 0
    for row in conn.execute('SELECT * FROM users').fetchall():
        email = (row['email'] or '').lower()
        if not email:
            continue
        if fb.get_user(email):
            continue  # already present in Firestore
        u = User(
            id=row['id'],
            email=email,
            full_name=row['full_name'],
            phone=row['phone'] or '',
            organisation=row['organisation'] or '',
            location=row['location'] or '',
            age=row['age'],
            role=row['role'] or 'user',
            email_verified=bool(row['email_verified']),
            account_status=row['account_status'] or 'active',
            created_at=parse_dt(row['created_at']) or datetime.utcnow(),
            updated_at=parse_dt(row['updated_at']) or datetime.utcnow(),
        )
        u.password_hash = row['password_hash'] or ''
        fb.save_user(u)
        migrated_users += 1
    print(f'Users migrated: {migrated_users}')

    # ---- Incidents (with evidence / submissions / comments) ----
    legacy_to_uuid = {}
    migrated_incidents = 0
    for row in conn.execute('SELECT * FROM incidents').fetchall():
        incident_id = row['incident_id']
        if not incident_id:
            continue
        if fb.get_incident(incident_id):
            continue
        # Resolve reporter email from legacy user_id
        user_row = conn.execute('SELECT email FROM users WHERE id = ?', (row['user_id'],)).fetchone()
        user_email = (user_row['email'] if user_row else '').lower()
        if not user_email:
            continue
        legacy_to_uuid[row['id']] = incident_id

        inc = fb.create_incident(
            user_email,
            incident_id=incident_id,
            category=row['category'] or '',
            incident_date=row['incident_date'] or None,
            incident_time=row['incident_time'] or '',
            platform=row['platform'] or '',
            description=row['description'] or '',
            message=row['message'] or '',
            additional_information=row['additional_information'] or '',
            status=row['status'] or 'draft',
            created_at=parse_dt(row['created_at']) or datetime.utcnow(),
            updated_at=parse_dt(row['updated_at']) or datetime.utcnow(),
        )
        # Assign investigator by legacy id if present
        if row['assigned_investigator_id']:
            inv = conn.execute('SELECT email FROM users WHERE id = ?', (row['assigned_investigator_id'],)).fetchone()
            if inv:
                fb.assign_investigator(incident_id, inv['email'].lower())

        # Evidence
        for ev in conn.execute('SELECT * FROM evidence WHERE incident_id = ?', (row['id'],)).fetchall():
            fb.add_evidence(
                incident_id,
                file_name=ev['file_name'] or '',
                file_type=ev['file_type'] or '',
                file_size=ev['file_size'] or 0,
                storage_location=ev['storage_location'] or '',
                checksum_hash=ev['checksum_hash'] or '',
            )

        # Submissions
        for sub in conn.execute('SELECT * FROM submissions WHERE incident_id = ?', (row['id'],)).fetchall():
            fb.add_submission(
                incident_id,
                channel=sub['channel'] or '',
                status=sub['status'] or 'prepared',
                submitted_at=parse_dt(sub['submitted_at']),
                external_reference=sub['external_reference'],
                error_message=sub['error_message'],
            )

        # Comments
        for cm in conn.execute('SELECT * FROM investigator_comments WHERE incident_id = ?', (row['id'],)).fetchall():
            author = conn.execute('SELECT email FROM users WHERE id = ?', (cm['author_id'],)).fetchone()
            if author:
                fb.add_comment(incident_id, author['email'].lower(), cm['message'] or '')

        migrated_incidents += 1
    print(f'Incidents migrated: {migrated_incidents}')

    # ---- Notifications ----
    migrated_notifs = 0
    for row in conn.execute('SELECT * FROM notifications').fetchall():
        user_row = conn.execute('SELECT email FROM users WHERE id = ?', (row['user_id'],)).fetchone()
        if not user_row:
            continue
        fb.create_notification(user_row['email'].lower(), row['type'], row['title'], row['message'] or '')
        migrated_notifs += 1
    print(f'Notifications migrated: {migrated_notifs}')

    # ---- Reporting channels (only if Firestore has none) ----
    if not fb.list_channels():
        fb.seed_default_channels()
        print('Default reporting channels seeded.')

    conn.close()
    print('\nMigration complete. You can now delete the old SQLite file.')


if __name__ == '__main__':
    main()
