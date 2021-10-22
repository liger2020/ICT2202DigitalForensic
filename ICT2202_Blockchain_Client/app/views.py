import sys

from flask import request, jsonify
from app import app, db
from app.controller import send_block, convert_to_pool, verify
from app.models import Pool

STATUS_OK = 200
STATUS_NOT_FOUND = 404
TIMEOUT = 3000


@app.route("/health")
def current_health():
    resp = {"Python_version": sys.version,
            "Platform": sys.platform,
            "Health": "Good"}
    return resp, STATUS_OK


@app.route('/receivepool', methods=['POST'])
def receive():
    # Process JSON to Pool Model Object
    pool_json = request.get_json()
    # for pool in pool_json["Pool"]:# Convert string to json object
    pool = convert_to_pool(pool_json)
    if pool is None:
        return {"Format": "Wrong"}

    # TODO Verification Process
    verified = verify(pool)
    resp = {"pool_id": pool.id, "response": verified}  # Placeholder

    # Send Response Back to Server
    send_block(request.remote_addr, resp)

    return pool.as_dict(), STATUS_OK


@app.route('/send_block')
def send():
    test = Pool(1, meta_data="test", log="test")
    db.session.add(test)
    db.session.commit()

    return jsonify(output=test), STATUS_OK