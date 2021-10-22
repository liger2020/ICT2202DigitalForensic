import os

from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

# Configurations
app.config.from_object('config')

auth = HTTPBasicAuth()
db = SQLAlchemy(app)

# Using SQLAlchemy ORM for Session
engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

from app.controller import sync_schedule, send_unverified_block, check_twothird

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

bg_scheduler = BackgroundScheduler()
# bg_scheduler.add_job(func=sync_schedule, trigger="interval", seconds=30)
bg_scheduler.add_job(func=send_unverified_block, trigger="interval", seconds=10)
bg_scheduler.add_job(func=check_twothird, trigger="interval", seconds=10)
bg_scheduler.start()

from app import views

# Build the database
db.create_all()

# Shut down the scheduler when exiting the app
atexit.register(lambda: bg_scheduler.shutdown())
