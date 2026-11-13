from enum import Enum
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel, RootModel

from pyuploadcare.api.entities import (
    DocumentConvertInfo,
    Entity,
    FileInfo,
    FileSearchInfo,
    GroupInfo,
    MetadataDict,
    VideoConvertInfo,
)


class Response(BaseModel): ...


class EntityListResponse(Response):
    results: list[Entity]


class PaginatedResponse(EntityListResponse):
    next: str | None = None
    previous: str | None = None
    total: int
    per_page: int


class FileListResponse(PaginatedResponse):
    # https://uploadcare.com/docs/api/rest/file/files-list/
    results: list[FileInfo]  # type: ignore


class FileSearchResponse(PaginatedResponse):
    # https://uploadcare.com/docs/api/rest/file/search-files/
    results: list[FileSearchInfo]  # type: ignore


class GroupListResponse(PaginatedResponse):
    # https://uploadcare.com/docs/api/rest/group/groups-list/
    results: list[GroupInfo]  # type: ignore


class BatchFileOperationResponse(Response):
    # https://uploadcare.com/docs/api/rest/file/files-storing/
    status: str
    problems: dict[str, Any] | None = None
    result: list[FileInfo] | None = None


class CreateLocalCopyResponse(Response):
    # https://uploadcare.com/docs/api/rest/file/create-local-copy/
    type: str
    result: FileInfo


class CreateRemoteCopyResponse(Response):
    # https://uploadcare.com/docs/api/rest/file/create-remote-copy/
    type: str
    result: str


class DocumentConvertResponse(Entity):
    problems: dict[str, Any] | None = None
    result: list[DocumentConvertInfo] | None = None


class VideoConvertResponse(Entity):
    problems: dict[str, Any] | None = None
    result: list[VideoConvertInfo] | None = None


class UpdateMetadataKeyResponse(RootModel, Entity):
    root: str


class DeleteMetadataKeyResponse(Entity):
    pass


class GetAllMetadataResponse(RootModel, Entity):
    root: MetadataDict


class GetFileTagsResponse(Response):
    # https://uploadcare.com/docs/api/rest/file-tags/get-tags/
    tags: list[str]


class UpdateFileTagsResponse(Response):
    # https://uploadcare.com/docs/api/rest/file-tags/put-tags/
    # https://uploadcare.com/docs/api/rest/file-tags/patch-tags/
    tags: list[str]
    added: list[str]
    deleted: list[str]


class AddonResponseResult(Entity):
    pass


class AddonStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    ERROR = "error"
    DONE = "done"
    UNKNOWN = "unknown"


class AddonExecuteResponse(Response):
    request_id: UUID


AddonResultType = TypeVar("AddonResultType", bound=AddonResponseResult)


class AddonResponse(Response):
    status: AddonStatus
    result: dict[str, Any] | None = None
