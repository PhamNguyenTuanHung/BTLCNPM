from flask import Flask, request, jsonify, redirect, url_for, session, g
# from flask_socketio import SocketIO
# from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
from flask_login import LoginManager
from flask_login import UserMixin
import cloudinary
# from flask_mail import Mail
import os
# from dotenv import load_dotenv
# from authlib.integrations.flask_client import OAuth

# db = SQLAlchemy()
# migrate = Migrate()
# login = LoginManager()
# mail = Mail()
# load_dotenv()
# oauth = OAuth()
# socketio = SocketIO()

user = os.getenv('MAIL_USERNAME')
password = os.getenv('MAIL_PASSWORD')

db_user = os.getenv("DB_USER")
db_pass = os.getenv("DB_PASS")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_driver = os.getenv("DB_DRIVER")

secret_key = os.getenv("SECRET_KEY")

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

from .models import User


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mssql+pyodbc://{db_user}:{db_pass}@{db_host}/{db_name}?driver={db_driver}"
    )

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = secret_key
    app.config['PAGE_SIZE'] = 12

    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_SSL'] = True
    app.config['MAIL_USERNAME'] = user
    app.config['MAIL_PASSWORD'] = password

    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )


    login.login_view = 'main.login'

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)
    socketio.init_app(app)


    @login.user_loader
    def load_user(user_id):
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            return None

        with app.app_context():
            return db.session.get(User, user_id_int)
            # =======================================================

    oauth.register(
        name='google',
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid email profile"
        }
    )

    from QuanLyHocSinh.routes import main,admin
    app.register_blueprint(main)
    app.register_blueprint(admin)

    return app