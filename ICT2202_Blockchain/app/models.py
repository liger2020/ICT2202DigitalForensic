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
    __table_args__ = {'extend_existing': True}
    ip_address = db.Column(db.String(15), nullable=False, unique=True)
    port = db.Column(db.SmallInteger, nullable=True)

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port


# TODO Placeholder (Ray)
class Block(db.Model):
    __tablename__ = "Block"
    __table_args__ = {'extend_existing': True}
    index= db.Column(db.Integer)
    id = db.Column(db.Integer, primary_key=True)
    proof_number = db.Column(db.Integer)
    previous_block_hash = db.Column(db.String(255), nullable=True)
    meta_data = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.Time, nullable=True)
    block_hash = db.Column(db.String(255), nullable=True)

    def __init__(self, index, proof_number, previous_block_hash, meta_data):
        """
        this for the creation of a new block NOT for the blockchain
        :param index: case number
        :param proof_number: position in the blockchain
        :param previous_block_hash: this refers to the hash of the previous block within the chain;
        :param meta_data: this refers to whatever information we want to put in. can give json format or just str.
        """
        self.index = index
        self.proof_number = proof_number
        self.previous_block_hash = str(previous_block_hash)
        self.meta_data = meta_data
        self.timestamp = str(datetime.now())
        self.block_data = "-".join(meta_data) + "-" + self.timestamp \
                          + "-" + self.previous_block_hash
        self.block_hash = hashlib.sha256(self.block_data.encode()).hexdigest()

    def __repr__(self):
        return "index: {}\nproof_number: {}\nprevious_block_hash: {}\nmeta_data: {}\ntimestamp: {}".format(self.index, self.proof_number, self.previous_block_hash,
                                                                          self.meta_data, self.timestamp)
