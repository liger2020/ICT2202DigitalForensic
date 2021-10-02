import time

import requests
from flask import request, jsonify
from app import app, db, controller
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

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
        block = controller.convert_to_block(json_block)
        if block is None:
            # print("Error processing: {}".format(json_block))
            num_of_errors += 1
            continue

        # Check if verified, add to Database
        if block.isverified:
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
    blocks = Block.query.all()
    # Convert Object to JSON TODO
    return ""


# Testing sending block
@app.route("/test")
def test():
    start = time.time()

    # Check peers alive
    live_peers = []
    pool = ThreadPoolExecutor(5)
    futures = []
    peer_list = Peers.query.all()
    for peer in peer_list:
        futures.append(pool.submit(controller.check_health, peer.ip_address, peer.port))

    for x in as_completed(futures):
        result = x.result()
        if result is not None:
            live_peers.append(result)

    # Send blocks to peer
    for (ip_address, port) in live_peers:
        data = {"Blocks": [
            {
                "ID": "1",
                "Comment": "This is a comment",
                "Amount": "23.21",
                "Verified": "False"
            }]
        }

        r = requests.post("http://{}:{}/receiveblock".format(ip_address, port), json=data)
        print(r.json())
        print(r.status_code)

    end = time.time()

    return jsonify({"Alive": live_peers, "Time": end - start})
