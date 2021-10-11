from app import db
import hashlib
from datetime import datetime


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


# TODO Placeholder for testing
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


# TODO Placeholder (Ray)
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

    def __init__(self, id, meta_data, log, status):
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
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def set_block_number(self):
        result = Block.query.filter_by(id=self.id).order_by(Block.block_number.desc()).first()
        if result is None:
            self.block_number = 0
            self.previous_block_hash = str("")
        else:
            self.block_number = result.block_number+1
            self.previous_block_hash = result.block_hash



