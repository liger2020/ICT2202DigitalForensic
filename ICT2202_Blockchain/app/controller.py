import json

import hashlib
from dateutil import parser
import math
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import requests
from flask import jsonify

from app import db, app, Session
from app.models import Block, Peers, Pool, Consensus, UserCase, MetaDataFile

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
        block = Pool(json_block["case_id"], json_block["meta_data"], json_block["log"])
        if "block_number" in json_block and "previous_block_hash" in json_block and "timestamp" in json_block and "block_hash" in json_block:
            block.id = json_block["case_id"]
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


def get_live_peers(servertype):
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
    url = "http://{}:{}/{}".format(peer.ip_address, peer.port, url)
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain', "Authorization": "Bearer secret-token-1"}
    print(data)
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
    peer_list = Peers.query.all()
    numberofpeer = len(peer_list)
    fiftyone = math.ceil(numberofpeer * 0.51)
    delegates = random.sample(peer_list, fiftyone)
    # print(delegates)
    return delegates  # List of user to give their consensus.


def sync_schedule():
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
        for length_json in resp_json["Blocks"]:
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
                for block_json in resp_json["Blocks"]:
                    block = convert_to_block(block_json)
                    db.session.add(block)

                # If verified add to block, else discard
                if verify(case_id):
                    db.session.commit()
                else:
                    db.session.rollback()


def send_new_verified_to_clients(add_the_block):
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
            print("This is the number of peer:", str(numberofpeer))
            selectnumber = math.ceil(numberofpeer * 0.51)
            print("This is the select number:", str(selectnumber))
            twothird = math.ceil(selectnumber * 0.66)
            print("This is the deciding factor number:", twothird)
            print("This is the pool id:", str(pool.id))
            consensus_list = session.query(Consensus).filter(Consensus.pool_id == pool.id).all()
            print(consensus_list)
            print(type(consensus_list))
            number_of_consensuses = [x for x in consensus_list if x.response]
            if len(number_of_consensuses) >= twothird:
                verified_block = session.query(Pool).filter(Pool.id == pool.id).first()
                print("Case ID:", str(verified_block.case_id))
                print("Block number:", str(verified_block.block_number))
                print("meta data:", verified_block.meta_data)
                print("log:", verified_block.log)
                print("last verified hash: ", str(verified_block.previous_block_hash))
                print("timestamp:", str(verified_block.timestamp))
                print("Just verified block:", str(verified_block.block_hash))
                # verified_block.status = 1
                # session.commit()

                # DO NOT DELETE
                add_the_block = Block(
                    id=verified_block.case_id,
                    # block_number=verified_block.block_number,
                    # previous_block_hash=send_unverified_block.previous_block_hash,
                    meta_data=verified_block.meta_data,
                    log=verified_block.log
                    # timestamp=send_unverified_block.timestamp,
                    # block_hash=send_unverified_block.block_hash,
                    # status=1,
                )

                add_the_block.block_hash = verified_block.block_hash
                add_the_block.timestamp = verified_block.timestamp
                add_the_block.status = 1

                session.add(add_the_block)
                remove_old_pool = session.query(Pool).filter(Pool.id == verified_block.id).first()
                session.delete(remove_old_pool)
                consensus_list = session.query(Consensus).filter(Consensus.pool_id == verified_block.id).all()
                for remove_consensus in consensus_list:
                    session.delete(remove_consensus)
                session.commit()

                #Resetting the count of the pool after the previous pool is verified
                # update_pool = session.query(Pool).filter(Pool.case_id == verified_block.case_id).all()
                # if update_pool is None:
                #     pass
                # else:
                #     for all in update_pool:
                #         all.count = 0
                #     session.commit()  

                #     #Changing the first block in the pool with same case ID with the latest block's black_hash
                #     get_new_first_pool = session.query(Pool).filter(Pool.case_id == verified_block.case_id).first()  
                #     last_hash_block = Block.query.filter_by(id=verified_block.case_id).order_by(Block.block_number.desc()).first()
                #     get_new_first_pool.previous_block_hash = last_hash_block.block_hash
                #     session.commit()

                
                # Sending new verified blocks to clients
                send_new_verified_to_clients(add_the_block)

                # commiting to Meta_Data_File table
                # sql = Meta_Data_File(case_id=verified_block.case_id, meta_data=verified_block.meta_data.File_Name)
                # session.add(sql)
                # session.commit()

                # TODO I edited here...
                # Load string as json
                metadata_json = json.loads(verified_block.meta_data)
                log_json = json.loads(verified_block.log)

                # commiting to MetaDataFile table
                queryMeta = session.query(MetaDataFile).filter(MetaDataFile.case_id == verified_block.case_id).first()
                if queryMeta:
                     queryMeta.meta_data += "," + metadata_json["File_Name"]
                else:
                    sqlmeta = metadata_json["File_Name"]
                    sql = MetaDataFile(case_id=verified_block.case_id, meta_data=sqlmeta)
                    session.add(sql)
                session.commit()

                # Check log action add user
                if "AddUser" == log_json["Action"]:
                    user_list = log_json["Username"]
                    for user in user_list:
                        print(user)
                        # Check exist
                        test = session.query(UserCase).filter(UserCase.username == user, UserCase.case_id == verified_block.case_id).first()
                        if test is not None:
                            continue

                        # Add User to case
                        usercase = UserCase(user, verified_block.case_id)
                        session.add(usercase)
                    session.commit()
                elif "RemoveUser" == log_json["Action"]:
                    usercase = session.query(UserCase) \
                        .filter(UserCase.username == log_json["Username"], UserCase.case_id == verified_block.case_id) \
                        .first()
                    session.delete(usercase)

            # else:
            #     print("Fail")

    Session.remove()


def verify(case_id):
    blocks = Block.query.filter_by(id=case_id).order_by(Block.block_number.asc()).all()
    previous_block_hash = ""
    for block in blocks:
        if previous_block_hash != block.previous_block_hash:
            return False

        data = "-".join(block.meta_data) + "-".join(block.log) + "-" + str(block.timestamp) \
               + "-" + block.previous_block_hash
        block_hash = hashlib.sha256(data.encode()).hexdigest()
        if block_hash != block.block_hash:
            return False
        previous_block_hash = block_hash
    return True


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

# send_unverified_block()
# print(verify("1"))
# randomselect()


# a = Peers("192.168.75.133", 5000)
# print(a.as_dict())
# print(send_block(a, "", "/api/test"))
