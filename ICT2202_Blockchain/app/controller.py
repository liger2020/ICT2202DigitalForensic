from dateutil import parser
import math
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import requests

from app import db
from app.models import Block, Peers, Pool, Consesus

SYNC_INTERVAL = 60 * 10  # 10 Mins


def convert_to_block(json_block):
    try:
        block = Block(json_block["id"], json_block["meta_data"], json_block["log"])
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


def convert_to_pool(json_block):
    try:
        pool = Pool(json_block["id"], json_block["meta_data"], json_block["log"])
        if "block_number" in json_block and "previous_block_hash" in json_block and "timestamp" in json_block and "block_hash" in json_block:
            pool.id = json_block["id"]
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

# Placeholder TODO
def convert_to_consesus(json_block, ip_address):
    try:
        consesus = Consesus(ip_address, json_block["pool_id"], json_block["response"])
        return consesus
    except KeyError:
        return None
    except TypeError:
        return None

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


def send_block(peer, data):
    url = "http://{}:{}/receiveblock".format(peer.ip_address, peer.port)
    r = requests.post(url, json=data)
    output = {"Peer": url,
              "Answer": r.json(),
              "Status_Code": r.status_code
              }

    return output


'''
User will store Case id and the last block hash of the respective cases they are in.
When verification is needed, the server will select 51 percent of the people in the case. 
These delegates will then verify the hash of the block and return a yes/no respond to the server.
'''


def randomselect():
    peer_list = Peers.query.all()
    numberofpeer = len(peer_list)
    fiftyone = math.ceil(numberofpeer * 0.51)
    delegates = random.sample(peer_list, fiftyone)
    print(delegates)
    return delegates  # List of user to give their consensus.


def verify():
    chosen_ones = randomselect()
    send_unverified_block()
    #how to send to the user? 
    blocks = [x.as_dict() for x in Block.query.all()]
    last_block = blocks[-1].get('block_hash')
    case_id = blocks[-1].get('id')

    # Check if last block's hash matches user's
    if case_id == 1:  # Let the value 1 be case id value stored in user side.
        if last_block == "123":  # Let 123 be last block hash stored in user side.
            print("Yes")  # consensus is send to the speaker
        else:
            print("No")  # consensus is send to the speaker
    else:
        None


def sync_schedule():
    live_peers = get_live_peers()
    for peer in live_peers:
        # Ask for his length
        resp = requests.get("http://{}:{}/sync".format(peer.ip_address, peer.port))
        if resp.status_code != 200:
            continue

        resp_json = resp.json()
        # Make sure json is valid
        if "Blocks" not in resp_json:
            continue

        # Check length received
        for length_json in resp_json["Blocks"]:
            # Make sure json is valid
            if "id" not in length_json or "length" not in length_json:
                continue

            case_id = length_json["id"]
            block_count = Block.query.filter_by(id=case_id).count()
            # Check if longer
            if length_json["length"] <= block_count:
                continue

            resp = requests.post("http://{}:{}/sync".format(peer.ip_address, peer.port),
                                 json={"id": case_id, "length": block_count}, timeout=3)

            if resp.status_code == 200:
                resp_json = resp.json()
                for block_json in resp_json["Blocks"]:
                    block = convert_to_block(block_json)
                    db.session.add(block)
                db.session.commit()

def send_unverified_block():
    # Every 10 Second
    futures = []
    list_of_unverified = [x.as_dict() for x in Pool.query.order_by('case_id')]
    list_of_users = randomselect()
    pool = ThreadPoolExecutor(5)  # 5 Worker Threads
    for unverified_block in list_of_unverified:
        block = convert_to_pool(unverified_block)
        #data = block.case_id, block.meta_data, block.log, block.previous_block_hash, block.block_hash
        count = block.count
        print(block.sendout_time)
        if block.sendout_time is None:        
            block.sendout_time = datetime.now()
            db.session.commit()
            print(block.sendout_time)
            # for peer in list_of_users:
            #     futures.append(pool.submit(send_block, peer, data)) #send block to user
            #check if user belong to case (dk how to check)
            count += 1 #increment count 
        else:
            pass 
            #
    #     If send_timestamp is not None, send_timestamp + TIMEOUT <= date.now(), count += 1;
    db.session.commit()
        # Send to user
        # futures.append(pool.submit(send_block, peer, data))
        # unveri set send send_timestamp


send_unverified_block()
# verify()
# randomselect()
