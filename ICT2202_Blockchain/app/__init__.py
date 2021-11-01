import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

# Configurations
app.config.from_object('config')

auth = HTTPTokenAuth(scheme='Bearer')
db = SQLAlchemy(app)

# Using SQLAlchemy ORM for Session
engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

from app.controller import sync_schedule, send_unverified_block, check_twothird

bg_scheduler = BackgroundScheduler()
bg_scheduler.add_job(func=sync_schedule, trigger="interval", seconds=10)
bg_scheduler.add_job(func=send_unverified_block, trigger="interval", seconds=10)
bg_scheduler.add_job(func=check_twothird, trigger="interval", seconds=10)
bg_scheduler.start()

from app import views
from app.models import Peers


# Init the Peers Table db with values (hardcode)
@event.listens_for(Peers.__table__, 'after_create')
def insert_initial_values(*args, **kwargs):
    init_list = [
        ("127.0.0.1", 5000, "server"),
        ("192.168.1.1", 5000, "client"),
    ]
    for (ip_address, port, server_type) in init_list:
        db.session.add(Peers(ip_address=ip_address, port=port, server_type=server_type))
    db.session.commit()


# Build the database
db.create_all()

# Shut down the scheduler when exiting the app
atexit.register(lambda: bg_scheduler.shutdown())
