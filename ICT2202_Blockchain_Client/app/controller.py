import json.decoder
from datetime import datetime

from dateutil import parser

import requests

from app.models import Pool


def send_block(ip_address, data):
    url = "http://{}:5000/receive_response".format(ip_address)
    r = requests.post(url, json=data)
    try:
        output = {"Peer": url,
                  "Answer": r.json(),
                  "Status_Code": r.status_code
                  }

        return output
    except json.decoder.JSONDecodeError:
        return {"Error": "True"}



def convert_to_pool(json_block):
    try:
        pool = Pool(json_block["id"], json_block["meta_data"], json_block["log"])
        if "block_number" in json_block and "previous_block_hash" in json_block and "timestamp" in json_block and "block_hash" in json_block:
            pool.id = json_block["id"]
            pool.case_id = json_block["case_id"]
            pool.block_number = json_block["block_number"]
            pool.previous_block_hash = json_block["previous_block_hash"]
            pool.meta_data = json_block["meta_data"]
            pool.log = json_block["log"]
            if isinstance(json_block["timestamp"], str):
                pool.timestamp = parser.parse(json_block["timestamp"])
            else:
                pool.timestamp = json_block["timestamp"]
            pool.block_hash = json_block["block_hash"]
            pool.status = json_block["status"]
        return pool
    except KeyError:
        return None



