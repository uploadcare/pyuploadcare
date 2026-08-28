import hashlib
import hmac
import logging
import warnings
from json import JSONDecodeError
from time import time
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Type,
    Union,
    cast,
)
from uuid import UUID

from httpx._types import RequestFiles

from pyuploadcare.api import entities, responses
from pyuploadcare.api.addon_entities import (
    AddonExecutionGeneralRequestData,
    AddonExecutionParams,
    AddonLabels,
)
from pyuploadcare.api.base import (
    API,
    CreateMixin,
    DeleteMixin,
    DeleteWithResponseMixin,
    ListCountMixin,
    ListMixin,
    RetrieveMixin,
    UpdateMixin,
    _iterate_pages,
)
from pyuploadcare.exceptions import (
    APIError,
    DuplicateFileError,
    InvalidParamError,
    InvalidRequestError,
    WebhookIsNotUnique,
)

from .entities import UUIDEntity
from .metadata import validate_meta_key, validate_meta_value, validate_metadata
from .search_entities import FileSearchRequest
from .tags import validate_tags
from .utils import flatten_dict, require_optional_int, require_range


logger = logging.getLogger("pyuploadcare")


# File search pagination limits.
# https://uploadcare.com/docs/api/rest/file/search-files/
SEARCH_DEFAULT_LIMIT = 20  # the server default when `limit` is not sent
SEARCH_MAX_LIMIT = 100
SEARCH_MAX_WINDOW = 1000  # `offset` + `limit` must not exceed this


