from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

# Configurations
app.config.from_object('config')

db = SQLAlchemy(app)

from app.controller import sync_schedule

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

bg_scheduler = BackgroundScheduler()
# bg_scheduler.add_job(func=sync_schedule, trigger="interval", seconds=30)
bg_scheduler.start()

from app import views

# Build the database
db.create_all()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())