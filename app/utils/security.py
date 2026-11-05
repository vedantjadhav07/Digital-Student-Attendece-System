import secrets
import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

logger = logging.getLogger(__name__)

# Argon2id password hasher with secure modern parameters
_hasher = PasswordHasher(
    time_cost=3,        # 3 iterations
    memory_cost=65536,  # 64 MiB RAM
    parallelism=4,      # 4 threads
    hash_len=32,
    salt_len=16
)


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    if not plain_password:
        raise ValueError("Password cannot be empty")
    return _hasher.hash(plain_password)


def verify_password(stored_hash: str, candidate_password: str) -> bool:
    """Verify a candidate password against an Argon2id hash."""
    if not stored_hash or not candidate_password:
        return False
    try:
        return _hasher.verify(stored_hash, candidate_password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    except Exception as e:
        logger.error(f"Unexpected error during password verification: {e}")
        return False


def needs_rehash(stored_hash: str) -> bool:
    """Check if hash needs updating to newer parameters."""
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except Exception:
        return True


def generate_workstation_token() -> str:
    """Generate a high-entropy secret token for workstation registration."""
    return secrets.token_urlsafe(32)


def generate_session_code() -> str:
    """Generate a human-readable 6-character alphanumeric session code."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(secrets.choice(alphabet) for _ in range(6))

