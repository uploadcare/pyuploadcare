import mimetypes
import os
from typing import IO, Iterable, List, Union

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


def guess_mime_type(file_object: IO) -> str:
    """Guess mime type from file extension."""
    mime_type, _encoding = mimetypes.guess_type(file_object.name)
    if not mime_type:
        mime_type = "application/octet-stream"
    return mime_type
