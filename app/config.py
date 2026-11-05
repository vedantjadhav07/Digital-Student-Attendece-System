import os
from pathlib import Path
from dotenv import load_dotenv

# Load root .env
basedir = Path(__file__).resolve().parent.parent
load_dotenv(basedir / '.env')


class Config:
    """Base application configuration."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-insecure-dev-key-change-in-production')
    
    # Instance directory for SQLite
    INSTANCE_DIR = basedir / 'instance'
    INSTANCE_DIR.mkdir(exist_ok=True)
    
    # Database
    db_env_url = os.getenv('DATABASE_URL', 'sqlite:///attendance.db')
    if db_env_url.startswith('sqlite:///'):
        db_filename = db_env_url.replace('sqlite:///', '')
        db_path = INSTANCE_DIR / db_filename
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path.as_posix()}"
    else:
        SQLALCHEMY_DATABASE_URI = db_env_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLite Engine Configuration (WAL mode, foreign keys, busy timeout)
    SQLITE_TIMEOUT = int(os.getenv('SQLITE_TIMEOUT', '15'))
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {
            'timeout': SQLITE_TIMEOUT,
            'check_same_thread': False,
        }
    }

    # Security Cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

    # Proxy Handling
    BEHIND_PROXY = os.getenv('BEHIND_PROXY', 'False').lower() in ('true', '1')

    # Rate Limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200/day;50/hour')
    RATELIMIT_STORAGE_URI = "memory://"

    # Lab Attendance Default Parameters
    DEFAULT_SESSION_DURATION_MINUTES = 10
    ATTENDANCE_AT_RISK_THRESHOLD = 75.0  # percentage


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}

