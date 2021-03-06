import atexit
import os
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers import interval
from flask import Flask
from flask_httpauth import HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, event
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

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

# Using SQLAlchemy ORM for Session
engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

from app.controller import sync_schedule, send_unverified_block, check_twothird

bg_scheduler = BackgroundScheduler()
trigger = interval.IntervalTrigger(seconds=10)
bg_scheduler.add_job(func=sync_schedule, trigger=trigger)
bg_scheduler.add_job(func=send_unverified_block, trigger=trigger)
bg_scheduler.add_job(func=check_twothird, trigger=trigger)
bg_scheduler.start()

from app import views
from app.models import Peers


# Init the Peers Table db with values (hardcode)
@event.listens_for(Peers.__table__, 'after_create')
def insert_initial_values(*args, **kwargs):
    init_list = []
    try:
        with open(os.path.join(BASE_DIR, 'nodes.txt'), "r") as f:
            lines = f.readlines()

            for line in lines:
                (ip, port, servertype) = line.strip().split(sep=',')
                init_list.append((ip, int(port), servertype))
    except FileNotFoundError:
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