class FilesAPI(API, ListCountMixin, RetrieveMixin, DeleteWithResponseMixin):
    resource_type = "files"
    response_classes = {
        "retrieve": entities.FileInfo,
        "list": responses.FileListResponse,
        "count": responses.FileListResponse,
        "store": entities.FileInfo,
        "update": entities.FileInfo,
        "delete": entities.FileInfo,
        "batch_store": responses.BatchFileOperationResponse,
        "batch_delete": responses.BatchFileOperationResponse,
        "local_copy": responses.CreateLocalCopyResponse,
        "remote_copy": responses.CreateRemoteCopyResponse,
        "search": responses.FileSearchResponse,
    }

    def search(
        self,
        request: Union[FileSearchRequest, Dict[str, Any]],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_appdata: bool = False,
    ) -> responses.FileSearchResponse:
        """Search files, returning a single page of results.

        https://uploadcare.com/docs/file-search/

        Args:
            - request: a ``FileSearchRequest`` or a dict in the same shape.
                A dict uses the SDK's shape for ``exact.metadata``, i.e.
                ``{"exact": {"metadata": {"color": ["red"]}}}``, not the wire
                shape ``{"exact": {"metadata[color]": [...]}}``.
            - limit: results per page, 1 to 100. The server defaults to 20.
            - offset: how many results to skip. ``offset + limit`` must not
                exceed 1000.
            - include_appdata: embed application data in every result.
        """
        search_request = (
            request
            if isinstance(request, FileSearchRequest)
            else FileSearchRequest.model_validate(request)
        )

        require_optional_int("limit", limit)
        require_optional_int("offset", offset)
        require_range("limit", limit, minimum=1, maximum=SEARCH_MAX_LIMIT)
        require_range("offset", offset, minimum=0)

        effective_limit = SEARCH_DEFAULT_LIMIT if limit is None else limit
        effective_offset = 0 if offset is None else offset

        if effective_offset + effective_limit > SEARCH_MAX_WINDOW:
            raise InvalidParamError(
                "`offset` + `limit` must not exceed "
                f"{SEARCH_MAX_WINDOW}, got "
                f"{effective_offset} + {effective_limit}. "
                "Narrow the query instead of paging deeper"
            )

        query_parameters: Dict[str, Any] = {}
        if limit is not None:
            query_parameters["limit"] = limit
        if offset is not None:
            query_parameters["offset"] = offset
        if include_appdata:
            query_parameters["include"] = "appdata"

        url = self._build_url(
            suffix="search", query_parameters=query_parameters
        )
        response_class = self._get_response_class("search")
        json_response = self._client.post(
            url, json=search_request.to_payload()
        ).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.FileSearchResponse, response)

    def search_iterate(
        self,
        request: Union[FileSearchRequest, Dict[str, Any]],
        limit: Optional[int] = None,
        request_limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_appdata: bool = False,
    ) -> Iterator[entities.FileSearchInfo]:
        """Iterate over search results, page by page.

        Pages are walked the same way ``ListMixin.list`` walks them — by
        following the response's ``next`` URL, which points back at the
        search endpoint with the ``limit``/``offset`` of the following page —
        except that each page re-sends the search request as a ``POST`` body.

        Only the first request is built here, and it is clamped to the search
        window, because a legal starting ``offset`` can otherwise produce an
        illegal ``offset`` + ``limit`` combination; from then on the server
        computes ``next`` within the window.

        Args:
            - request: a ``FileSearchRequest`` or a dict in the same shape.
            - limit: total number of results to yield. ``None`` yields
                everything reachable.
            - request_limit: number of results retrieved per request (page).
            - offset: how many results to skip before the first page.
            - include_appdata: embed application data in every result.
        """
        search_request = (
            request
            if isinstance(request, FileSearchRequest)
            else FileSearchRequest.model_validate(request)
        )

        page_size = (
            SEARCH_DEFAULT_LIMIT if request_limit is None else request_limit
        )
        start = 0 if offset is None else offset

        if start >= SEARCH_MAX_WINDOW:
            raise InvalidParamError(
                f"`offset` must be less than {SEARCH_MAX_WINDOW}: search "
                "cannot reach past the first "
                f"{SEARCH_MAX_WINDOW} results"
            )

        first_page_size = min(page_size, SEARCH_MAX_WINDOW - start)
        if limit is not None:
            first_page_size = min(first_page_size, limit)
        if first_page_size <= 0:
            return iter(())

        query_parameters: Dict[str, Any] = {
            "limit": first_page_size,
            "offset": start,
        }
        if include_appdata:
            query_parameters["include"] = "appdata"

        first_url = self._build_url(
            suffix="search", query_parameters=query_parameters
        )
        response_class = self._get_response_class("search")
        payload = search_request.to_payload()  # rendered once for all pages

        return _iterate_pages(
            first_url,
            lambda url: self._client.post(url, json=payload).json(),
            lambda raw: self._parse_response(raw, response_class),
            limit=limit,
        )

    def store(self, file_uuid: Union[UUID, str]) -> entities.FileInfo:
        url = self._build_url(file_uuid, suffix="storage")
        response_class = self._get_response_class("store")
        json_response = self._client.put(url).json()
        response = self._parse_response(json_response, response_class)
        return cast(entities.FileInfo, response)

    def batch_store(
        self, file_uuids: Iterable[Union[UUID, str]]
    ) -> responses.BatchFileOperationResponse:
        url = self._build_url(suffix="storage")
        response_class = self._get_response_class("batch_store")
        json_response = self._client.put(url, json=file_uuids).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.BatchFileOperationResponse, response)

    def batch_delete(
        self, file_uuids: Iterable
    ) -> responses.BatchFileOperationResponse:
        url = self._build_url(suffix="storage")
        response_class = self._get_response_class("batch_delete")
        json_response = self._client.delete_with_payload(
            url, json=file_uuids
        ).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.BatchFileOperationResponse, response)

    def local_copy(
        self, source: Union[UUID, str], store: bool = False
    ) -> responses.CreateLocalCopyResponse:
        url = self._build_url(suffix="local_copy")
        data = {"source": source, "store": store}
        response_class = self._get_response_class("local_copy")
        json_response = self._client.post(url, json=data).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.CreateLocalCopyResponse, response)

    def remote_copy(
        self,
        source: Union[UUID, str],
        target: str,
        make_public: bool = True,
        pattern: str = "${default}",
    ) -> responses.CreateRemoteCopyResponse:
        url = self._build_url(suffix="remote_copy")
        data = {
            "source": source,
            "target": target,
            "make_public": make_public,
            "pattern": pattern,
        }
        response_class = self._get_response_class("remote_copy")
        json_response = self._client.post(url, json=data).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.CreateRemoteCopyResponse, response)


