import json.decoder
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dateutil import parser

from app import db
from app.models import Pool, Peers, Block


def check_health(peer):
    try:
        resp = requests.get("http://{}:{}/health".format(peer.ip_address, peer.port), timeout=3)
        if resp.status_code == 200:
            return peer

        return None
    except:
        return None


def get_live_peers():
    # Check peers alive
    live_peers = []
    futures = []

    pool = ThreadPoolExecutor(5)  # 5 Worker Threads

    # Get all peer's ip address and port from DB
    peer_list = Peers.query.all()

    # Use check_health() to get whether machine online
    for peer in peer_list:
        futures.append(pool.submit(check_health, peer))

    for x in as_completed(futures):
        result = x.result()
        if result is not None:
            live_peers.append(result)

    return live_peers


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


def convert_to_block(json_block):
    try:
        block = Block(json_block["id"], json_block["block_hash"], json_block["block_number"] + 1)
        return block
    except KeyError:
        return None


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


def sync_schedule():
    futures = []

    thread_pool = ThreadPoolExecutor(5)  # 5 Worker Threads
    live_peers = get_live_peers()
    for peer in live_peers:
        futures.append(thread_pool.submit(send_sync, peer))


def send_sync(peer):
    # Ask for his length
    resp = requests.get("http://{}:{}/sync".format(peer.ip_address, peer.port))
    if resp.status_code != 200:
        return None

    resp_json = resp.json()
    # Make sure json is valid
    if "Blocks" not in resp_json:
        return None

    # Check length received
    for length_json in resp_json["Blocks"]:
        # Make sure json is valid
        if "id" not in length_json or "length" not in length_json:
            continue

        case_id = length_json["id"]
        original_block = Block.query.filter_by(id=case_id).first()
        # Check if longer
        if length_json["length"] <= original_block.length:
            continue

        resp = requests.post("http://{}:{}/sync".format(peer.ip_address, peer.port),
                             json={"id": case_id, "length": original_block.length, "last": 1}, timeout=3)

        if resp.status_code == 200:
            resp_json = resp.json()
            for block_json in resp_json["Blocks"]:
                block = convert_to_block(block_json)
                if block is not None:
                    original_block.block_hash = block.block_hash
                    original_block.length = block.length
            db.session.commit()
