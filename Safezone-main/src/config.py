import os


class Config:
    SECRET_KEY = 'your_secret_key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'flask_login_'
    SESSION_FILE_DIR = os.path.join(os.path.dirname(__file__), 'instance/sessions')
    os.makedirs(SESSION_FILE_DIR, exist_ok=True)