class GroupsAPI(API, ListCountMixin, RetrieveMixin, DeleteMixin):
    resource_type = "groups"
    entity_class = entities.GroupInfo

    response_classes = {
        "retrieve": entities.GroupInfo,
        "list": responses.GroupListResponse,
        "count": responses.GroupListResponse,
    }

    def store(self, file_uuid: Union[UUID, str]) -> Dict[str, Any]:
        warnings.warn(
            "/groups/:uuid/storage/ endpoint has been removed from REST API v0.7"
            "https://uploadcare.com/api-refs/rest-api/v0.7.0/#tag/Changelog",
            DeprecationWarning,
        )
        url = self._build_url(file_uuid, suffix="storage")
        return self._client.put(url).json()


class ProjectAPI(API, RetrieveMixin):
    resource_type = "project"
    entity_class = entities.ProjectInfo
    response_classes = {
        "retrieve": entities.ProjectInfo,
    }


class WebhooksAPI(API, CreateMixin, ListMixin, UpdateMixin, DeleteMixin):
    resource_type = "webhooks"
    entity_class = entities.Webhook
    response_classes = {
        "create": entities.Webhook,
        "list": List[entities.Webhook],  # type: ignore
        "update": entities.Webhook,
    }
    _NON_FIELD = "non_field_errors"
    _ALREADY = "project is already subscribed on this event"

    def _process_exceptions(self, raised):
        _text = str(raised)
        if self._NON_FIELD in _text and self._ALREADY in _text:
            raise WebhookIsNotUnique(_text)

        raise

    def update(
        self,
        resource_uuid: Union[UUID, str, UUIDEntity],
        data: Optional[Dict] = None,
    ):
        try:
            return super(WebhooksAPI, self).update(resource_uuid, data)
        except InvalidRequestError as request_error:
            self._process_exceptions(request_error)

    def create(
        self,
        data: Optional[Dict] = None,
    ):
        try:
            return super(WebhooksAPI, self).create(data)
        except InvalidRequestError as request_error:
            self._process_exceptions(request_error)


class DocumentConvertAPI(API, RetrieveMixin):
    resource_type = "convert/document"
    entity_class = entities.DocumentConvertInfo

    response_classes = {
        "retrieve": entities.DocumentConvertFormatInfo,
        "convert": responses.DocumentConvertResponse,
        "status": entities.DocumentConvertStatus,
    }

    def retrieve(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        include_appdata: bool = False,
    ) -> entities.DocumentConvertFormatInfo:
        response = super().retrieve(resource_uuid)
        return cast(entities.DocumentConvertFormatInfo, response)

    def convert(
        self,
        paths: List[str],
        store: Optional[bool] = None,
        save_in_group: bool = False,
    ) -> responses.DocumentConvertResponse:
        url = self._build_url()

        data = {
            "paths": paths,
        }

        if isinstance(store, bool):
            data["store"] = str(store).lower()  # type: ignore

        if save_in_group:
            data["save_in_group"] = "1"  # type: ignore

        response_class = self._get_response_class("convert")
        document = self._client.post(url, json=data).json()
        response = self._parse_response(document, response_class)
        return cast(responses.DocumentConvertResponse, response)

    def status(self, token: int) -> entities.DocumentConvertStatus:
        url = self._build_url(suffix=f"status/{token}")
        response_class = self._get_response_class("status")
        document = self._client.get(url).json()
        response = self._parse_response(document, response_class)
        return cast(entities.DocumentConvertStatus, response)


class VideoConvertAPI(API):
    resource_type = "convert/video"
    entity_class = entities.VideoConvertInfo

    response_classes = {
        "convert": responses.VideoConvertResponse,
        "status": entities.VideoConvertStatus,
    }

    def convert(
        self,
        paths: List[str],
        store: Optional[bool] = None,
    ) -> responses.VideoConvertResponse:
        url = self._build_url()

        data = {
            "paths": paths,
        }
        if isinstance(store, bool):
            data["store"] = str(store).lower()  # type: ignore

        response_class = self._get_response_class("convert")
        document = self._client.post(url, json=data).json()
        response = self._parse_response(document, response_class)
        return cast(responses.VideoConvertResponse, response)

    def status(self, token: int) -> entities.VideoConvertStatus:
        url = self._build_url(suffix=f"status/{token}")
        response_class = self._get_response_class("status")
        document = self._client.get(url).json()
        response = self._parse_response(document, response_class)
        return cast(entities.VideoConvertStatus, response)


