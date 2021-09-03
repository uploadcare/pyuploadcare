from unittest import result
from pyuploadcare.entities import Entity, FileInfo
from pydantic import BaseModel

import typing


class Response(BaseModel):
    ...


class EntityListResponse(Response):
    results: typing.List[Entity]


class PaginatedResponse(EntityListResponse):
    next: typing.Optional[str]
    previous: typing.Optional[str]
    total: int
    per_page: int


class FileListResponse(PaginatedResponse):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/filesList
    results: typing.List[FileInfo]


class BatchFileOperationResponse(EntityListResponse):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/filesStoring
    status: str
    problems: typing.Optional[typing.Dict[str, typing.Any]]


class CopyFile2LocalStorageResponse(Response):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/createLocalCopy
    type: str
    result: FileInfo


class CopyFile2RemoteStorageResponse(Response):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/createRemoteCopy
    type: str
    result: str
