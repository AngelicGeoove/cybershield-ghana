# CyberShield Ghana - Server-Side Documentation

## Overview
CyberShield Ghana is a Flask-based desktop application (packaged with PyInstaller) that runs a local web server for reporting cybersecurity incidents to the Cyber Security Authority (CSA) of Ghana. The application provides a guided multi-step wizard for users to create detailed incident reports and submit them through official CSA channels.

## Architecture

### Technology Stack
- **Framework**: Flask 2.x
- **Database**: SQLite (SQLAlchemy ORM)
- **Authentication**: Flask-Login with bcrypt password hashing
- **CSRF Protection**: Flask-WTF CSRF
- **Packaging**: PyInstaller (creates standalone .exe)
- **Frontend**: Server-rendered templates (Jinja2) with Bootstrap 5

### Application Structure
```
Final Year Project/
├── app.py                 # Application factory & entry point
├── config.py              # Configuration management
├── models.py              # Database models
├── extensions.py          # Flask extensions initialization
├── routes/                # Blueprint route modules
│   ├── __init__.py        # Route registration
│   ├── auth.py            # Authentication routes
│   ├── report.py          # Incident reporting wizard
│   ├── channels.py        # Channel information
│   ├── dashboard.py       # User dashboard
│   ├── profile.py         # User profile
│   ├── settings.py        # Application settings
│   ├── admin.py           # Admin panel
│   ├── awareness.py       # Cyber awareness content
│   └── cyberlog.py        # Activity logging
├── services/              # Business logic services
│   ├── __init__.py
│   ├── submission_service.py  # Channel submission logic
│   └── export_service.py      # Data export functionality
├── templates/             # Jinja2 templates
├── static/                # Static assets (CSS, JS, images)
├── instance/              # Database file location (created at runtime)
├── uploads/               # Evidence file storage
└── requirements.txt       # Python dependencies
```

## Server Initialization (`app.py`)

### Application Factory Pattern
The app uses a factory pattern (`create_app()`) for initialization:

```python
def create_app():
    template_dir = resource_path('templates')
    static_dir = resource_path('static')
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(Config)
    
    # Override database URI with absolute path for PyInstaller
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_uri()
    
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    
    register_routes(app)
    
    with app.app_context():
        db.create_all()
        seed_reporting_channels()
    
    return app
```

### Key Initialization Steps
1. **Resource Path Resolution**: Handles both script mode and PyInstaller bundle mode via `resource_path()` and `get_database_uri()`
2. **Database Configuration**: SQLite database stored in `instance/cybershield.db` (absolute path resolved at runtime)
3. **Extension Initialization**: SQLAlchemy, Flask-Login, CSRF protection
4. **Route Registration**: All blueprints registered via `register_routes()`
5. **Database Creation**: Tables created on startup
6. **Default Data Seeding**: Pre-populates reporting channels (CSA Online Form, Email, WhatsApp, Call)

### Running the Server
```python
if __name__ == '__main__':
    app = create_app()
    Timer(1.5, open_browser).start()  # Auto-opens browser
    app.run(debug=True, host='0.0.0.0', port=5000)
```

## Database Models (`models.py`)

### User Account Storage
**Table: `users`**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `full_name` | String(120) | Not Null | User's full name |
| `email` | String(120) | Unique, Not Null | Login email |
| `phone` | String(20) | | Phone number |
| `organisation` | String(120) | | Organisation name |
| `location` | String(120) | | User location |
| `age` | Integer | | User age |
| `password_hash` | String(255) | Not Null | Bcrypt hashed password |
| `email_verified` | Boolean | Default False | Email verification status |
| `account_status` | String(20) | Default 'active' | Account status |
| `created_at` | DateTime | Default UTC now | Account creation timestamp |
| `updated_at` | DateTime | Auto-update | Last update timestamp |

**Password Security**: Passwords are hashed using bcrypt with salt via `set_password()` and verified with `check_password()`.

**Relationships**:
- `incidents`: One-to-many with Incident (cascade delete)
- `notifications`: One-to-many with Notification (cascade delete)

