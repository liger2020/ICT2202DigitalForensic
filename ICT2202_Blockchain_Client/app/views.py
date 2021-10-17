import sys

from flask import request

from app import app
from app.controller import send_block, convert_to_pool

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
    pool_json = request.get_json()  # Convert string to json object
    pool = convert_to_pool(pool_json)
    if pool is None:
        return {"Format": "Wrong"}

    # TODO Verification Process
    # resp = verify(pool)
    resp = {"pool_id": pool.id, "response": 1}  # Placeholder

    # Send Response Back to Server
    send_block(request.remote_addr, resp)

    return pool.as_dict(), STATUS_OK
