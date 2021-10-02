from app import db


class Base(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, default=db.func.current_timestamp())
    date_modified = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())


# TODO Placeholder for testing
class Peers(Base):
    __tablename__ = "peers"

    ip_address = db.Column(db.String(15), nullable=False, unique=True)
    port = db.Column(db.SmallInteger, nullable=True)

    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port


# TODO Placeholder (Ray)
class Block(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(255), nullable=True)
    amount = db.Column(db.String(255), nullable=True)
    isverified = db.Column(db.Boolean, nullable=False)

    def __init__(self, block_id, comment, amount, isverified):
        self.block_id = block_id
        self.comment = comment
        self.amount = amount
        self.isverified = isverified

    def __repr__(self):
        return "ID: {}\nComment: {}\nAmount: {}\nVerified: {}".format(self.block_id, self.comment, self.amount, self.isverified)