class UploadAPI(API):
    resource_type = "base"

    @staticmethod
    def generate_secure_signature(secret: str, expire: int):
        return hmac.new(
            secret.encode("utf-8"), str(expire).encode("utf-8"), hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _set_tags(data: Dict[str, Any], tags: Optional[Iterable[str]]) -> None:
        """Add the comma-separated `tags` form field to `data`, if any.

        The field is omitted entirely when there is nothing to send.
        """
        if tags is None:
            return

        validated_tags = validate_tags(tags)

        if validated_tags:
            data["tags"] = ",".join(validated_tags)

    def upload(  # noqa: C901
        self,
        files: RequestFiles,
        secure_upload: bool = False,
        common_metadata: Optional[dict] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        store: Optional[str] = "auto",
        expire: Optional[int] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        data = {}

        data["UPLOADCARE_STORE"] = store

        if public_key is None:
            public_key = self.public_key

        if common_metadata is not None:
            validate_metadata(common_metadata)
            data.update(flatten_dict(common_metadata))

        self._set_tags(data, tags)

        data["UPLOADCARE_PUB_KEY"] = public_key

        if secure_upload:
            if secret_key is None:
                secret_key = self.secret_key

            if expire is None:
                expire = int(time()) + self.signed_uploads_ttl
            data["expire"] = str(expire)

            signature = self.generate_secure_signature(secret_key, expire)  # type: ignore
            data["signature"] = signature

        url = self._build_url()
        document = self._client.post(url, data=data, files=files)
        return document.json()

    def start_multipart_upload(
        self,
        file_name: str,
        file_size: int,
        content_type: str,
        metadata: Optional[dict] = None,
        store: Optional[str] = None,
        secure_upload: bool = False,
        expire: Optional[int] = None,
        tags: Optional[Iterable[str]] = None,
    ):
        data = {
            "filename": file_name,
            "size": str(file_size),
            "content_type": content_type,
            "UPLOADCARE_PUB_KEY": self.public_key,
        }

        if store is not None:
            data["UPLOADCARE_STORE"] = store

        if metadata is not None:
            validate_metadata(metadata)
            data.update(flatten_dict(metadata))

        self._set_tags(data, tags)

        if secure_upload:
            expire = (
                (int(time()) + self.signed_uploads_ttl)
                if expire is None
                else expire
            )

            data["expire"] = str(expire)
            data["signature"] = self.generate_secure_signature(
                self.secret_key, expire  # type: ignore
            )

        url = self._build_url(base="multipart/start")
        document = self._client.post(url, data=data)
        return document.json()

    def multipart_upload_chunk(self, url: str, chunk: bytes):
        document = self._client.put(
            url,
            content=chunk,
            headers={"Content-Type": "application/octet-stream"},
        )
        return document.content

    def multipart_complete(self, uuid: UUID):
        data = {
            "uuid": str(uuid),
            "UPLOADCARE_PUB_KEY": self.public_key,
        }
        url = self._build_url(base="multipart/complete")
        document = self._client.post(url, data=data)
        return document.json()

    def upload_from_url(  # noqa: max-complexity: 8
        self,
        source_url,
        store="auto",
        filename=None,
        metadata: Optional[Dict] = None,
        secure_upload: bool = False,
        expire: Optional[int] = None,
        check_duplicates: Optional[bool] = None,
        save_duplicates: Optional[bool] = None,
    ) -> str:
        data = {
            "source_url": source_url,
            "store": store,
            "pub_key": self.public_key,
        }
        if filename:
            data["filename"] = filename

        if metadata is not None:
            validate_metadata(metadata)
            data.update(flatten_dict(metadata))

        if secure_upload:
            expire = (
                (int(time()) + self.signed_uploads_ttl)
                if expire is None
                else expire
            )

            data["expire"] = str(expire)
            data["signature"] = self.generate_secure_signature(
                self.secret_key, expire  # type: ignore
            )

        if check_duplicates is not None:
            data["check_URL_duplicates"] = "1" if check_duplicates else "0"

        if save_duplicates is not None:
            data["save_URL_duplicates"] = "1" if save_duplicates else "0"

        url = self._build_url(base="/from_url")
        document = self._client.post(url, data=data)
        response = document.json()
        if "token" not in response:
            if check_duplicates and response["type"] == "file_info":
                file_id = response["file_id"]
                raise DuplicateFileError(
                    f"The file is a duplicate of a previously uploaded file ({file_id})",
                    file_id=file_id,
                )
            raise APIError(f"could not find token in result: {response}")
        return response["token"]

    def get_upload_from_url_status(self, token: str) -> Dict[str, Any]:
        query_parameters = {
            "token": token,
        }
        url = self._build_url(
            base="/from_url/status", query_parameters=query_parameters
        )
        document = self._client.get(url)
        response = document.json()
        if "status" not in response:
            raise APIError(f"could not find status in result: {response}")
        return response

    def create_group(
        self,
        files: Iterable[Union[str, UUID]],
        secure_upload: bool = False,
        expire: Optional[int] = None,
    ):
        data = {
            "pub_key": self.public_key,
        }

        for index, file in enumerate(files):
            data[f"files[{index}]"] = file  # type: ignore

        if secure_upload:
            expire = (
                (int(time()) + self.signed_uploads_ttl)
                if expire is None
                else expire
            )

            data["expire"] = str(expire)
            data["signature"] = self.generate_secure_signature(
                self.secret_key, expire  # type: ignore
            )

        url = self._build_url(base="/group/")
        document = self._client.post(url, data=data)
        return document.json()


class MetadataAPI(API):
    resource_type = "files"
    response_classes = {
        "update": responses.UpdateMetadataKeyResponse,
        "get_all": responses.GetAllMetadataResponse,
        "get_key": responses.UpdateMetadataKeyResponse,
    }

    def update_or_create_key(
        self, file_uuid: Union[UUID, str], mkey: str, mvalue: str
    ) -> str:
        validate_meta_key(mkey)
        validate_meta_value(mvalue)
        suffix = f"metadata/{mkey}"
        url = self._build_url(file_uuid, suffix=suffix)
        response_class = self._get_response_class("update")
        json_response = self._client.put(url, json=mvalue).json()
        response = self._parse_response(json_response, response_class).root  # type: ignore
        return cast(str, response)

    def get_all_metadata(self, file_uuid: Union[UUID, str]) -> dict:
        url = self._build_url(file_uuid, suffix="metadata")
        response_class = self._get_response_class("get_all")

        try:
            json_response = self._client.get(url).json()
        except JSONDecodeError as jerr:  # noqa
            # assume that there is "empty response" bug (Expecting value: line 1 column 1 (char 0))
            logging.warning(
                f"For file `{file_uuid}` there is empty metadata response"
            )
            json_response = {}

        response = self._parse_response(json_response, response_class).root  # type: ignore
        return cast(dict, response)

    def delete_key(self, file_uuid: Union[UUID, str], mkey: str) -> None:
        validate_meta_key(mkey)
        suffix = f"metadata/{mkey}"
        url = self._build_url(file_uuid, suffix=suffix)
        self._client.delete(url)

    def get_key(self, file_uuid: Union[UUID, str], mkey: str) -> str:
        validate_meta_key(mkey)
        suffix = f"metadata/{mkey}"
        url = self._build_url(file_uuid, suffix=suffix)
        response_class = self._get_response_class("get_key")
        json_response = self._client.get(url).json()
        response = self._parse_response(json_response, response_class).root  # type: ignore
        return cast(str, response)


class TagsAPI(API):
    """File tags.

    https://uploadcare.com/docs/file-tags/
    """

    resource_type = "files"
    response_classes = {
        "get": responses.GetFileTagsResponse,
        "replace": responses.UpdateFileTagsResponse,
        "update": responses.UpdateFileTagsResponse,
    }

    @staticmethod
    def _canonical_uuid(file_uuid: Union[UUID, str]) -> str:
        """Return a canonical UUID string, rejecting anything else.

        ``API._build_url`` joins the identifier with ``urljoin``, so a value
        like ``"//example.com/x"`` or an absolute URL would replace the
        configured API origin on an authenticated request.
        """
        try:
            return str(UUID(str(file_uuid)))
        except (AttributeError, TypeError, ValueError):
            raise InvalidParamError(f"Invalid UUID: {file_uuid!s}")

    def _tags_url(self, file_uuid: Union[UUID, str]) -> str:
        return self._build_url(self._canonical_uuid(file_uuid), suffix="tags")

    def get(self, file_uuid: Union[UUID, str]) -> List[str]:
        """Return the tags of a file, an empty list if it has none."""
        url = self._tags_url(file_uuid)
        response_class = self._get_response_class("get")
        json_response = self._client.get(url).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.GetFileTagsResponse, response).tags

    def replace(
        self, file_uuid: Union[UUID, str], tags: Iterable[str]
    ) -> responses.UpdateFileTagsResponse:
        """Replace all tags of a file.

        Passing an empty collection clears the tags.
        """
        url = self._tags_url(file_uuid)
        data = {"tags": validate_tags(tags)}
        response_class = self._get_response_class("replace")
        json_response = self._client.put(url, json=data).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.UpdateFileTagsResponse, response)

    def update(
        self,
        file_uuid: Union[UUID, str],
        add: Optional[Iterable[str]] = None,
        delete: Optional[Iterable[str]] = None,
    ) -> responses.UpdateFileTagsResponse:
        """Add and/or delete tags of a file atomically.

        Both arguments are optional, matching the endpoint: calling this
        without them sends an empty request and returns the current state.
        """
        data: Dict[str, List[str]] = {}

        if add is not None:
            data["add"] = validate_tags(add)

        if delete is not None:
            # No count limit here: `delete` is a list of candidates and tags
            # that are not present are ignored, so it may legitimately be
            # longer than the per-file storage limit.
            data["delete"] = validate_tags(delete, max_count=None)

        url = self._tags_url(file_uuid)
        response_class = self._get_response_class("update")
        json_response = self._client.patch(url, json=data).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.UpdateFileTagsResponse, response)


