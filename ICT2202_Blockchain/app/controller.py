import json

from dateutil import parser
import math
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import requests
from flask import jsonify

from app import db, app, Session
from app.models import Block, Peers, Pool, Consensus

SYNC_INTERVAL = 60 * 10  # 10 Mins
TIMEOUT = 30


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
def convert_to_consensus(json_block, ip_address):
    try:
        consensus = Consensus(ip_address, json_block["pool_id"], json_block["response"])
        return consensus
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


def send_block(peer, data, url):
    url = "http://{}:{}/{}".format(peer.ip_address, peer.port, url)
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post(url, json=data, headers=headers, timeout=3)
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
    # print(delegates)
    return delegates  # List of user to give their consensus.


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


# !!! Native SQLAlchemy Syntax !!!
def check_twothird():
    session = Session()

    # Get all Unverified Blocks
    pool_list = session.query(Pool).all()
    for pool in pool_list:
        if pool.sendout_time is None:
            continue

        # If Unverified block Timed Out, Check all response to check if 2/3
        if pool.sendout_time + timedelta(seconds=TIMEOUT) >= datetime.now():
            # Check if id has 2/3 >, add to block
            numberofpeer = len(Peers.query.all())
            twothird = math.ceil(numberofpeer * 0.66)
            consensus_list = Consensus.query.filter_by(pool_id=pool.id).all()
            number_of_agree = [x for x in consensus_list if x.response]
            if len(number_of_agree) >= twothird:
                # Add to block TODO
                # add_to_block()
                print("2/3  liao")
                # TODO check log action add user

    Session.remove()


# !!! Native SQLAlchemy Syntax !!!
def send_unverified_block():
    session = Session()

    # Every 10 Second
    list_of_unverified = session.query(Pool).order_by(Pool.case_id).all()
    list_of_users = randomselect()
    thread_pool = ThreadPoolExecutor(5)  # 5 Worker Threads
    for block in list_of_unverified:
        data = {"Pool": [{"id": block.id, "case_id": block.case_id, "meta_data": block.meta_data, "log": block.log,
                          "timestamp": str(block.timestamp),
                          "previous_block_hash": block.previous_block_hash, "block_hash": block.block_hash}]
                }
        if block.sendout_time is None:
            block.sendout_time = datetime.now()
            block.count = 0
            session.commit()
            for peer in list_of_users:
                thread_pool.submit(send_block, peer, data, "receivepool")  # send block to user
        else:
            if block.count < 3:
                block.count += 1  # increment count
                if (block.sendout_time + timedelta(seconds=TIMEOUT)) <= datetime.now():
                    block.sendout_time = datetime.now()
                    session.commit()

                    for peer in list_of_users:
                        thread_pool.submit(send_block, peer, data, "receivepool")  # send block to user
            else:
                session.delete(block)
                consensus_list = session.query(Consensus).filter(Consensus.pool_id == block.id).all()
                for remove_consensus in consensus_list:
                    session.delete(remove_consensus)
                session.commit()

    Session.remove()

# send_unverified_block()
# verify()
# randomselect()

a = peers
send_block(, "5000","/api/test")

