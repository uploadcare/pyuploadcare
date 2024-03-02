import mimetypes
import os
from typing import IO, Any, Dict, Iterable, List, TypeVar, Union

from pyuploadcare import File


def get_file_size(file_object: IO) -> int:
    return os.fstat(file_object.fileno()).st_size


def extracts_uuids(files: Iterable[Union[str, File]]) -> List[str]:
    uuids: List[str] = []

    for file_ in files:
        if isinstance(file_, File):
            uuids.append(file_.uuid)
        elif isinstance(file_, str):
            uuids.append(file_)
        else:
            raise ValueError(
                "Invalid type for sequence item: {0}".format(type(file_))
            )

    return uuids


T = TypeVar("T")


def iterate_over_batches(
    collection: List[T], batch_size: int
) -> Iterable[List[T]]:
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
    mapping: Dict[KeyType, Any], *updating_mappings: Dict[KeyType, Any]
) -> Dict[KeyType, Any]:
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
