import logging
from flask import request
from app.extensions import db
from app.models import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    @staticmethod
    def log(action: str, user_id=None, target_type=None, target_id=None, ip_address=None, details=None):
        """Record an event to the audit log."""
        try:
            if not ip_address and request:
                ip_address = request.remote_addr

            log_entry = AuditLog(
                user_id=user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                ip_address=ip_address,
                details=str(details) if details else None
            )
            db.session.add(log_entry)
            db.session.commit()
            return log_entry
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to write audit log: {e}")
            return None

