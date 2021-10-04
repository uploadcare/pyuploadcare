import typing

from pydantic import BaseModel

from pyuploadcare.api.entities import (
    DocumentConvertInfo,
    Entity,
    FileInfo,
    GroupInfo,
    VideoConvertInfo,
)


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
    results: typing.List[FileInfo]  # type: ignore


class GroupListResponse(PaginatedResponse):
    # https://uploadcare.com/api-refs/rest-api/v0.5.0/#operation/groupsList
    results: typing.List[GroupInfo]  # type: ignore


class BatchFileOperationResponse(Response):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/filesStoring
    status: str
    problems: typing.Optional[typing.Dict[str, typing.Any]]
    result: typing.Optional[typing.List[FileInfo]]


class CreateLocalCopyResponse(Response):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/createLocalCopy
    type: str
    result: FileInfo


class CreateRemoteCopyResponse(Response):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/createRemoteCopy
    type: str
    result: str


class DocumentConvertResponse(Entity):
    problems: typing.Optional[typing.Dict[str, typing.Any]]
    result: typing.Optional[typing.List[DocumentConvertInfo]]


class VideoConvertResponse(Entity):
    problems: typing.Optional[typing.Dict[str, typing.Any]]
    result: typing.Optional[typing.List[VideoConvertInfo]]
