from sqlalchemy import inspect

from app.models import Block


def convert_to_block(json_block):
    try:
        return Block(json_block["ID"], json_block["Comment"], json_block["Amount"], json_block["Verified"] == "True")
    except KeyError:
        return None


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}
