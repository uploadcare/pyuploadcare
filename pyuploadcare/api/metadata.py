import re

from pyuploadcare.exceptions import MetadataValidationError


META_KEY_PATTERN = r"[-_.:A-Za-z0-9]"
META_KEY_MAX_LEN = 64

META_VALUE_MAX_LEN = 512

LENGTH = f"{{1,{META_KEY_MAX_LEN}}}"
key_matcher = re.compile(f"^{META_KEY_PATTERN}{LENGTH}$")


def validate_meta_key(key):
    if not isinstance(key, str):
        raise MetadataValidationError(
            f"Meta Key [{key!s}] must be string not a {type(key)}"
        )

    if not key_matcher.match(key):
        raise MetadataValidationError(f"Meta Key [{key}] is not valid")


def validate_meta_value(value):
    if not isinstance(value, str):
        raise MetadataValidationError(
            f"Meta Value [{value!s}] must be string not a {type(value)}"
        )

    if len(value) > META_VALUE_MAX_LEN:
        raise MetadataValidationError(f"Meta Value [{value}] is not valid")


def validate_metadata(metadata_dict):
    for key, value in metadata_dict.items():
        validate_meta_key(key)
        validate_meta_value(value)
