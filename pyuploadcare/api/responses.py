from enum import Enum
from typing import Any, Dict, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, RootModel

from pyuploadcare.api.entities import (
    DocumentConvertInfo,
    Entity,
    FileInfo,
    GroupInfo,
    MetadataDict,
    VideoConvertInfo,
)


class Response(BaseModel): ...


class EntityListResponse(Response):
    results: List[Entity]


class PaginatedResponse(EntityListResponse):
    next: Optional[str] = None
    previous: Optional[str] = None
    total: int
    per_page: int


class FileListResponse(PaginatedResponse):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/filesList
    results: List[FileInfo]  # type: ignore


class GroupListResponse(PaginatedResponse):
    # https://uploadcare.com/api-refs/rest-api/v0.5.0/#operation/groupsList
    results: List[GroupInfo]  # type: ignore


class BatchFileOperationResponse(Response):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/filesStoring
    status: str
    problems: Optional[Dict[str, Any]] = None
    result: Optional[List[FileInfo]] = None


class CreateLocalCopyResponse(Response):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/createLocalCopy
    type: str
    result: FileInfo


class CreateRemoteCopyResponse(Response):
    # https://uploadcare.com/api-refs/rest-api/v0.6.0/#operation/createRemoteCopy
    type: str
    result: str


class DocumentConvertResponse(Entity):
    problems: Optional[Dict[str, Any]] = None
    result: Optional[List[DocumentConvertInfo]] = None


class VideoConvertResponse(Entity):
    problems: Optional[Dict[str, Any]] = None
    result: Optional[List[VideoConvertInfo]] = None


class UpdateMetadataKeyResponse(RootModel, Entity):
    root: str


class DeleteMetadataKeyResponse(Entity):
    pass


class GetAllMetadataResponse(RootModel, Entity):
    root: MetadataDict


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
    result: Optional[Dict[str, Any]] = None
