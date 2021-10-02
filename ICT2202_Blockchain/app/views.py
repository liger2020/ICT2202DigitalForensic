from flask import request, jsonify
from app import app, db, controller

# Import module models
from app.controller import object_as_dict
from app.models import Peers, Block

STATUS_OK = 200


@app.route("/")
def index():
    return "Hello world"


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
