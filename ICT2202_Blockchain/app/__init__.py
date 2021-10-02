from flask import Flask
from flaskext.mysql import MySQL

app = Flask(__name__)
app.config.from_object('config')

mysql = MySQL(app)

from app import views
