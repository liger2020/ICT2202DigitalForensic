import json.decoder
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dateutil import parser
import hashlib
from app import db
from app.models import Pool, Peers, User_stored_info


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
    url = "http://{}:5000/receive_response ".format(ip_address)
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post(url, json=data, headers=headers, timeout=1)
    try:
        output = {"Peer": url,
                  "Answer": r.json(),
                  "Status_Code": r.status_code
                  }

        return output
    except json.decoder.JSONDecodeError:
        return {"Error": "True"}


def convert_to_user_stored_info(json_block):
    try:
        block = User_stored_info(json_block["id"], json_block["block_hash"], json_block["block_number"] + 1)
        return block
    except KeyError:
        return None


def convert_to_pool(json_block):
    try:
        pool = Pool(json_block["id"], json_block["case_id"], json_block["meta_data"], json_block["log"], parser.parse(json_block["timestamp"]),
                    json_block["previous_block_hash"], json_block["block_hash"])
        return pool
    except KeyError:
        return None
    except TypeError:
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
        original_block = User_stored_info.query.filter_by(id=case_id).first()
        # Check if longer
        if length_json["length"] <= original_block.length:
            continue

        resp = requests.post("http://{}:{}/sync".format(peer.ip_address, peer.port),
                             json={"id": case_id, "length": original_block.length, "last": 1}, timeout=3)

        if resp.status_code == 200:
            resp_json = resp.json()
            for block_json in resp_json["Blocks"]:
                block = convert_to_user_stored_info(block_json)
                if block is not None:
                    original_block.block_hash = block.block_hash
                    original_block.length = block.length
            db.session.commit()


def verify(unverified_block):
    # unverified block is in json format
    user_block_info = User_stored_info.query.filter_by(case_id=unverified_block.case_id).first_or_404()
    if user_block_info.last_verified_hash == unverified_block.previous_block_hash:
        verifying = "-".join(unverified_block.meta_data) + "-".join(unverified_block.log) + "-" + str(
            unverified_block.timestamp) \
                    + "-" + user_block_info.last_verified_hash
        verify_block_hash = hashlib.sha256(verifying.encode()).hexdigest()
        if verify_block_hash == unverified_block.block_hash:
            return True
        else:
            return False
