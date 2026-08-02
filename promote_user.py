"""CLI helper: promote a user to admin (or another role).

Usage:
    python promote_user.py your@email.com admin
    python promote_user.py your@email.com investigator
    python promote_user.py your@email.com user

Roles: user, investigator, admin (default: admin)

Run this once after registering the first account so someone can access
the Admin Dashboard. Only an existing admin can change roles in the UI.
"""
import sys
from app import create_app
from services import firebase_service as fb


def main():
    if len(sys.argv) < 2:
        print("Usage: python promote_user.py <email> [role]")
        print("Roles: user, investigator, admin (default: admin)")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    role = sys.argv[2].strip().lower() if len(sys.argv) > 2 else 'admin'
    if role not in ('user', 'investigator', 'admin'):
        print(f"Invalid role '{role}'. Use user, investigator or admin.")
        sys.exit(1)

    create_app()  # Initializes Firebase
    user = fb.get_user(email)
    if not user:
        print(f"No user found with email '{email}'. Register the account first.")
        sys.exit(1)
    user.role = role
    fb.save_user(user)
    print(f"OK: '{email}' is now a {role}.")


if __name__ == '__main__':
    main()
