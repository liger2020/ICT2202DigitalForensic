"""
Database model for SQLite database
"""
import hashlib
from datetime import datetime

from app import db


class Peers(db.Model):
    """
    Keeps database on who and how to communicate to other clients/nodes
    """
    __tablename__ = "Peers"
    # __table_args__ = {'extend_existing': True}
    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(15), nullable=False, unique=True)
    port = db.Column(db.SmallInteger, nullable=True)
    server_type = db.Column(db.String(6), nullable=False)

    def __init__(self, ip_address, port, server_type):
        """
        Init function of Peers Class
        :param ip_address: IP Address of the machine
        :type ip_address: str
        :param port: Port Number of the machine
        :type port: int
        :param server_type: "server" / "client" to identify the machine
        :type server_type: str
        """
        self.ip_address = ip_address
        self.port = port
        self.server_type = server_type

    def as_dict(self):
        """Returns this object as dict

        Converts all keypair into a dict for outputing/processed as json object

        :return: Object as dict
        :rtype: dict
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Block(db.Model):
    """
    Keeps database of the blockchain itself
    """
    __tablename__ = "Block"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.String(255), primary_key=True)
    block_number = db.Column(db.Integer, primary_key=True)
    previous_block_hash = db.Column(db.String(255))
    meta_data = db.Column(db.String(255), nullable=True)
    log = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)
    block_hash = db.Column(db.String(255))
    status = db.Column(db.Boolean)

    def __init__(self, id, meta_data, log, block_number=None, previous_block_hash=None, timestamp=None, block_hash=None,
                 status=None):
        """
        this for the creation of a new block NOT for the blockchain
        :param id: case number
        :param block_number: position in the blockchain
        :param previous_block_hash: this refers to the hash of the previous block within the chain;
        :param meta_data: this refers to whatever information we want to put in. can give json format or just str.
        """

        self.id = id
        if block_number is None:
            self.set_block_number()
        else:
            self.block_number = block_number
            self.previous_block_hash = previous_block_hash

        self.meta_data = meta_data
        self.log = log

        if timestamp is None:
            self.timestamp = datetime.now()
        else:
            self.timestamp = timestamp

        if block_hash is None:
            block_data = self.case_id + "-" + str(self.block_number) + "-" + self.meta_data + "-" + self.log + "-" + \
                         str(self.timestamp) + "-" + self.previous_block_hash
            self.block_hash = hashlib.sha256(block_data.encode()).hexdigest()
        else:
            self.block_hash = block_hash

        if status is None:
            self.status = False
        else:
            self.status = status

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
        """
        Returns this object as dict

        Converts all rows into a dict for outputing/processed as json object

        :return: Object as dict
        :rtype: dict
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def set_block_number(self):
        """
        return block_number given id, if id is does not exist block_number is 0 else it is the next increment

        :return: block_number
        :rtype: str
        """
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
    case_id = db.Column(db.String(255), nullable=True)
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
        self.block_data = self.case_id + "-" + str(
            self.block_number) + "-" + self.meta_data + "-" + self.log + "-" + str(self.timestamp) \
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
    pool_id = db.Column(db.String(15), nullable=True)
    response = db.Column(db.Boolean, nullable=False)
    receive_timestamp = db.Column(db.DateTime, nullable=True)

    def __init__(self, ip_address, pool_id, response):
        self.ip_address = ip_address
        self.pool_id = pool_id
        self.response = response
        self.receive_timestamp = datetime.now()

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class UserCase(db.Model):
    """
    Keeps track on the User's assigned cases in the blockchain
    """
    __tablename__ = "UserCase"
    __table_args__ = {'extend_existing': True}

    id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    case_id = db.Column(db.String(255), nullable=False)

    def __init__(self, username, case_id):
        """
        Init function of UserCase Class

        :param username: Username of the User
        :type username: str
        :param case_id: Case ID of the case
        :type case_id: str
        """
        self.username = username
        self.case_id = case_id

    def as_dict(self):
        """Returns this object as dict

        Converts all keypair into a dict for outputing/processed as json object

        :return: Object as dict
        :rtype: dict
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}