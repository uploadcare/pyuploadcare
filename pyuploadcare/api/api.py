import hashlib
import hmac
import logging
import warnings
from json import JSONDecodeError
from time import time
from typing import Any, Dict, Iterable, List, Optional, Type, Union, cast
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
)
from pyuploadcare.exceptions import (
    APIError,
    DuplicateFileError,
    InvalidRequestError,
    WebhookIsNotUnique,
)

from .entities import UUIDEntity
from .metadata import validate_meta_key, validate_meta_value, validate_metadata
from .utils import flatten_dict


logger = logging.getLogger("pyuploadcare")


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
    }

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

    def upload(  # noqa: C901
        self,
        files: RequestFiles,
        secure_upload: bool = False,
        common_metadata: Optional[dict] = None,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        store: Optional[str] = "auto",
        expire: Optional[int] = None,
    ) -> Dict[str, Any]:
        data = {}

        data["UPLOADCARE_STORE"] = store

        if public_key is None:
            public_key = self.public_key

        if common_metadata is not None:
            validate_metadata(common_metadata)
            data.update(flatten_dict(common_metadata))

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
