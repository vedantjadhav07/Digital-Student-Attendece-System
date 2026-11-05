import pytest
from app.utils.security import hash_password, verify_password
from app.services.auth_service import AuthService
from app.models import User


def test_argon2id_password_hashing():
    raw = "MySuperSecretKey!2026"
    pwd_hash = hash_password(raw)

    assert pwd_hash.startswith("$argon2")
    assert verify_password(pwd_hash, raw) is True
    assert verify_password(pwd_hash, "WrongPassword") is False
    assert verify_password(pwd_hash, "") is False


def test_user_password_property_write_only(db):
    user = User(username="test_prop", full_name="Test", role="student", password="ValidPassword123")
    db.session.add(user)
    db.session.commit()

    with pytest.raises(AttributeError):
        _ = user.password

    assert user.verify_password("ValidPassword123") is True
    assert user.verify_password("IncorrectPassword") is False


def test_auth_service_success(db, test_student):
    user, err = AuthService.authenticate_user(test_student.username, "StudentTestPassword!123", "127.0.0.1")
    assert err is None
    assert user is not None
    assert user.username == test_student.username
    assert user.last_login_at is not None


def test_auth_service_invalid_credentials(db, test_student):
    user, err = AuthService.authenticate_user(test_student.username, "WrongPassword", "127.0.0.1")
    assert user is None
    assert "Invalid username or password" in err


def test_auth_service_inactive_user(db, test_student):
    test_student.is_active = False
    db.session.commit()

    user, err = AuthService.authenticate_user(test_student.username, "StudentTestPassword!123", "127.0.0.1")
    assert user is None
    assert "deactivated" in err.lower()


def test_login_and_logout_routes(client, test_student):
    # GET login
    res = client.get('/login')
    assert res.status_code == 200
    assert b"Institutional" in res.data or b"Sign In" in res.data

    # POST valid login
    res = client.post('/login', data={
        'username': test_student.username,
        'password': 'StudentTestPassword!123'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Student Attendance Portal" in res.data or b"Welcome back" in res.data

    # GET logout
    res = client.get('/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b"signed out safely" in res.data or b"Sign In" in res.data

