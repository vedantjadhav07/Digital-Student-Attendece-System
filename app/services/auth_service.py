from datetime import datetime
from sqlalchemy import func
from app.extensions import db
from app.models import User
from app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    def authenticate_user(username: str, password: str, client_ip: str = None):
        """
        Authenticate a user by username and password.
        Case-insensitive username lookup for user convenience.
        Returns (user, None) on success or (None, error_message) on failure.
        """
        if not username or not password:
            return None, "Username and password are required."

        cleaned_username = username.strip()
        user = User.query.filter(func.lower(User.username) == cleaned_username.lower()).first()
        if not user:
            AuditService.log(
                action="LOGIN_FAILED",
                details=f"Unknown username: {username}",
                ip_address=client_ip
            )
            return None, "Invalid username or password."

        if not user.is_active:
            AuditService.log(
                action="LOGIN_BLOCKED",
                user_id=user.id,
                details=f"Inactive account: {username}",
                ip_address=client_ip
            )
            return None, "This account has been deactivated. Please contact administrator."

        if not user.verify_password(password):
            AuditService.log(
                action="LOGIN_FAILED",
                user_id=user.id,
                details=f"Incorrect password for user: {username}",
                ip_address=client_ip
            )
            return None, "Invalid username or password."

        # Successful authentication
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        AuditService.log(
            action="LOGIN_SUCCESS",
            user_id=user.id,
            target_type="User",
            target_id=user.id,
            details=f"User {username} logged in as {user.role}",
            ip_address=client_ip
        )
        return user, None

    @staticmethod
    def change_password(user: User, new_password: str, changed_by_user_id: int = None, client_ip: str = None):
        """Update a user's password securely with Argon2id."""
        if not new_password or len(new_password) < 6:
            return False, "Password must be at least 6 characters long."

        user.password = new_password
        db.session.commit()

        AuditService.log(
            action="PASSWORD_CHANGED",
            user_id=changed_by_user_id or user.id,
            target_type="User",
            target_id=user.id,
            details=f"Password updated for user {user.username}",
            ip_address=client_ip
        )
        return True, "Password updated successfully."

