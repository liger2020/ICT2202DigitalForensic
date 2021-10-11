import sys
import time
from datetime import datetime

import requests
from flask import request, jsonify

from app import app, db
from app.controller import convert_to_block, get_live_peers, send_block
# Import module models
from app.models import Peers, Block

STATUS_OK = 200


@app.route("/health")
def current_health():
    resp = {"Python_version": sys.version,
            "Platform": sys.platform,
            "Health": "Good"}
    return resp, STATUS_OK


@app.route('/receiveblock', methods=['POST'])
def receive_block():
    # For Info
    num_of_errors = 0

    # Check block need verify
    json_blocks = request.get_json()
    for json_block in json_blocks["Blocks"]:
        # Convert into class object
        block = convert_to_block(json_block)
        if block is None:
            # print("Error processing: {}".format(json_block))
            num_of_errors += 1
            continue

        # Check if verified, add to Database
        # TODO Block missing isverified field
        """ Note: Might have to do a loop here to do a check if verified after the block status is NOT verified"""
        if block.status == "verified": 
            if block.previous_block_hash:
                # Create Block
                # TODO Example of inserting to DB

                db.session.add(block) 
                db.session.commit()
            else:
                # Add to pool
                # TODO
                pass

    # Print extra info
    json_blocks.update({"Errors": num_of_errors})

    return json_blocks, STATUS_OK


@app.route("/getallblocks")
def get_all_blocks():
    blocks = [x.as_dict() for x in Block.query.all()]
    # Convert Object to JSON TODO
    return jsonify(output=blocks), STATUS_OK

# Testing sending block
@app.route("/test")
def test():
    start = time.time()

    # Get peers alive
    live_peers = get_live_peers()

    # Send blocks to peer
    output_list = []
    for peer in live_peers:
        data = {"Blocks": [
            {
                "index": "1",
                "proof_number": "1",
                "previous_block_hash": "",
                "meta_data": ["1", "2", "3"]
            }]
        }

        output_list.append(send_block(peer, data))

    end = time.time()

    return jsonify({"Output": output_list, "Time": end - start})


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
    print(blocks[-1].get('block_hash'))
    # Convert Object to JSON TODO
    return jsonify(output=blocks), STATUS_OK

@app.route("/insertblock")
def insertblock():
    test = Block(1,"test","test",True)
    db.session.add(test)
    db.session.commit()

