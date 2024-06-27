import pytest
from ..app import app, db
from ..models import User, UserSession, Content


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


def test_register(client):
    response = client.post('/register', data=dict(
        username='testuser',
        password='password',
        confirm='password'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Your account has been created! You are now able to log in' in response.data


def test_login(client):
    # 注册用户
    client.post('/register', data=dict(
        username='testuser',
        password='password',
        confirm='password'
    ), follow_redirects=True)

    # 测试登录
    response = client.post('/login', data=dict(
        username='testuser',
        password='password'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Login successful!' in response.data


def test_prevent_double_login(client):
    # 注册用户
    client.post('/register', data=dict(
        username='testuser',
        password='password',
        confirm='password'
    ), follow_redirects=True)

    # 第一次登录
    client.post('/login', data=dict(
        username='testuser',
        password='password'
    ), follow_redirects=True)

    # 尝试第二次登录
    response = client.post('/login', data=dict(
        username='testuser',
        password='password'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'This account is already logged in from another device.' in response.data


def test_logout(client):
    # 注册用户
    client.post('/register', data=dict(
        username='testuser',
        password='password',
        confirm='password'
    ), follow_redirects=True)

    # 登录
    client.post('/login', data=dict(
        username='testuser',
        password='password'
    ), follow_redirects=True)

    # 测试登出
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data


def test_content_post_and_delete(client):
    # 注册用户
    client.post('/register', data=dict(
        username='testuser',
        password='password',
        confirm='password'
    ), follow_redirects=True)

    # 登录
    client.post('/login', data=dict(
        username='testuser',
        password='password'
    ), follow_redirects=True)

    # 发布内容
    response = client.post('/home', data=dict(
        text='This is a test content'
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b'Content saved successfully!' in response.data

    # 删除内容
    content = Content.query.first()
    response = client.delete(f'/delete_content/{content.id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'success' in response.json['result']

