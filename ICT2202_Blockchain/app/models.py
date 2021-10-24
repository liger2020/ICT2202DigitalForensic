from app import db, app
import hashlib
from datetime import datetime
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from passlib.apps import custom_app_context as pwd_context


class Peers(db.Model):
    __tablename__ = "Peers"
    # __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(15), nullable=False, unique=True)
    port = db.Column(db.SmallInteger, nullable=True)
    server_type = db.Column(db.String(6), nullable=False)

    def __init__(self, ip_address, port, server_type):
        self.ip_address = ip_address
        self.port = port
        self.server_type = server_type

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Block(db.Model):
    __tablename__ = "Block"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    block_number = db.Column(db.Integer, primary_key=True)
    previous_block_hash = db.Column(db.String(255))
    meta_data = db.Column(db.String(255), nullable=True)
    log = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)
    block_hash = db.Column(db.String(255))
    status = db.Column(db.Boolean)

    def __init__(self, id, meta_data, log):
        """
        this for the creation of a new block NOT for the blockchain
        :param id: case number
        :param block_number: position in the blockchain
        :param previous_block_hash: this refers to the hash of the previous block within the chain;
        :param meta_data: this refers to whatever information we want to put in. can give json format or just str.
        """

        self.id = id
        self.set_block_number()

        self.meta_data = meta_data
        self.log = log
        self.timestamp = datetime.now()
        self.block_data = "-".join(meta_data) + "-".join(log) + "-" + str(self.timestamp) \
                          + "-" + self.previous_block_hash
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()
        self.status = False

    def __repr__(self):
        return "id: {}\nblock_number: {}\nprevious_block_hash: {}\nmeta_data: {}\nlog: " \
               "{}\ntimestamp: {}\nblock_hash: {}\nstatus: {}".format(self.id,
                                                                      self.block_number,
                                                                      self.previous_block_hash,
                                                                      self.meta_data, self.log,
                                                                      self.timestamp,
                                                                      self.block_hash,
                                                                      self.status)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def set_block_number(self):
        result = Block.query.filter_by(id=self.id).order_by(Block.block_number.desc()).first()
        if result is None:
            self.block_number = 0
            self.previous_block_hash = str("")
        else:
            self.block_number = result.block_number + 1
            self.previous_block_hash = result.block_hash


class Pool(db.Model):
    __tablename__ = "Pool"
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
        """
        this for the creation of a new block NOT for the blockchain
        :param id: case number
        :param block_number: position in the blockchain
        :param previous_block_hash: this refers to the hash of the previous block within the chain;
        :param meta_data: this refers to whatever information we want to put in. can give json format or just str.
        """

        self.case_id = case_id
        self.set_block_number()

        self.meta_data = meta_data
        self.log = log
        self.timestamp = datetime.now()
        self.block_data = "-".join(meta_data) + "-".join(log) + "-" + str(self.timestamp) \
                          + "-" + self.previous_block_hash
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()
        self.status = False
        self.count = 0
        self.sendout_time = None

    def __repr__(self):
        return "case_id: {}\nblock_number: {}\nprevious_block_hash: {}\nmeta_data: {}\nlog: " \
               "{}\ntimestamp: {}\nblock_hash: {}\nstatus: {}\ncount:".format(self.case_id,
                                                                              self.block_number,
                                                                              self.previous_block_hash,
                                                                              self.meta_data, self.log,
                                                                              self.timestamp,
                                                                              self.block_hash,
                                                                              self.status,
                                                                              self.count)

    def set_block_number(self):
        result = Block.query.filter_by(id=self.case_id).order_by(Block.block_number.desc()).first()
        if result is None:
            self.block_number = 0
            self.previous_block_hash = str("")
        else:
            self.block_number = result.block_number + 1
            self.previous_block_hash = result.block_hash

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Consensus(db.Model):
    __tablename__ = "Consensus"
    __table_args__ = {'extend_existing': True}

    consensus_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(15), nullable=False)
    pool_id = db.Column(db.Integer, nullable=True)
    response = db.Column(db.Boolean, nullable=False)
    receive_timestamp = db.Column(db.DateTime, nullable=True)

    def __init__(self, ip_address, pool_id, response):
        self.ip_address = ip_address
        self.pool_id = pool_id
        self.response = response
        self.receive_timestamp = datetime.now()

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(db.Model):
    __tablename__ = 'Users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    password_hash = db.Column(db.String(128))
    ip_address = db.Column(db.String(128), nullable=True)
    token = db.Column(db.String(128), nullable=True)

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self):
        s = Serializer(app.config['SECRET_KEY'])
        token = s.dumps({'id': self.id})
        self.token = token.decode('ascii')
        return s.dumps({'id': self.id})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None  # valid token, but expired
        except BadSignature:
            return None  # invalid token
        user = User.query.get(data['id'])
        return user


class UserCase(db.Model):
    __tablename__ = "UserCase"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    case_id = db.Column(db.Integer, nullable=False)

    def __init__(self, username, case_id):
        self.username = username
        self.case_id = case_id

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# class User_stored_info(db.Model):
#     __tablename__ = "user_stored_info"
#     __table_args__ = {'extend_existing': True}

#     user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     case_id = db.Column(db.String(15), nullable=False)
#     last_verified_hash = db.Column(db.String(255))

#     def __init__(self, case_id, last_verified_hash):
#         self.case_id = case_id
#         self.last_verified_hash = last_verified_hash

#     def as_dict(self):
#         return {c.name: getattr(self, c.name) for c in self.__table__.columns}
