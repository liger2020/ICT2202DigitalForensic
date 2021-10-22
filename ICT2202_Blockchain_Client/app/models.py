from sqlalchemy.orm import relationship

from app import db
import hashlib
from datetime import datetime


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


class Peers(Base):
    __tablename__ = "peers"
    # __table_args__ = {'extend_existing': True}
    ip_address = db.Column(db.String(15), nullable=False, unique=True)
    port = db.Column(db.SmallInteger, nullable=True)

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Pool(db.Model):
    __tablename__ = "pool"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    case_id = db.Column(db.Integer, nullable=True)
    block_number = db.Column(db.Integer, nullable=True)
    previous_block_hash = db.Column(db.String(255))
    meta_data = db.Column(db.String(255), nullable=True)
    log = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)
    block_hash = db.Column(db.String(255))
    status = db.Column(db.Boolean)
    count = db.Column(db.Integer, nullable=True)
    sendout_time = db.Column(db.DateTime, nullable=True)

    def __init__(self, case_id, meta_data, log):
        self.case_id = case_id
        self.block_number = 0

        self.meta_data = meta_data
        self.log = log
        self.timestamp = datetime.now()
        self.block_data = ""
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()
        self.status = False
        self.count = 0
        self.sendout_time = None

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User_stored_info(db.Model):
    __tablename__ = "user_stored_info"
    __table_args__ = {'extend_existing': True}

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    case_id = db.Column(db.String(15), nullable=False)
    last_verified_hash = db.Column(db.String(255))
    length = db.Column(db.Integer, nullable=False)

    def __init__(self, case_id, last_verified_hash, length):
        self.case_id = case_id
        self.last_verified_hash = last_verified_hash
        self.length = length

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
