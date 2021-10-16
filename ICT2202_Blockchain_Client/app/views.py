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


@app.route('/receivepool', methods=['POST'])
def receive():
    pool_json = request.get_json()  # Convert string to json object
    pool_json["id"]
    resp = verify(pool_json)
    send(resp, server)
    #
    #
    #
    return json_blocks, STATUS_OK

# Server~
@app.route('/receive')
def receive_resp():
    resp = request.get_json()
    a = Block.query
    a.id =
    db.session.add()