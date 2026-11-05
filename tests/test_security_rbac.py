def test_unauthenticated_access_redirects(client):
    res = client.get('/student/dashboard', follow_redirects=False)
    assert res.status_code == 302
    assert '/login' in res.location

    res = client.get('/teacher/dashboard', follow_redirects=False)
    assert res.status_code == 302
    assert '/login' in res.location

    res = client.get('/admin/dashboard', follow_redirects=False)
    assert res.status_code == 302
    assert '/login' in res.location


def test_student_cannot_access_admin_or_teacher(client, test_student):
    # Log in as student
    client.post('/login', data={'username': test_student.username, 'password': 'StudentTestPassword!123'})

    # Try admin
    res = client.get('/admin/dashboard', follow_redirects=True)
    assert res.status_code == 200
    assert b"Access denied" in res.data

    # Try teacher
    res = client.get('/teacher/dashboard', follow_redirects=True)
    assert res.status_code == 200
    assert b"Access denied" in res.data


def test_teacher_cannot_access_admin(client, test_teacher):
    # Log in as teacher
    client.post('/login', data={'username': test_teacher.username, 'password': 'TeacherTestPassword!123'})

    # Try admin
    res = client.get('/admin/dashboard', follow_redirects=True)
    assert res.status_code == 200
    assert b"Access denied" in res.data


def test_admin_has_full_access(client, test_admin):
    # Log in as admin
    client.post('/login', data={'username': test_admin.username, 'password': 'AdminTestPassword!123'})

    res = client.get('/admin/dashboard')
    assert res.status_code == 200
    assert b"System Administration" in res.data

