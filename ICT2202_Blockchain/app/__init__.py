from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from flask_apscheduler import APScheduler

app = Flask(__name__)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# Configurations
app.config.from_object('config')

db = SQLAlchemy(app)
api = Api(app)

from app import views

# Build the database
db.create_all()
