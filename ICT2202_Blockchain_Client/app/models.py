from app import db


class Peers(db.Model):
    """
    Keeps database on who and how to communicate to other clients/nodes
    """
    __tablename__ = "Peers"
    # __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ip_address = db.Column(db.String(15), nullable=False, unique=True)
    port = db.Column(db.SmallInteger, nullable=True)
    server_type = db.Column(db.String(6), nullable=True)

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


class Pool(db.Model):
    __tablename__ = "Pool"
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, nullable=True)
    previous_block_hash = db.Column(db.String(255))
    meta_data = db.Column(db.String(255), nullable=True)
    log = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=True)
    block_hash = db.Column(db.String(255))

    def __init__(self, id, case_id, meta_data, log, timestamp, previous_block_hash, block_hash):
        self.id = id
        self.case_id = case_id
        self.meta_data = meta_data
        self.log = log
        self.timestamp = timestamp
        self.previous_block_hash = previous_block_hash
        self.block_hash = block_hash

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class UserStoredInfo(db.Model):
    """
    Keeps database on the last hash of all cases
    """
    __tablename__ = "UserStoredInfo"
    __table_args__ = {'extend_existing': True}

    user_id: int = db.Column(db.Integer, primary_key=True, autoincrement=True)
    case_id = db.Column(db.String(15), nullable=False)
    last_verified_hash = db.Column(db.String(255))
    length = db.Column(db.Integer, nullable=False)

    def __init__(self, case_id, last_verified_hash, length):
        """
        Init function of UserStoredInfo class
        :param case_id: Case ID of the case
        :type case_id: str
        :param last_verified_hash: Last verified hash of cases
        :type last_verified_hash: str
        :param length: Length of the Case Blockchain
        :type length: int
        """
        self.case_id = case_id
        self.last_verified_hash = last_verified_hash
        self.length = length

    def as_dict(self):
        """Returns this object as dict

        Converts all keypair into a dict for outputing/processed as json object

        :return: Object as dict
        :rtype: dict
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
