import requests
import random
import math
from app.models import Block, Peers
from concurrent.futures import ThreadPoolExecutor, as_completed


def convert_to_block(json_block):
    try:
        return Block(json_block["index"], json_block["proof_number"], json_block["previous_block_hash"], json_block["meta_data"])
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

'''
User will store Case id and the last block hash of the respective cases they are in.
When verification is needed, the server will select 51 percent of the people in the case. 
These delegates will then verify the hash of the block and return a yes/no respond to the server.
'''




def randomselect():
    peer_list = Peers.query.all()
    numberofpeer = len(peer_list)
    fiftyone = math.ceil(numberofpeer * 0.51)
    delegates = random.sample(peer_list,fiftyone)
    print(delegates)
    return delegates


def verify():
    blocks = [x.as_dict() for x in Block.query.all()]
    last_block = blocks[-1].get('block_hash')
    case_id = blocks[-1].get('id')
    
    print("This case the case ID: " + str(case_id))
    #Check if last block's hash matches user's
    if case_id == 1: # Let the value 1 be case id value stored in user side.
        if last_block == "123":  #Let 123 be last block hash stored in user side.
            print("Yes") #consensus is send to the speaker
        else:
            print("No")
    else:
        print("No tele")

#verify()
randomselect()
