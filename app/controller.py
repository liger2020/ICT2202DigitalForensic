import requests
import random
from app.models import Block, Peers
from concurrent.futures import ThreadPoolExecutor, as_completed
from app import db


def convert_to_block(json_block):
    try:
        return Block(json_block["index"], json_block["proof_number"], json_block["previous_block_hash"],
                     json_block["meta_data"])
    except KeyError:
        return None


def check_health(peer):
    try:
        resp = requests.get("http://{}:{}/health".format(peer.ip_address, peer.port), timeout=3)
        if resp.status_code == 200:
            return peer

        return None
    except:
        return None


def get_live_peers():
    # Check peers alive
    live_peers = []
    futures = []

    pool = ThreadPoolExecutor(5)  # 5 Worker Threads

    # Get all peer's ip address and port from DB
    peer_list = Peers.query.all()

    # Use check_health() to get whether machine online
    for peer in peer_list:
        futures.append(pool.submit(check_health, peer))

    for x in as_completed(futures):
        result = x.result()
        if result is not None:
            live_peers.append(result)

    return live_peers


def send_block(peer, data):
    url = "http://{}:{}/receiveblock".format(peer.ip_address, peer.port)
    r = requests.post(url, json=data)
    output = {"Peer": url,
              "Answer": r.json(),
              "Status_Code": r.status_code
              }

    return output


def verify():
    peer_list = Peers.query.all()
    blocks = [x.as_dict() for x in Block.query.all()]

    last_block = blocks[-1].get('block_hash')
    case_id = blocks[-1].get('index')
    print(peer_list)

    # select 51% of the peers
    print(random.choices(peer_list))
    print(case_id)
    # Check if last block's hash matches user's
    # if case_id == "1": # Check if case ID match
    if last_block == "123":  # Let 123 be last block matches with user's side last hash
        print("Yes")  # consensus is send to the speaker
    else:
        print("No")
