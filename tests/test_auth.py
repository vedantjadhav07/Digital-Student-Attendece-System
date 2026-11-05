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


def test_jwt_lifecycle_and_session_refresh(client, test_student):
    # 1. API Login returns 2-day access token and 7-day refresh token
    login_res = client.post('/api/auth/login', json={
        'username': test_student.username,
        'password': 'StudentTestPassword!123'
    })
    assert login_res.status_code == 200
    login_data = login_res.get_json()
    assert login_data['success'] is True
    access_token = login_data['access_token']
    refresh_token = login_data['refresh_token']
    assert access_token is not None
    assert refresh_token is not None

    # Verify expiration windows (2 days = ~172800s, 7 days = ~604800s)
    from app.utils.jwt_util import decode_jwt_token
    access_payload = decode_jwt_token(access_token, expected_type='access')
    refresh_payload = decode_jwt_token(refresh_token, expected_type='refresh')
    assert access_payload is not None
    assert refresh_payload is not None
    assert access_payload['user_id'] == test_student.id
    assert refresh_payload['user_id'] == test_student.id

    access_duration = access_payload['exp'] - access_payload['iat']
    refresh_duration = refresh_payload['exp'] - refresh_payload['iat']
    assert access_duration == 2 * 24 * 3600
    assert refresh_duration == 7 * 24 * 3600

    # 2. Access protected endpoint using Bearer Token (logout session first)
    client.get('/api/auth/logout')
    headers = {'Authorization': f'Bearer {access_token}'}
    me_res = client.get('/api/auth/me', headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.get_json()
    assert me_data['authenticated'] is True
    assert me_data['user']['username'] == test_student.username

    # 3. Refresh Access Token using 7-day refresh token
    refresh_res = client.post('/api/auth/refresh', json={'refresh_token': refresh_token})
    assert refresh_res.status_code == 200
    ref_data = refresh_res.get_json()
    assert ref_data['success'] is True
    new_access_token = ref_data['access_token']
    assert new_access_token is not None

    # 4. Use new access token
    headers_new = {'Authorization': f'Bearer {new_access_token}'}
    me_res_new = client.get('/api/auth/me', headers=headers_new)
    assert me_res_new.status_code == 200
    assert me_res_new.get_json()['authenticated'] is True

    # 5. Invalid / expired token rejection
    client.get('/api/auth/logout')
    bad_headers = {'Authorization': 'Bearer invalid.token.payload'}
    me_bad = client.get('/api/auth/me', headers=bad_headers)
    assert me_bad.get_json()['authenticated'] is False

