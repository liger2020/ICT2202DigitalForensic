"""
Functions to be called
"""
import hashlib
import json
import math
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

import requests
from dateutil import parser

from app import db, Session
from app.models import Block, Peers, Pool, Consensus, UserCase

SYNC_INTERVAL = 60 * 10  # 10 Mins
TIMEOUT = 30


def convert_to_block(json_block):
    try:
        timestamp = json_block.get("timestamp")
        if timestamp is not None:
            timestamp = parser.parse(json_block["timestamp"])

        block = Block(json_block["id"], json.dumps(json_block["meta_data"]), json.dumps(json_block["log"]),
                      block_number=json_block.get("block_number"),
                      previous_block_hash=json_block.get("previous_block_hash"), timestamp=timestamp,
                      block_hash=json_block.get("block_hash"), status=json_block.get("status"))
        return block
    except KeyError():
        return None


def convert_to_pool(json_block):
    try:
        block = Pool(json_block["case_id"], json.dumps(json_block["meta_data"]), json.dumps(json_block["log"]))
        if "block_number" in json_block and "previous_block_hash" in json_block and "timestamp" in json_block and "block_hash" in json_block:
            block.case_id = json_block["case_id"]
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


def convert_to_consensus(json_block, ip_address):
    try:
        consensus = Consensus(ip_address, json_block["pool_id"], json_block["response"])
        return consensus
    except KeyError:
        return None
    except TypeError:
        return None


def check_health(peer):
    """Return response of target

    Check if the target machine is online by requesting from "/health" on the machine

    :param peer: Peer object of the target
    :type peer: Peers
    :returns:
        - Online - Target Peer
        - Offline - None
    :rtype: Peers
    """
    try:
        resp = requests.get("http://{}:{}/health".format(peer.ip_address, peer.port), timeout=3)
        if resp.status_code == 200:
            return peer

        return None
    except:
        return None


def get_live_peers(servertype):
    """Returns list of online

    Returns a list of all peers that is online from the database.

    :param servertype: "server"/"client" to check
    :type servertype: str
    :return: List of All Peers that is online
    :rtype: list
    """
    # Check peers alive
    live_peers = []
    futures = []

    pool = ThreadPoolExecutor(5)  # 5 Worker Threads

    # Get all peer's ip address and port from DB
    peer_list = Peers.query.filter_by(server_type=servertype).all()

    # Use check_health() to get whether machine online
    for peer in peer_list:
        futures.append(pool.submit(check_health, peer))

    for x in as_completed(futures):
        result = x.result()
        if result is not None:
            live_peers.append(result)

    return live_peers


def send_block(peer, data, url):
    """
    A function to send data to target

    :param peer: Machine to sent to
    :type peer: Peers
    :param data: Json data to be sent
    :type data: dict
    :param url: The target link to be sent to
    :type url: str
    :return: The response of the request sent
    :rtype:
        - "get" - Response
        - "post" - dict
    """
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


'''
User will store Case id and the last block hash of the respective cases they are in.
When verification is needed, the server will select 51 percent of the people in the case.
These delegates will then verify the hash of the block and return a yes/no respond to the server.
'''


def randomselect():
    """
    This function will select 51 percent of the user in the system for verification of the block
    """
    peer_list = Peers.query.all()
    numberofpeer = len(peer_list)
    fiftyone = math.ceil(numberofpeer * 0.51)
    delegates = random.sample(peer_list, fiftyone)
    return delegates  # List of user to give their consensus.


def sync_schedule():
    """
    Syncing scheduled to run frequently to ensure the database is updated with other nodes
    """
    live_peers = get_live_peers("server")
    for peer in live_peers:
        # Ask for his length
        resp = send_block(peer, "", "sync")
        if resp.status_code != 200:
            continue

        resp_json = resp.json()
        # Make sure json is valid
        if "Blocks" not in resp_json:
            continue

        # Check length received
        for length_json in resp_json.get("Blocks"):
            # Make sure json is valid
            if "id" not in length_json or "length" not in length_json or "last" not in length_json:
                continue

            case_id = length_json["id"]
            block_count = Block.query.filter_by(id=case_id).count()
            last_hash_block = Block.query.filter_by(id=case_id) \
                .order_by(Block.block_number.desc()) \
                .first()
            if last_hash_block is None:
                last_hash = ""
            else:
                last_hash = last_hash_block.block_hash

            # Check if longer
            if length_json["length"] <= block_count:
                continue

            resp = send_block(peer, {"id": case_id, "length": block_count, "last": last_hash}, "sync")

            if resp["Status_Code"] == 200:
                resp_json = resp["Answer"]
                for block_json in resp_json.get("Blocks"):
                    block = convert_to_block(block_json)
                    db.session.add(block)

                # If verified add to block, else discard
                if verify(case_id):
                    db.session.commit()
                else:
                    db.session.rollback()


def send_new_verified_to_clients(add_the_block):
    """
    Sends new blocks to all clients.

    :param add_the_block: The new verified block
    :type add_the_block: Block
    """
    pool = ThreadPoolExecutor(5)  # 5 Worker Threads

    data = {
        "case_id": add_the_block.id,
        "previous_hash": add_the_block.previous_block_hash,
        "last_verified_hash": add_the_block.block_hash,
        "length": add_the_block.block_number + 1
    }
    client_list = Peers.query.filter_by(server_type="client").all()
    for client in client_list:
        pool.submit(send_block, client, data, "sync")


