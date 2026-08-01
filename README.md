# CyberShield Ghana

Cybercrime and Cybersecurity Incident Reporting Application

This is an independent application designed to facilitate reporting to the Cyber Security Authority (CSA) of Ghana. It is NOT an official CSA application.

## Quick Start

### Option 1 - Run the Executable (Recommended):
1. Double-click CyberShieldGhana.exe or run run_exe.bat
2. Place `firebase-adminsdk.json` (service account key) next to the exe
3. The application will start and open a web browser automatically
4. Navigate to http://localhost:5000

### Option 2 - Run as Python Application:
1. Create a virtual environment: `python -m venv .venv`
2. Install dependencies: `.venv\Scripts\pip install -r requirements.txt`
3. Place `firebase-adminsdk.json` in the project folder
4. Run: `run.bat` (or `.venv\Scripts\python app.py`)
5. Open http://127.0.0.1:5000

> **Note:** the app is fully online and uses Firebase (Authentication, Cloud
> Firestore) as its single data store. An internet connection is required and
> the `firebase-adminsdk.json` service account key must be present.

## Features
- User registration and secure login (Firebase Authentication)
- Multi-step cyber incident reporting wizard
- Local evidence upload (images, PDFs, documents, max 10MB) - metadata stored in Firestore
- Multiple submission channels: CSA Online Form, Email, WhatsApp
- Personal Cyber Log for tracking all reports
- Report status tracking (Submitted, Under Investigation, Evidence Requested, Resolved)
- Investigator console: assign cases, update status, message reporters
- PDF export of reports
- Cybersecurity awareness section (Stay Safe)
- Responsive cybersecurity-themed UI
- Audit trail and notifications
- Reporting channel configuration
- Profile management and data export

## Security Notes
- Passwords are hashed with bcrypt
- All data is encrypted in transit (HTTPS)
- Files are validated and scanned
- No sensitive data stored in reports

## Requirements
Python 3.11+ with the following packages:
```
pip install Flask Flask-Login Flask-SQLAlchemy Flask-WTF email-validator bcrypt reportlab
```

## Project Structure
```
CyberShieldGhana/
├── app.py                  # Main application entry point
├── config.py               # Configuration settings
├── extensions.py           # Flask extensions (db, login, csrf)
├── models.py               # Database models
├── requirements.txt        # Python dependencies
├── routes/                 # Route blueprints
│   ├── auth.py             # Authentication routes
│   ├── dashboard.py        # Dashboard routes
│   ├── report.py           # Report wizard routes
│   ├── cyberlog.py         # Cyber Log routes
│   ├── channels.py         # Reporting channels routes
│   ├── awareness.py        # Cybersecurity awareness routes
│   ├── profile.py          # Profile management routes
│   ├── settings.py         # Settings routes
│   └── admin.py            # Admin dashboard routes
├── services/               # Business logic services
│   ├── submission_service.py   # Report submission logic
│   └── export_service.py       # PDF export logic
├── templates/              # HTML templates (Jinja2)
├── static/                 # CSS and JavaScript files
│   ├── css/style.css
│   └── js/main.js
└── uploads/                # Uploaded evidence files
```

## Important Notice
This is an independent application. The Cyber Security Authority (CSA) of Ghana is an external authority. This application is responsible for collecting, structuring, and facilitating report submissions. It does not investigate incidents, determine guilt, or guarantee outcomes.