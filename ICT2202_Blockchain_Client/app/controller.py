import requests
from dateutil import parser

from app.models import Block


def convert_to_block(json_block):
    try:
        block = Block(json_block["id"], json_block["meta_data"], json_block["log"], json_block["status"])
        if "block_number" in json_block and "previous_block_hash" in json_block and "timestamp" in json_block and "block_hash" in json_block:
            block.id = json_block["id"]
            block.block_number = json_block["block_number"]
            block.previous_block_hash = json_block["previous_block_hash"]
            block.meta_data = json_block["meta_data"]
            block.log = json_block["log"]
            if isinstance(json_block["timestamp"], str):
                block.timestamp = parser.parse(json_block["timestamp"])
            else:
                block.timestamp = json_block["timestamp"]
            block.block_hash = json_block["block_hash"]
            block.status = json_block["status"]
        return block
    except KeyError:
        return None


def check_health(peer):
    try:
        resp = requests.get("http://{}:{}/health".format(peer.ip_address, peer.port), timeout=3)
        if resp.status_code == 200:
            return peer

        return None
    except:
        return None