class AddonsAPI(API):
    resource_type = "addons"
    request_type: Type[AddonExecutionGeneralRequestData] = (
        AddonExecutionGeneralRequestData
    )
    response_classes = {
        "execute": responses.AddonExecuteResponse,
        "status": responses.AddonResponse,
    }

    def _get_request_data(
        self,
        file_uuid: Union[UUID, str],
        params: Optional[Union[AddonExecutionParams, dict]] = None,
    ) -> dict:
        cleaned_params = {}
        if params:
            if isinstance(params, AddonExecutionParams):
                cleaned_params = params.model_dump(
                    exclude_unset=True, exclude_none=True
                )
            else:
                cleaned_params = params
        execution_request_data = self.request_type.model_validate(
            dict(target=str(file_uuid), params=cleaned_params)
        )
        return execution_request_data.model_dump(
            exclude_unset=True, exclude_none=True
        )

    def execute(
        self,
        file_uuid: Union[UUID, str],
        addon_name: Union[AddonLabels, str],
        params: Optional[Union[AddonExecutionParams, dict]] = None,
    ) -> responses.AddonExecuteResponse:
        if isinstance(addon_name, AddonLabels):
            addon_name = addon_name.value
        suffix = f"{addon_name}/execute"
        url = self._build_url(suffix=suffix)
        response_class = self._get_response_class("execute")
        request_payload = self._get_request_data(file_uuid, params)
        json_response = self._client.post(url, json=request_payload).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.AddonExecuteResponse, response)

    def status(
        self, request_id: Union[UUID, str], addon_name: Union[AddonLabels, str]
    ) -> responses.AddonResponse:
        if isinstance(addon_name, AddonLabels):
            addon_name = addon_name.value
        suffix = f"{addon_name}/execute/status"
        query = dict(request_id=str(request_id))
        url = self._build_url(suffix=suffix, query_parameters=query)
        response_class = self._get_response_class("status")

        json_response = self._client.get(url).json()
        response = self._parse_response(json_response, response_class)
        return cast(responses.AddonResponse, response)


class URLAPI(API):
    resource_type = ""
    response_classes = {
        "detect_faces": entities.ImageInfoWithFaces,
    }

    def detect_faces(
        self, file_uuid: Union[UUID, str]
    ) -> entities.ImageInfoWithFaces:
        url = self._build_url(file_uuid, suffix="detect_faces/")
        response_class = self._get_response_class("detect_faces")
        json_response = self._client.get(url).json()
        response = self._parse_response(json_response, response_class)
        return cast(entities.ImageInfoWithFaces, response)
