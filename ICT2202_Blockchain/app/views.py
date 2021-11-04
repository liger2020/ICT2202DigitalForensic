"""
views.py
========
The webpage routing of flask server
"""
import datetime
import sys

from flask import request, jsonify

from app import app, db, auth
from app.controller import convert_to_pool, convert_to_consensus, verify, send_new_verified_to_clients
from app.models import Block, Pool, Consensus, UserCase

STATUS_OK = 200
STATUS_NOT_FOUND = 404
TIMEOUT = 60 * 15

tokens = {
    "secret-token-1": "john",
    "secret-token-2": "susan"
}


@app.route("/health")
def current_health():
    """
    Return health of current server

    :return: Python version, Platform and Health
    :rtype:
        - dict
        - Status 200
    """
    resp = {"Python_version": sys.version,
            "Platform": sys.platform,
            "Health": "Good"}
    return resp, STATUS_OK


# Assuming unverified
@app.route('/receiveblock', methods=['POST'])
@auth.login_required
def receive_block():
    """
    Server to receive blocks from server

    :return: Show input receives by server
    :rtype: json, Status 200
    """
    num_of_errors = 0

    # Check block need verify
    json_blocks = request.get_json()
    for json_block in json_blocks["Pool"]:

        # Convert into class object
        block = convert_to_pool(json_block)
        if block is None:
            ("Error processing: {}".format(json_block))
            num_of_errors += 1
            continue

        # If case doesnt exist (Block 0) add to block directly
        exist = Block.query.filter_by(id=block.case_id).first()
        if exist is None:
            # Add to Block
            new_block = Block(block.case_id, block.meta_data, block.log, block_number=block.block_number,
                              previous_block_hash=block.previous_block_hash, timestamp=block.timestamp,
                              block_hash=block.block_hash, status=1)
            db.session.add(new_block)
            db.session.commit()

            # Sending new verified blocks to clients
            send_new_verified_to_clients(new_block)
        else:
            # Add to Pool
            db.session.add(block)
            db.session.commit()

    # Print extra info
    json_blocks.update({"Errors": num_of_errors})
    return json_blocks, STATUS_OK


@app.route('/receive_response', methods=['POST'])
@auth.login_required
def receive_response():
    # Placeholder Expected Input: {"pool_id": "2", "response": "yes"}
    # Process Json to Consensus Model Object\
    """
    This function will receive the response sent by the delegates (client) 

    :return: Give a response whether the code runs smoothly 
    :rtype:
        - "Error Occurred" - str 
        - "Responding from" - Dict 
    """
    resp = request.get_json()
    consensus = convert_to_consensus(resp, request.remote_addr)
    if consensus is None:
        return "Error Occurred!"

    # Check Timeout
    pool = Pool.query.filter_by(id=consensus.pool_id).first()
    if pool is not None:
        response_timestamp = pool.sendout_time
        try:
            if (response_timestamp + datetime.timedelta(seconds=TIMEOUT)) >= datetime.datetime.now():
                # Add to consensus Table
                consent = Consensus.query.filter_by(ip_address=consensus.ip_address, pool_id=consensus.pool_id).first()
                if consent is None:
                    db.session.add(consensus)
                    db.session.commit()
                else:
                    consent.response = consensus.response
                    consent.receive_timestamp = consensus.receive_timestamp
                    db.session.commit()
            else:
                # Discard (TIMED OUT)
                pass
        except:
            pass
    return {"Responding From": "/receive_response"}, STATUS_OK


@app.route('/sync')
@auth.login_required
def sync():
    """
    Return the length of blockchain for syncing

    :return: Case ID's length and last_hash
    :rtype: json
    """
    output = []
    id_list = Block.query.with_entities(Block.id).distinct()
    for case_id in id_list:
        case_id = case_id[0]  # IDK why
        length = Block.query.filter_by(id=case_id).count()  # Get length of ID
        last_hash = Block.query.filter_by(id=case_id) \
            .order_by(Block.block_number.desc()) \
            .first()
        output.append({"id": case_id, "length": length, "last": last_hash.block_hash})
    return jsonify(Blocks=output)


