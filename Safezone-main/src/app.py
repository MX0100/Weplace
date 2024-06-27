import sys

from flask import Flask, render_template, redirect, url_for, flash, session, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import os
import socket
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import db, User, Content, UserSession

from interceptor import login_required

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)  # 初始化db
Session(app)
socketio = SocketIO(app)

# 导入表单和模型
from forms import LoginForm, RegistrationForm, ContentForm

@app.before_request
def create_tables():
    with app.app_context():
        db.create_all()

def validate_session():
    session_token = session.get('session_token') or request.args.get('session_token')
    username = session.get('username')

    if not username or not session_token:
        return False

    user = User.query.filter_by(username=username).first()
    if not user:
        return False

    user_session = UserSession.query.filter_by(session_token=session_token, user_id=user.id).first()
    if not user_session:
        return False

    if user_session.expires_at <= datetime.utcnow():
        return False

    return True

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            existing_session = UserSession.query.filter_by(user_id=user.id).first()
            if existing_session and existing_session.expires_at > datetime.utcnow():
                flash('This account is already logged in from another device.', 'danger')
                return redirect(url_for('login'))

            user_session = UserSession(user_id=user.id)
            db.session.add(user_session)
            db.session.commit()

            session['username'] = user.username
            session['session_token'] = user_session.session_token
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            flash('That username is taken. Please choose a different one.', 'danger')
        else:
            user = User(username=form.username.data, password=form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if not validate_session():
        flash('Session has expired. Please log in again.', 'danger')
        return redirect(url_for('login'))

    form = ContentForm()
    if form.validate_on_submit():
        content = Content(text=form.text.data)
        db.session.add(content)
        db.session.commit()
        socketio.emit('new_content', {'text': content.text, 'id': content.id})
        flash('Content saved successfully!', 'success')

    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = 6  # 每页显示的条数
    pagination = Content.query.order_by(Content.id.desc()).paginate(page, per_page, False)
    contents = pagination.items
    has_next = pagination.has_next
    has_prev = pagination.has_prev  # 添加上一页的检查

    return render_template('home.html', form=form, contents=contents, page=page, has_next=has_next, has_prev=has_prev)

@app.route('/delete_content/<int:content_id>', methods=['DELETE'])
@login_required
def delete_content(content_id):
    content = Content.query.get_or_404(content_id)
    try:
        content = db.session.merge(content)  # 确保对象在当前会话中
        db.session.delete(content)
        db.session.commit()
        socketio.emit('delete_content', {'id': content_id})
        return jsonify({'result': 'success'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting content: {e}")
        return jsonify({'result': 'failure', 'error': str(e)}), 500

@app.route('/logout')
@login_required
def logout():
    if 'session_token' in session:
        session_token = UserSession.query.filter_by(session_token=session['session_token']).first()
        if session_token:
            session_token = db.session.merge(session_token)  # 确保对象在当前会话中
            db.session.delete(session_token)
            db.session.commit()
    session.pop('username', None)
    session.pop('session_token', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/api_logout', methods=['POST'])
@login_required
def api_logout():
    if 'session_token' in session:
        session_token = UserSession.query.filter_by(session_token=session['session_token']).first()
        if session_token:
            session_token = db.session.merge(session_token)  # 确保对象在当前会话中
            db.session.delete(session_token)
            db.session.commit()
    session.pop('username', None)
    session.pop('session_token', None)
    return '', 204

# SocketIO事件处理程序
@socketio.on('connect')
def handle_connect():
    print('Client connected:', request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected:', request.sid)

if __name__ == '__main__':
    # 获取本机IP地址
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print(f'Server running on http://{local_ip}:5000')
    socketio.run(app, debug=True, host='0.0.0.0')
