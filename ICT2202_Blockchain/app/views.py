import math
import sys
import time
import datetime

import requests
from flask import request, jsonify

from app import app, db
from app.controller import convert_to_block, get_live_peers, send_block, convert_to_pool, convert_to_consesus
# Import module models
from app.models import Peers, Block, Pool, Consesus

STATUS_OK = 200
STATUS_NOT_FOUND = 404
TIMEOUT = 60 * 15


@app.route("/health")
def current_health():
    resp = {"Python_version": sys.version,
            "Platform": sys.platform,
            "Health": "Good"}
    return resp, STATUS_OK


# Assuming unverified
@app.route('/receiveblock', methods=['POST'])
def receive_block():
    # For Info
    num_of_errors = 0

    # Check block need verify
    json_blocks = request.get_json()
    for json_block in json_blocks["Pool"]:
        # Convert into class object
        block = convert_to_pool(json_block)
        # print(block)
        if block is None:
            # print("Error processing: {}".format(json_block))
            num_of_errors += 1
            continue

        # Add to Pool
        db.session.add(block)
        db.session.commit()

    # Print extra info
    json_blocks.update({"Errors": num_of_errors})
    return json_blocks, STATUS_OK


@app.route('/receive_response', methods=['POST'])
def receive_response():
    # Placeholder Expected Input: {"pool_id": "2", "response": "yes"}
    # Process Json to Consensus Model Object
    resp = request.get_json()
    consesus = convert_to_consesus(resp, request.remote_addr)
    if consesus is None:
        # TODO return error code
        return {"error": "very true"}

    # Check Timeout
    pool = Pool.query.filter_by(id=consesus.pool_id).first()
    response_timestamp = pool.sendout_time
    if (response_timestamp + datetime.timedelta(seconds=TIMEOUT)) >= datetime.datetime.now():
        # Add to Consesus Table TODO Add checks
        db.session.add(consesus)
        db.session.commit()
    else:
        # Discard (TIMED OUT)
        pass

    # Check if id has 2/3 >, add to block
    numberofpeer = len(Peers.query.all())
    twothird = math.ceil(numberofpeer * 0.66)
    if len(Consesus.query.filter_by(pool_id=consesus.pool_id).all()) >= twothird:
        # Add to block TODO
        # add_to_block()
        print("2/3  liao")
        pass

    return {"Responding From": "/receive_response"}, STATUS_OK


# @app.route("/getallblocks")
# def get_all_blocks():
#     blocks = [x.as_dict() for x in Block.query.all()]
#     # Convert Object to JSON TODO
#     return jsonify(output=blocks), STATUS_OK


# Testing sending block
# @app.route("/test")
# def test():
#     start = time.time()
#
#     # Get peers alive
#     live_peers = get_live_peers()
#
#     # Send blocks to peer
#     output_list = []
#     for peer in live_peers:
#         data = {"Blocks": [
#             {
#                 "index": "1",
#                 "proof_number": "1",
#                 "previous_block_hash": "",
#                 "meta_data": ["1", "2", "3"]
#             }]
#         }
#
#         output_list.append(send_block(peer, data))
#
#     end = time.time()
#
#     return jsonify({"Output": output_list, "Time": end - start})


@app.route('/sync')
def sync():
    output = []
    id_list = Block.query.with_entities(Block.id).distinct()
    for case_id in id_list:
        case_id = case_id[0]  # IDK why
        length = Block.query.filter_by(id=case_id).count()  # Get length of ID
        output.append({"id": case_id, "length": length})
    return jsonify(Blocks=output)


# Syncing blockchain, request length of id, if longer send all blocks above length (Honestly cutting corners here)
@app.route('/sync', methods=['POST'])
def sync_receive():
    resp = request.get_json()
    # Make sure json is valid
    if "id" not in resp or "length" not in resp or "last" not in resp:
        return "", STATUS_NOT_FOUND

    resp_id = resp["id"]
    resp_length = resp["length"]
    resp_last = resp["last"] == 1
    output_list = []
    block_list_count = 0
    length = Block.query.filter_by(id=resp_id).count()  # Get length of ID

    # If length is longer then sender, send blocks
    if length > resp_length:
        if resp_last:
            # Get last block only (For Client)
            last_block = Block.query.filter(Block.id == resp_id, Block.block_number >= resp_length).order_by(
                Block.block_number.desc()).first()
            data = last_block.as_dict()
            output_list.append(data)
        else:
            # Get all blocks above length (For Nodes)
            block_list = Block.query.filter(Block.id == resp_id, Block.block_number >= resp_length).order_by(
                Block.block_number.desc())
            block_list_count = Block.query.filter(Block.block_number >= resp_length).count()  # For printing only
            for block in block_list:
                data = block.as_dict()
                output_list.append(data)
    return jsonify({"Blocks": output_list, "length": length, "Count": block_list_count})


# TODO Auth for sensitive functions (API Keys)
# Getting Data From Database
@app.route('/peers/<peer_ip_address>', methods=['GET'])
def get_peers(peer_ip_address):
    peer = Peers.query.filter_by(ip_address=str(peer_ip_address)).first_or_404()
    return peer.as_dict()


@app.route('/peers', methods=['PUT'])
def create_peers():
    peer = request.get_json()
    if "ip_address" not in peer or "port" not in peer:
        return 404

    peer_obj = Peers(peer["ip_address"], peer["port"])
    db.session.add(peer_obj)
    db.session.commit()

    return peer_obj.as_dict(), STATUS_OK


@app.route('/peers', methods=['POST'])
def update_peers():
    peer = request.get_json()
    if "id" not in peer or "ip_address" not in peer or "port" not in peer:
        return 404

    peer_obj = Peers.query.filter_by(id=peer["id"]).first()
    peer_obj.ip_address = peer["ip_address"]
    peer_obj.port = peer["port"]

    db.session.commit()

    return peer, STATUS_OK


@app.route('/peers/<peer_ip_address>', methods=['DELETE'])
def delete_peers(peer_ip_address):
    peer = Peers.query.filter_by(ip_address=str(peer_ip_address)).first_or_404()
    db.session.delete(peer)
    db.session.commit()

    return peer.as_dict(), STATUS_OK


@app.route("/getlastblocks")
def getlastblocks():
    blocks = [x.as_dict() for x in Block.query.all()]
    for block in blocks:
        print(block)
    # Convert Object to JSON TODO
    return jsonify(output=blocks), STATUS_OK


@app.route("/insertblock")
def insertblock():
    blocks = [x.as_dict() for x in Block.query.all()]
    # case_id = blocks[-1].get('id')
    # block_number = blocks[-1].get('block_number') + 1
    # block_hash =  blocks[-1].get('block_hash')
    # time_stamp = blocks[-1].get('timestamp')
    # test = Block(1, meta_data="test", log="test", status=True)
    test = Pool(1, meta_data="test", log="test")
    db.session.add(test)
    db.session.commit()

    return jsonify(output=test), STATUS_OK


@app.route("/query")
def check_query():
    queries = Block.query.filter_by(id=1).all()
    for query in queries:
        print(query)

    return str(query), STATUS_OK
