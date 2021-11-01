import json
import sys
from concurrent.futures import ThreadPoolExecutor

from flask import request, jsonify

from app import app, db, auth
from app.controller import send_block, verify
from app.models import Pool, UserStoredInfo, Peers

STATUS_OK = 200
STATUS_NOT_FOUND = 404
TIMEOUT = 3000

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


@app.route("/sync", methods=["POST"])
@auth.login_required
def get_latest_verified():
    # {"case_id": "1", "previous_hash": "123", "last_verified_hash":"123", "length":"2"}
    sync_json = request.get_json()
    if "case_id" not in sync_json or "previous_hash" not in sync_json or "last_verified_hash" not in sync_json or "length" not in sync_json:
        return "", STATUS_NOT_FOUND

    json_case_id = sync_json["case_id"]
    json_previous_hash = sync_json["previous_hash"]
    json_last_verified_hash = sync_json["last_verified_hash"]
    json_length = sync_json["length"]
    last_hash_block = UserStoredInfo.query.filter_by(case_id=sync_json["case_id"]).first()

    # First 0 Block
    if json_length == 1 and last_hash_block is None:
        new_stored_info = UserStoredInfo(json_case_id, json_last_verified_hash, json_length)
        db.session.add(new_stored_info)
    # If new matches to current last hash
    elif last_hash_block.last_verified_hash == json_previous_hash and last_hash_block.length == json_length - 1:
        last_hash_block.last_verified_hash = json_last_verified_hash
        last_hash_block.length += 1
    else:
        return "", STATUS_NOT_FOUND

    db.session.commit()
    return "", STATUS_OK


@app.route('/receivepool', methods=['POST'])
@auth.login_required
def receive():
    thread_pool = ThreadPoolExecutor(5)  # 5 Worker Threads

    # Process JSON to Pool Model Object
    pool_json = request.get_json()  # Convert string to json object
    for pool in pool_json["Pool"]:
        if pool is None:
            return {"Format": "Wrong"}
        else:
            print("This is the pool:", str(pool))
            verified = verify(pool)
            resp = {"pool_id": pool.get('id'), "response": verified}  # Placeholder
            print(resp)
            # Send Response Back to Server
            peer = Peers(request.remote_addr, 5000, None)
            thread_pool.submit(send_block, peer, resp, "receive_response")  # send block to user
            print("after submit")

        return request.remote_addr, STATUS_OK


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
