import hashlib
from datetime import datetime, timedelta, timezone
from flask import current_app
import jwt
from app.extensions import db
from app.models import User

ACCESS_TOKEN_EXPIRES_DAYS = 2
REFRESH_TOKEN_EXPIRES_DAYS = 7


def _get_signing_key():
    secret = current_app.config.get('SECRET_KEY', 'labora-default-secret-key-attendance-system')
    if isinstance(secret, str):
        secret = secret.encode('utf-8')
    return hashlib.sha256(secret).digest()


def create_access_token(user, expires_days=ACCESS_TOKEN_EXPIRES_DAYS):
    """Generate a JWT access token valid for 2 days by default."""
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user.id),
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'type': 'access',
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(days=expires_days)).timestamp())
    }
    return jwt.encode(payload, _get_signing_key(), algorithm='HS256')


def create_refresh_token(user, expires_days=REFRESH_TOKEN_EXPIRES_DAYS):
    """Generate a JWT refresh token valid for 7 days by default."""
    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user.id),
        'user_id': user.id,
        'username': user.username,
        'type': 'refresh',
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(days=expires_days)).timestamp())
    }
    return jwt.encode(payload, _get_signing_key(), algorithm='HS256')


def decode_jwt_token(token_str, expected_type='access'):
    """Decodes and validates a JWT token string."""
    if not token_str:
        return None
    try:
        payload = jwt.decode(token_str, _get_signing_key(), algorithms=['HS256'])
        if expected_type and payload.get('type') != expected_type:
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_user_from_jwt(token_str, expected_type='access'):
    """Decodes JWT and retrieves active User from database."""
    payload = decode_jwt_token(token_str, expected_type=expected_type)
    if not payload:
        return None
    user_id = payload.get('user_id') or payload.get('sub')
    if not user_id:
        return None
    user = db.session.get(User, int(user_id))
    if user and user.is_active:
        return user
    return None
