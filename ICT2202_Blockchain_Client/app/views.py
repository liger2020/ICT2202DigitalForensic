import sys

from flask import request, jsonify
from app import app, db, auth
from app.controller import send_block, convert_to_pool, verify
from app.models import Pool
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, g
from flask_httpauth import HTTPTokenAuth

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


@app.route('/receivepool', methods=['POST'])
@auth.login_required
def receive():
    thread_pool = ThreadPoolExecutor(5)  # 5 Worker Threads

    # Process JSON to Pool Model Object
    pool_json = request.get_json()  # Convert string to json object
    for x in pool_json["Pool"]:
        pool = convert_to_pool(x)
        if pool is None:
            return {"Format": "Wrong"}

        # verified = verify(pool)
        # print("AFTER VERIFY", verified)
        # TODO VERIFY RETURNING NONE
        verified = 1
        resp = {"pool_id": pool.id, "response": verified}  # Placeholder

        # Send Response Back to Server
        thread_pool.submit(send_block, request.remote_addr, resp)  # send block to user

        return "Lol", STATUS_OK


@app.route('/send_block')
def send():
    test = Pool(1, meta_data="test", log="test")
    db.session.add(test)
    db.session.commit()

    return jsonify(output=test), STATUS_OK


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