# !!! Native SQLAlchemy Syntax !!!
def check_twothird():
    """
    A scheduled function to check if unverified block have meet the requirements and those that meet the requirements
    gets added as a block
    """
    session = Session()

    # Get all Unverified Blocks
    pool_list = session.query(Pool).all()
    for pool in pool_list:
        if pool.sendout_time is None:
            continue

        # If Unverified block Timed Out, Check all response to check if 2/3
        if pool.sendout_time + timedelta(seconds=TIMEOUT) >= datetime.now():
            # Check if id has 2/3 >, add to block
            numberofpeer = len(session.query(Peers).filter(Peers.server_type == "client").all())
            selectnumber = math.ceil(numberofpeer * 0.51)
            twothird = math.ceil(selectnumber * 0.66)
            consensus_list = session.query(Consensus) \
                .filter(Consensus.pool_id == pool.id, Consensus.response == 1) \
                .all()
            number_of_consensuses = [x for x in consensus_list if x.response]
            if len(number_of_consensuses) >= twothird:
                verified_block = session.query(Pool).filter(Pool.id == pool.id).first()
                temp = verified_block.case_id  # Store a temp value

                add_the_block = Block(
                    id=verified_block.case_id,
                    meta_data=verified_block.meta_data,
                    log=verified_block.log,
                    block_hash=verified_block.block_hash,
                    timestamp=verified_block.timestamp,
                    status=1
                )

                session.add(add_the_block)
                remove_old_pool = session.query(Pool).filter(Pool.id == verified_block.id).first()
                session.delete(remove_old_pool)
                consensus_list = session.query(Consensus).filter(Consensus.pool_id == verified_block.id).all()
                for remove_consensus in consensus_list:
                    session.delete(remove_consensus)
                session.commit()

                # Resetting the count of the pool after the previous pool is verified
                update_pool = session.query(Pool).filter(Pool.case_id == temp).all()

                last_hash_block = Block.query.filter_by(id=temp).order_by(Block.block_number.desc()).first()
                if update_pool is not None:
                    for all_pool in update_pool:
                        all_consensus = session.query(Consensus).filter(Consensus.pool_id == all_pool.id).all()
                        # Changing the first block in the pool with same case ID with the latest block's black_hash
                        for x in all_consensus:
                            session.delete(x)

                        all_pool.previous_block_hash = last_hash_block.block_hash
                        all_pool.block_number = last_hash_block.block_number + 1
                        block_data = all_pool.case_id + "-" + str(all_pool.block_number) + "-" + all_pool.meta_data + \
                                     "-" + all_pool.log + "-" + str(all_pool.timestamp) + "-" + all_pool.previous_block_hash

                        all_pool.block_hash = hashlib.sha256(block_data.encode()).hexdigest()
                        all_pool.sendout_time = None
                        all_pool.count = 0

                        session.commit()

                # Sending new verified blocks to clients
                send_new_verified_to_clients(add_the_block)

                # commiting to Meta_Data_File table
                # sql = Meta_Data_File(case_id=verified_block.case_id, meta_data=verified_block.meta_data.File_Name)
                # session.add(sql)
                # session.commit()

                # Load string as json
                # metadata_json = json.loads(verified_block.meta_data)
                log_json = json.loads(verified_block.log)

                # Check log action add user
                if "AddUser" == log_json["Action"]:
                    user_list = log_json["Username"]
                    for user in user_list:
                        # Check exist
                        test = session.query(UserCase) \
                            .filter(UserCase.username == user, UserCase.case_id == verified_block.case_id) \
                            .first()
                        if test is not None:
                            continue

                        # Add User to case
                        usercase = UserCase(user, verified_block.case_id)
                        session.add(usercase)
                    session.commit()

    Session.remove()


def verify(case_id):
    """
    A function used to verify if the case id exist in the system. 
    """
    blocks = Block.query.filter_by(id=case_id).order_by(Block.block_number.asc()).all()
    previous_block_hash = ""
    for block in blocks:
        if previous_block_hash != block.previous_block_hash:
            return False

        data = block.id + "-" + str(block.block_number) + "-" + block.meta_data + "-" + block.log + "-" + \
               str(block.timestamp) + "-" + block.previous_block_hash
        block_hash = hashlib.sha256(data.encode()).hexdigest()
        if block_hash != block.block_hash:
            return False
        previous_block_hash = block_hash
    return True


# !!! Native SQLAlchemy Syntax !!!
def send_unverified_block():
    """
    A scheduled function that sends unverified blocks in the pool to the selected delegates for them to vote if the block should be added to the 
    block. 
    """
    session = Session()

    # Every 10 Second
    list_of_unverified = session.query(Pool).order_by(Pool.case_id).all()
    list_of_users = randomselect()
    thread_pool = ThreadPoolExecutor(5)  # 5 Worker Threads
    for block in list_of_unverified:
        data = {"Pool": [
            {"id": block.id, "case_id": block.case_id, "block_number": block.block_number, "meta_data": block.meta_data,
             "log": block.log,
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
            if block.status:
                pass
                # interrupt schedule and move on
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