### Incident Reports
**Table: `incidents`**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `incident_id` | String(36) | Unique, Not Null | UUID for external reference |
| `user_id` | Integer | FK, Not Null | References users.id |
| `category` | String(100) | Not Null | Incident category |
| `incident_date` | Date | | Date of incident |
| `incident_time` | String(20) | | Time of incident |
| `platform` | String(100) | | Platform involved |
| `description` | Text | | Main incident description |
| `message` | Text | | Alias for description |
| `additional_information` | Text | | JSON metadata |
| `status` | String(30) | Default 'draft' | draft/prepared/sent/failed |
| `created_at` | DateTime | Default UTC now | Creation timestamp |
| `updated_at` | DateTime | Auto-update | Last update timestamp |

**Relationships**:
- `evidence`: One-to-many with Evidence (cascade delete)
- `submissions`: One-to-many with Submission (cascade delete)
- `versions`: One-to-many with IncidentVersion (cascade delete)

### Evidence Files
**Table: `evidence`**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `incident_id` | Integer | FK, Not Null | References incidents.id |
| `file_name` | String(255) | Not Null | Original filename |
| `file_type` | String(50) | | File extension |
| `file_size` | Integer | | Size in bytes |
| `storage_location` | String(255) | | Absolute file path |
| `uploaded_at` | DateTime | Default UTC now | Upload timestamp |
| `checksum_hash` | String(64) | | SHA-256 hash for integrity |

**Storage**: Files saved to `uploads/` directory with UUID-prefixed names.

### Submissions
**Table: `submissions`**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `incident_id` | Integer | FK, Not Null | References incidents.id |
| `channel` | String(50) | Not Null | Channel used (email/whatsapp/csa-online-form) |
| `attempted_at` | DateTime | Default UTC now | Attempt timestamp |
| `submitted_at` | DateTime | | Success timestamp |
| `status` | String(30) | Default 'prepared' | prepared/sent/failed |
| `external_reference` | String(255) | | External tracking ID |
| `error_message` | Text | | Error details if failed |

### Notifications
**Table: `notifications`**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `user_id` | Integer | FK, Not Null | References users.id |
| `type` | String(50) | Not Null | Notification type |
| `title` | String(200) | Not Null | Notification title |
| `message` | Text | | Notification body |
| `read_status` | Boolean | Default False | Read/unread status |
| `created_at` | DateTime | Default UTC now | Creation timestamp |

### Reporting Channels
**Table: `reporting_channels`**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | PK | Primary key |
| `channel_name` | String(100) | Not Null | Display name |
| `destination` | String(255) | | Contact destination (email/phone/URL) |
| `official_url` | String(500) | | Official website URL |
| `active` | Boolean | Default True | Channel availability |
| `last_verified` | DateTime | | Last verification date |

**Default Channels** (seeded on first run):
1. **CSA Online Form** - `https://www.csaghana.org/report`
2. **CSA Email** - `report@csa.gov.gh`
3. **CSA WhatsApp** - `https://wa.me/233501603111`
4. **CSA Call** - `+233-XXX-XXXX` (inactive by default)

### Other Models
- **AuditLog**: Tracks user actions for security auditing
- **IncidentVersion**: Version history for incident edits
- **Setting**: Key-value application settings

## Configuration (`config.py`)

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///' + get_database_path())
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'csv', 'zip'}
```

### Database Path Resolution
- **Script Mode**: `<project_root>/cybershield.db`
- **PyInstaller Mode**: `<exe_directory>/cybershield.db`
- **Instance Folder**: Actually created at `instance/cybershield.db` via `get_database_uri()` in app.py

## Reporting Workflow (`routes/report.py`)

### Multi-Step Wizard (6 Steps)
1. **Step 1**: Reporter Information (pre-filled from user profile)
2. **Step 2**: Incident Category Selection
3. **Step 3**: Description (Guided or Free-text)
4. **Step 4**: Metadata (Date, Time, Platform, Technical Details)
5. **Step 5**: Evidence Upload
6. **Step 6**: Channel Selection (CSA Online Form / Email / WhatsApp)

### Session-Based Draft Storage
- Draft data stored in Flask session: `session['draft_report']`
- Persists across steps until submission or manual save
- Cleared after successful submission

### Submission Process (`submit_report`)
1. Creates `Incident` record with all collected data
2. Associates uploaded `Evidence` records
3. Creates `Submission` record with selected channel
4. Calls `submission_service.submit_to_channel()` to open external channel
5. Updates submission/incident status based on result
6. Creates notification for user
7. Clears draft session
8. Redirects to confirmation page

## Channel Submission Service (`services/submission_service.py`)

### Report Content Preparation
`prepare_report_content(data)` generates a formatted text report including:
- Reporter details (name, organisation, email, phone, location, age)
- Incident details (category, date, time, platform, description)
- All additional metadata fields

### Channel Handlers

#### 1. CSA Online Form (`csa-online-form`)
- Opens `https://www.csaghana.org/report` in browser
- **Note**: Form may not support URL prefill; user must copy/paste content
- Returns status: `sent` with instruction message

