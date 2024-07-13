from app import db, Content
from flask import Flask
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def update_date_published():
    with app.app_context():
        # 更新所有现有内容的 date_published 列
        contents = Content.query.all()
        for content in contents:
            if content.date_published is None:
                content.date_published = datetime.utcnow()
                db.session.add(content)
        db.session.commit()

if __name__ == "__main__":
    update_date_published()
