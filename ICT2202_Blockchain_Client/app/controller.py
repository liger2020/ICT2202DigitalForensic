import json.decoder
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from dateutil import parser
import hashlib
from app import db
from app.models import Pool, Peers, UserStoredInfo


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
    peer_list = Peers.query.filter_by(server_type="server").all()

    # Use check_health() to get whether machine online
    for peer in peer_list:
        futures.append(pool.submit(check_health, peer))

    for x in as_completed(futures):
        result = x.result()
        if result is not None:
            live_peers.append(result)

    return live_peers


def send_block(peer, data, url):
    url = "http://{}:{}/{}".format(peer.ip_address, peer.port, url)
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain', "Authorization": "Bearer secret-token-1"}
    if data == "":
        r = requests.get(url, headers=headers, timeout=3)
        return r
    else:
        r = requests.post(url, json=data, headers=headers, timeout=3)
        try:
            answer = r.json()

        except json.decoder.JSONDecodeError:
            answer = r.text

        output = {
            "Peer": url,
            "Answer": answer,
            "Status_Code": r.status_code
        }

        return output


def convert_to_user_stored_info(json_block):
    try:
        block = UserStoredInfo(json_block["id"], json_block["block_hash"], json_block["block_number"] + 1)
        return block
    except KeyError:
        return None


def convert_to_pool(json_block):
    try:
        pool = Pool(json_block["id"], json_block["case_id"], json_block["meta_data"], json_block["log"],
                    parser.parse(json_block["timestamp"]),
                    json_block["previous_block_hash"], json_block["block_hash"])
        return pool
    except KeyError:
        return None
    except TypeError:
        return None


def sync_schedule():
    thread_pool = ThreadPoolExecutor(5)  # 5 Worker Threads

    live_peers = get_live_peers()
    for peer in live_peers:
        thread_pool.submit(send_sync, peer)


def send_sync(peer):
    thread_pool = ThreadPoolExecutor(5)  # 5 Worker Threads

    # Ask for his length
    resp = send_block(peer, "", "sync")
    if resp.status_code != 200:
        return None

    # Read Response
    resp_json = resp.json()
    # Make sure json is valid
    if "Blocks" not in resp_json:
        return None

    # Check length received
    blocks = resp_json["Blocks"]
    for length_json in blocks:
        # Make sure json is valid
        if "id" not in length_json or "length" not in length_json:
            continue

        case_id = length_json["id"]
        original_block = UserStoredInfo.query.filter_by(case_id=case_id).first()
        if original_block is not None:
            # Check if longer, dont ask to update
            if original_block.length >= length_json["length"]:
                continue

        # If shorter, ask for update
        thread_pool.submit(request_for_update, peer, case_id, original_block)


def request_for_update(peer, case_id, original_block):
    if original_block is None:
        data = {"id": case_id, "length": 0, "last": 1}
    else:
        data = {"id": case_id, "length": original_block.length, "last": 1}
    resp = send_block(peer, data, "sync")

    if resp["Status_Code"] == 200:
        resp_json = resp["Answer"]
        blocks = resp_json["Blocks"]
        # Sort by block number
        blocks = sorted(blocks, key=lambda x: x["block_number"])
        
        if original_block is None:
            previous_hash = ""
            last_length = 0
        else:
            previous_hash = original_block.last_verified_hash
            last_length = original_block.length
        for block_json in blocks:
            block_json_id = block_json["id"]
            block_json_previous_hash = block_json["previous_hash"]
            block_json_hash = block_json["hash"]
            block_json_block_number = block_json["block_number"]

            # If case_id does not match
            if case_id != block_json_id:
                continue

            # If previous hash matches current and is the next block
            if previous_hash == block_json_previous_hash and last_length == block_json_block_number:
                if original_block is None:
                    userstoredinfo = UserStoredInfo(case_id, block_json_hash, block_json_block_number + 1)
                    db.session.add(userstoredinfo)
                else:
                    original_block.last_verified_hash = block_json_hash
                    original_block.length = block_json_block_number + 1

                # Increment
                previous_hash = block_json_hash
                last_length += 1
        db.session.commit()


def verify(unverified_block):
    """
    User will perform verification using the information sent by the server and respond with a boolean statement. 
    """
    # unverified block is in json format
    caseid = unverified_block.get('case_id')
    block_num = unverified_block.get('block_number')
    prev_hash = unverified_block.get('previous_block_hash')
    metadata = unverified_block.get('meta_data')
    log = unverified_block.get('log')
    timestamp = unverified_block.get('timestamp')
    block_hash = unverified_block.get('block_hash')
    user_block_info = UserStoredInfo.query.filter_by(case_id=caseid).first()
    if user_block_info.last_verified_hash == prev_hash:
        verifying = caseid + "-" + str(block_num) + "-" + metadata + "-" + log + "-" + str(timestamp) \
                          + "-" + user_block_info.last_verified_hash
        verify_block_hash = hashlib.sha256(verifying.encode()).hexdigest()
        if verify_block_hash == block_hash:
            return 1
        else:
            return 0
    else:
        return 0
