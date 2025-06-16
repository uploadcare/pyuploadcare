import hashlib
import string
from functools import partial


CNAME_PREFIX_LEN = 10


def base36encode(number):
    if number == 0:
        return '0'
    alphabet = string.digits + string.ascii_lowercase
    base36 = ''
    while number > 0:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    return base36


def get_cname_prefix(pub_key: str):
    sha256_hex = hashlib.sha256(pub_key.encode()).hexdigest()
    sha256_base36 = base36encode(
        number=int(sha256_hex, 16)
    )
    prefix = sha256_base36[:CNAME_PREFIX_LEN]
    return prefix


def flatten_dict(simple_mapping, attribute_base="metadata") -> dict:
    """
    Straightforward way to use nested dict for multipart/form-data
    """
    result = dict()
    for key, val in simple_mapping.items():
        if not isinstance(val, str):
            raise TypeError(
                f"Expect 'string' for dict to be flatten, got {type(val)} instead"
            )
        result[f"{attribute_base}[{key}]"] = val

    return result

