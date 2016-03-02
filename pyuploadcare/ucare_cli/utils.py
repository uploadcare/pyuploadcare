# coding: utf-8
import json


def pprint(value):
    print(json.dumps(value, indent=2))


def bool_or_none(value):
    return {'true': True, 'false': False}.get(value)


def int_or_none(value):
    return None if value.lower() == 'none' else int(value)
