"""
Secure Admin Account Creation Utility for Lab-Secure.
Allows the system administrator to create the initial root admin account securely.
Never hardcodes passwords or sensitive credentials.
"""
import getpass
import sys
from app import create_app, db
from app.models import User
from app.services.audit_service import AuditService


def create_initial_admin():
    app = create_app()
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        print("=" * 60)
        print(" LAB-SECURE: INITIAL ADMINISTRATOR PROVISIONING")
        print("=" * 60)

        username = input("Enter Admin Username / Employee ID: ").strip()
        if not username:
            print("Error: Username cannot be blank.")
            sys.exit(1)

        existing = User.query.filter_by(username=username).first()
        if existing:
            print(f"Error: User '{username}' already exists in database.")
            sys.exit(1)

        full_name = input("Enter Admin Full Name: ").strip()
        if not full_name:
            full_name = "System Administrator"

        email = input("Enter Admin Email (optional): ").strip() or None

        while True:
            password = getpass.getpass("Enter Admin Password (min 8 chars): ")
            if len(password) < 8:
                print("Password must be at least 8 characters long.")
                continue
            confirm = getpass.getpass("Confirm Admin Password: ")
            if password != confirm:
                print("Passwords do not match. Please try again.")
                continue
            break

        admin = User(
            username=username,
            full_name=full_name,
            email=email,
            role='admin',
            password=password  # Automatically hashed via Argon2id setter
        )
        db.session.add(admin)
        db.session.commit()

        AuditService.log(
            action="INITIAL_ADMIN_CREATED",
            user_id=admin.id,
            target_type="User",
            target_id=admin.id,
            details=f"Initial administrator account '{username}' provisioned via setup script."
        )

        print("-" * 60)
        print(f"Success! Administrator account '{username}' provisioned securely with Argon2id.")
        print("=" * 60)


if __name__ == '__main__':
    create_initial_admin()
