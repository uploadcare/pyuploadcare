import hashlib
import mimetypes
import os
import string
from collections.abc import Iterable
from datetime import datetime
from typing import IO, Any, TypeVar


def get_file_size(file_object: IO) -> int:
    return os.fstat(file_object.fileno()).st_size


def ensure_aware_datetime(value: datetime) -> datetime:
    """Return ``value`` if it is a timezone-aware ``datetime``.

    Raise ``ValueError`` for anything else, including a naive ``datetime``
    and a plain ``date``.
    """
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("Expected a timezone-aware datetime")
    return value


T = TypeVar("T")


def iterate_over_batches(
    collection: list[T], batch_size: int
) -> Iterable[list[T]]:
    """Generate consequent slices of size `batch_size`."""
    if batch_size < 1:
        raise ValueError("Wrong batch size: must be positive number")

    start, total = 0, len(collection)

    while start < total:
        yield collection[start : start + batch_size]  # noqa
        start += batch_size


def guess_mime_type(file_object: IO) -> str:
    """Guess mime type from file extension."""
    mime_type, _encoding = mimetypes.guess_type(file_object.name)
    if not mime_type:
        mime_type = "application/octet-stream"
    return mime_type


KeyType = TypeVar("KeyType")


def deep_update(
    mapping: dict[KeyType, Any], *updating_mappings: dict[KeyType, Any]
) -> dict[KeyType, Any]:
    updated_mapping = mapping.copy()
    for updating_mapping in updating_mappings:
        for k, v in updating_mapping.items():
            if (
                k in updated_mapping
                and isinstance(updated_mapping[k], dict)
                and isinstance(v, dict)
            ):
                updated_mapping[k] = deep_update(updated_mapping[k], v)
            else:
                updated_mapping[k] = v
    return updated_mapping


def base36encode(number):
    if number == 0:
        return "0"
    alphabet = string.digits + string.ascii_lowercase
    base36 = ""
    while number > 0:
        number, i = divmod(number, 36)
        base36 = alphabet[i] + base36
    return base36


def get_cname_prefix(pub_key: str):
    CNAME_PREFIX_LEN = 10
    sha256_hex = hashlib.sha256(pub_key.encode()).hexdigest()
    sha256_base36 = base36encode(number=int(sha256_hex, 16))
    prefix = sha256_base36[:CNAME_PREFIX_LEN]
    return prefix


def get_cdn_base(
    pub_key: str | None, default: str, subdomains: bool, subdomains_ptn: str
) -> str:
    if subdomains and pub_key:
        prefix = get_cname_prefix(pub_key)
        return subdomains_ptn.format(prefix=prefix)
    return default
