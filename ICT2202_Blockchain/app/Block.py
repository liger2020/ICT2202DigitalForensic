# Placeholder Class
import json


class Block():
    def __init__(self, block_id, comment, amount, isverified=None):
        self.block_id = block_id
        self.comment = comment
        self.amount = amount
        self.isverified = isverified

    def print_data(self):
        print("ID: {}".format(self.block_id))
        print("Comment: {}".format(self.comment))
        print("Amount: {}".format(self.amount))
        print("Verified: {}".format(self.isverified))


def convert_to_block(json_block):
    try:
        return Block(json_block["ID"], json_block["Comment"], json_block["Amount"])
    except KeyError:
        return None
