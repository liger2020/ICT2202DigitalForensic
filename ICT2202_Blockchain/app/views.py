import datetime
import math
import sys
import json

from flask import request, jsonify, url_for, g
from flask_restful import abort
from flask_httpauth import HTTPTokenAuth
from app import app, db, auth
from app.controller import convert_to_pool, convert_to_consensus, verify, send_new_verified_to_clients
# Import module models
from app.models import Peers, Block, Pool, Consensus, User, UserCase, MetaDataFile

STATUS_OK = 200
STATUS_NOT_FOUND = 404
TIMEOUT = 60 * 15

tokens = {
    "secret-token-1": "john",
    "secret-token-2": "susan"
}


@app.route("/health")
def current_health():
    resp = {"Python_version": sys.version,
            "Platform": sys.platform,
            "Health": "Good"}
    return resp, STATUS_OK


# Assuming unverified
@app.route('/receiveblock', methods=['POST'])
@auth.login_required
def receive_block():
    num_of_errors = 0

    # Check block need verify
    json_blocks = request.get_json()
    for json_block in json_blocks["Pool"]:

        # Convert into class object
        block = convert_to_pool(json_block)
        if block is None:
            print("Error processing: {}".format(json_block))
            num_of_errors += 1
            continue

        # If case doesnt exist (Block 0) add to block directly
        exist = Block.query.filter_by(id=block.case_id).first()
        if exist is None:
            # Add to Block
            new_block = Block(block.case_id, block.meta_data, block.log, block_number=block.block_number, previous_block_hash=block.previous_block_hash, timestamp=block.timestamp, block_hash=block.block_hash, status=1)
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
    print("RICHED")
    resp = request.get_json()
    print("This is the response:" , str(resp))
    consensus = convert_to_consensus(resp, request.remote_addr)
    print(consensus)
    print("This is consensus pool id:" + str(consensus.pool_id))
    if consensus is None:
        # TODO return error code
        return {"error": "very true"}

    # Check Timeout
    pool = Pool.query.filter_by(id=consensus.pool_id).first()
    print(pool)
    if pool is not None:
        print("HIT 1")
        response_timestamp = pool.sendout_time
        try:
            if (response_timestamp + datetime.timedelta(seconds=TIMEOUT)) >= datetime.datetime.now():
                # Add to consensus Table TODO Add checks
                consent = Consensus.query.filter_by(ip_address=consensus.ip_address,pool_id=consensus.pool_id).first()
                if consent is None:
                    db.session.add(consensus)
                    db.session.commit()
                else:
                    consent.receive_timestamp = consensus.receive_timestamp
                    db.session.commit()
            else:
                # Discard (TIMED OUT)
                pass
        except:
            pass
    else:
        print("HIt 2")
    return {"Responding From": "/receive_response"}, STATUS_OK


# @app.route("/getallblocks")
# def get_all_blocks():
#     blocks = [x.as_dict() for x in Block.query.all()]
#     # Convert Object to JSON TODO
#     return jsonify(output=blocks), STATUS_OK


@app.route('/sync')
@auth.login_required
def sync():
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
    print("PRINTING: \n{}\n{}\n{}".format(output_list, length, block_list_count))
    return jsonify({"Blocks": output_list, "length": length, "Count": block_list_count})


# Getting Data From Database
@app.route('/usercase', methods=['POST'])
@auth.login_required
def get_peers():
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
    if token in tokens:
        return tokens[token]


@app.route('/api/test')
@auth.login_required
def index():
    """
    testing remove before final product
    curl http://192.168.75.133:5000/api/test -H "Authorization: Bearer secret-token-1"
    """
    return "Hello, {}!".format(auth.current_user())


@app.route('/userAssignedCase', methods=['POST'])
@auth.login_required
def assignedCase():
    """
curl -i -X POST -H "Content-Type:application/json" -H "Authorization:Bearer secret-token-1" http://192.168.75.133:5000/userAssignedCase -d {\"username\":\"test2\"}
    """
    username = request.json.get('username')
    if username is None:
        abort(400)
        return "failed, username is None"
    query = UserCase.query.filter_by(username=username).first()
    if query:
        return query.case_id
    return "fail"


@app.route('/caseinfo', methods=['POST'])
@auth.login_required
def caseinfo():
    """
    curl -i -X POST -H "Content-Type:application/json" -H "Authorization:Bearer secret-token-1" http://192.168.75.133:5000/caseinfo -d {\"case_id\":\"1\"}
    """
    case_id = request.json.get('case_id')
    print(case_id)
    sql = Block.query.filter_by(id=case_id).all()
    if sql:
        output = {}
        i = 0
        for rows in sql:
            i += 1
            rows_as_dict = rows.as_dict()
            output[i] = rows_as_dict
        return jsonify(output)
    else:
        return "fail, cannot find case_id"

# @app.route('/api/users', methods=['POST'])
# def new_user():
#     """
#     function to create new users
#     example: curl -i -X POST -H "Content-Type: application/json" -d {
#     \"username\":\"tests\",\"password\":\"testing\"} http://127.0.0.1:5000/api/users
#     """
#     username = request.json.get('username')
#     password = request.json.get('password')
#     if username is None or password is None:
#         abort(400)  # missing arguments
#     if User.query.filter_by(username=username).first() is not None:
#         abort(401)  # existing user
#     user = User(username=username)
#     user.hash_password(password)
#     user.generate_auth_token()
#     db.session.add(user)
#     db.session.commit()
#     return jsonify({'username': user.username}), 201, {'Location': url_for('new_user', id=user.id, _external=True)}
#

# @app.route('/api/resource')
# @auth.login_required
# def get_resource():
#     """
#     This is only for testing, delete during final product
#     curl -u test:testing -i -X GET http://192.168.75.133:5000/api/resource
#     """
#     return jsonify({'data': 'Hello, %s!' % g.user.username})
#
#
# @app.route('/api/token')
# @auth.login_required
# def get_auth_token():
#     token = g.user.generate_auth_token()
#     return jsonify({'token': token.decode('ascii')})
#
#
# @auth.verify_password
# def verify_password(username_or_token, password):
#     """
#     username_or_token: users table username or token generated by /api/token
#     password: users table password
#     """
#     # first try to authenticate by token
#     user = User.verify_auth_token(username_or_token)
#     if not user:
#         # try to authenticate with username/password
#         user = User.query.filter_by(username=username_or_token).first()
#         if not user or not user.verify_password(password):
#             return False
#     g.user = user
#     return True cae12def59de0081a1ecdc3d8cc4a1bacbc893b5bdffe27921d1acca205d788d