#### 2. Email (`email`)
- Opens default mail client via `mailto:` link
- **Subject**: `Cyber Incident Report - {incident_id}`
- **Body**: Full formatted report content (truncated to ~3500 chars for URL limits)
- **To**: `report@csa.gov.gh`
- Returns status: `sent`

#### 3. WhatsApp (`whatsapp`)
- Opens WhatsApp Web/app via `https://wa.me/233501603111?text=...`
- **Message**: Full formatted report content with incident ID (truncated to ~3500 chars)
- Returns status: `sent`

#### 4. Unknown Channel
- Returns status: `prepared` with error message

### URL Length Protection
- `_truncate_for_url(text, max_chars=3500)` prevents exceeding browser/URL limits
- Truncation notice appended if content exceeds limit

## Authentication (`routes/auth.py`)

### Routes
- `GET/POST /login` - User login with email/password
- `GET /logout` - Logout and clear session
- `GET/POST /register` - New user registration
- `GET /verify-email/<token>` - Email verification (if implemented)

### Password Handling
- Registration: `user.set_password(password)` → bcrypt hash
- Login: `user.check_password(password)` → bcrypt verify
- Session management via Flask-Login

## File Storage

### Upload Directory
- Configured in `Config.UPLOAD_FOLDER`: `<project_root>/uploads/`
- Created automatically on first upload
- Files saved with UUID prefix: `{uuid}_{original_filename}`

### Evidence Integrity
- SHA-256 checksum calculated on upload
- Stored in `Evidence.checksum_hash`
- Enables tamper detection

## Admin Features (`routes/admin.py`)

### Channel Management
- View all reporting channels
- Activate/deactivate channels
- Update channel details (destination, official_url)
- Verification tracking

### User Management
- View all registered users
- Account status management

## Data Export (`services/export_service.py`)

Provides functionality to export incident data in various formats for backup or analysis.

## Security Considerations

1. **CSRF Protection**: Enabled globally via Flask-WTF CSRF
2. **Password Hashing**: bcrypt with automatic salt generation
3. **SQL Injection Prevention**: SQLAlchemy ORM parameterized queries
4. **File Upload Validation**: Extension allowlist, size limits (10MB per file)
5. **Session Security**: Secure session cookies in production
6. **Input Sanitization**: Jinja2 auto-escaping in templates

## Deployment Notes

### PyInstaller Packaging
- Entry point: `app.py`
- Spec file: `CyberShieldGhana.spec`
- Includes: templates, static, uploads, instance folders
- Database: Copied to executable directory on first run

### Database Location
- **Development**: `Final Year Project/instance/cybershield.db`
- **Packaged**: `<exe_folder>/instance/cybershield.db`

### Required Directories (Auto-created)
- `instance/` - Database
- `uploads/` - Evidence files
- `logs/` - Application logs (flask.log)

## API Endpoints Summary

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Home page | No |
| GET/POST | `/login` | User login | No |
| GET | `/logout` | User logout | Yes |
| GET/POST | `/register` | User registration | No |
| GET | `/report` | Start report wizard | Yes |
| GET/POST | `/report/step/<1-6>` | Wizard steps | Yes |
| GET | `/report/review` | Review draft | Yes |
| POST | `/report/submit` | Submit report | Yes |
| POST | `/report/save-draft` | Save draft (AJAX) | Yes |
| POST | `/report/upload-evidence` | Upload evidence | Yes |
| GET | `/dashboard` | User dashboard | Yes |
| GET | `/profile` | User profile | Yes |
| GET | `/channels` | View channels | Yes |
| GET | `/settings` | App settings | Yes |
| GET | `/admin/*` | Admin panel | Yes (admin) |

## Troubleshooting

### Common Issues
1. **Database not found**: Ensure `instance/` directory exists and is writable
2. **Upload failures**: Check `uploads/` directory permissions
3. **Channel not opening**: Verify default browser is set; check URL length limits
4. **PyInstaller paths**: Use `resource_path()` and `get_database_uri()` for all file references

### Logs
- Application logs: `flask.log` in project root
- Console output shows debug info during development