# Syncing blockchain, request length of id, if longer send all blocks above length (Honestly cutting corners here)
@app.route('/sync', methods=['POST'])
@auth.login_required
def sync_receive():
    """
    Send missing blocks back to the machine requesting it

    :return: Blocks missing, Length of Blockchain and Number of blocks sending
    :rtype: json
    """
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
            # Get send previous hash also (For Client)
            block_list = Block.query.filter(Block.id == resp_id, Block.block_number >= resp_length).order_by(
                Block.block_number.desc()).all()
            for block in block_list:
                data = {
                    "id": block.id,
                    "previous_hash": block.previous_block_hash,
                    "hash": block.block_hash,
                    "block_number": block.block_number
                }
                output_list.append(data)
        else:
            # Get all blocks above length (For Nodes)
            block_list = Block.query.filter(Block.id == resp_id, Block.block_number >= resp_length) \
                .order_by(Block.block_number.desc())
            block_list_count = Block.query.filter(Block.block_number >= resp_length).count()  # For printing only
            for block in block_list:
                data = block.as_dict()
                output_list.append(data)
    return jsonify({"Blocks": output_list, "length": length, "Count": block_list_count})


# Getting Data From Database
@app.route('/usercase', methods=['POST'])
@auth.login_required
def get_peers():
    """
    Returns list of assigned cases of the user

    :return: List of caseid
    :rtype:
        - Success - list, 200
        - Failure - str, 404
    """
    case_list = set()

    post_data = request.get_json()
    if "Username" not in post_data:
        return "", STATUS_NOT_FOUND

    username = post_data["Username"]
    # Get all cases with username
    usercase_list = UserCase.query.filter_by(username=str(username)).all()
    if len(usercase_list) > 0:
        for case in usercase_list:
            case_id = case.case_id

            # Double check case_id blockchain is verified
            if verify(case_id):
                case_list.add(case_id)
            else:
                return "Blockchain Verification Failed", STATUS_NOT_FOUND
        return jsonify({"Cases": sorted(list(case_list))}), STATUS_OK
    else:
        # No Cases Found
        return "", STATUS_OK


@auth.verify_token
def verify_token(token):
    """
    Compare token with the authorized token in the dictionary tokens and return the username of the token if found

    :param token: A token for authentication
    :type token: str
    :return: The username that belong to the token
    :rtype:
        - Success - str, username
    """
    if token in tokens:
        return tokens[token]


@app.route('/userAssignedCase', methods=['POST'])
@auth.login_required
def assignedCase():
    """
    Return a dictionary of case assigned to user filter by username

    :return: List of caseid
    :rtype:
        - Success - dictionary, 200
        - Failure - str, fail

    """
    # For testing: curl -i -X POST -H "Content-Type:application/json" -H "Authorization:Bearer secret-token-1" http://{your ip}:5000/userAssignedCase -d {\"username\":\"test2\"}
    username = request.json.get('username')
    if username is None:
        return "failed, username is None"
    query = UserCase.query.filter_by(username=username).all()
    query = [x.as_dict() for x in query]
    if query:
        return jsonify(query)
    return "fail"


@app.route('/caseinfo', methods=['POST'])
@auth.login_required
def caseinfo():
    """
    Return dictionary fill with rows of block info from Block database filter by case_id

    :return: dictionary of rows of block
    :rtype:
        - Success - dictionary, 200
        - Failure - str, "fail, cannot find case_id"
    """
    #For testing: curl -i -X POST -H "Content-Type:application/json" -H "Authorization:Bearer secret-token-1" http://{your ip }:5000/caseinfo -d {\"case_id\":\"1\"}
    case_id = request.json.get('case_id')
    sql = Block.query.filter_by(id=case_id).all()
    sql = [x.as_dict() for x in sql]
    if sql:
        return jsonify(Blocks=sql)
    else:
        return "fail, cannot find case_id"
