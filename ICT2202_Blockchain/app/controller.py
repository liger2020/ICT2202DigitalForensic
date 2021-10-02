import requests

from app.models import Block, Peers


def convert_to_block(json_block):
    try:
        return Block(json_block["ID"], json_block["Comment"], json_block["Amount"], json_block["Verified"] == "True")
    except KeyError:
        return None


def check_health(ip_address, port):
    try:
        resp = requests.get("http://{}:{}/health".format(ip_address, port), timeout=3)
        if resp.status_code == 200:
            return ip_address, port

        return None
    except:
        return None


def send_block(json):
    pass
