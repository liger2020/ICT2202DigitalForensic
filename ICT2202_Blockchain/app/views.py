from flask import request

from app import app, mysql, Block

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
        block = Block.convert_to_block(json_block)
        if block is None:
            # print("Error processing: {}".format(json_block))
            num_of_errors += 1
            continue

        # Check if verified, add to Database
        if block.isverified:
            # Create Block
            # TODO
            pass
        else:
            # Add to pool
            # TODO
            pass

    # Print extra info
    json_blocks.update({"Errors": num_of_errors})

    return json_blocks, STATUS_OK
