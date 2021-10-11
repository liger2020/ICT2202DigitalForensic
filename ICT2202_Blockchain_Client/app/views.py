import sys

from flask import request

from app import app, db
from app.controller import convert_to_block

STATUS_OK = 200
STATUS_NOT_FOUND = 404


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
        if block.status:
            if block.previous_block_hash:
                # Create Block
                db.session.add(block)
                db.session.commit()
            else:
                # Add to pool
                # TODO
                pass

    # Print extra info
    json_blocks.update({"Errors": num_of_errors})

    return json_blocks, STATUS_OK