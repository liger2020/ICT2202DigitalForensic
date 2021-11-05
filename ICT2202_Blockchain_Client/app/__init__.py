import atexit
import os
import sys

from flask import Flask
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy, event
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import interval


app = Flask(__name__)

# Configurations
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
elif __file__:
    BASE_DIR = os.path.dirname(__file__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["THREADS_PER_PAGE"] = 2
# app.config.from_object('config')

auth = HTTPTokenAuth(scheme='Bearer')

db = SQLAlchemy(app)

from app import views
from app.controller import sync_schedule

bg_scheduler = BackgroundScheduler()
trigger = interval.IntervalTrigger(seconds=10)
bg_scheduler.add_job(func=sync_schedule, trigger=trigger)
bg_scheduler.start()

from app.models import Peers


# Init the Peers Table db with values (hardcode)
@event.listens_for(Peers.__table__, 'after_create')
def insert_initial_values(*args, **kwargs):
    init_list = []
    with open(os.path.join(BASE_DIR, 'nodes.txt'), "r") as f:
        lines = f.readlines()

        for line in lines:
            (ip, port, servertype) = line.split(sep=',')
            init_list.append((ip, int(port), servertype))

    for (ip_address, port, server_type) in init_list:
        db.session.add(Peers(ip_address=ip_address, port=port, server_type=server_type))
    db.session.commit()


# Build the database
db.create_all()

# Shut down the scheduler when exiting the app
atexit.register(lambda: bg_scheduler.shutdown())
