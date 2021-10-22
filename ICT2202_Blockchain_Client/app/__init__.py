from flask import Flask
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

# Configurations
app.config.from_object('config')

auth = HTTPTokenAuth(scheme='Bearer')

db = SQLAlchemy(app)

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

from app import views
from app.controller import sync_schedule

bg_scheduler = BackgroundScheduler()
bg_scheduler.add_job(func=sync_schedule, trigger="interval", seconds=60)
bg_scheduler.start()

# Build the database
db.create_all()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())