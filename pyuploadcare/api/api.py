import hashlib
import hmac
from time import time
from typing import Any, Dict, Iterable, List, Optional, Union, cast
from uuid import UUID

from httpx._types import RequestFiles

from pyuploadcare.api import entities, responses
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
from pyuploadcare.exceptions import APIError


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


class GroupsAPI(API, ListCountMixin, RetrieveMixin):
    resource_type = "groups"
    entity_class = entities.GroupInfo

    response_classes = {
        "retrieve": entities.GroupInfo,
        "list": responses.GroupListResponse,
        "count": responses.GroupListResponse,
    }

    def store(self, file_uuid: Union[UUID, str]) -> Dict[str, Any]:
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


class DocumentConvertAPI(API):
    resource_type = "convert/document"
    entity_class = entities.DocumentConvertInfo

    response_classes = {
        "convert": responses.DocumentConvertResponse,
        "status": entities.DocumentConvertStatus,
    }

    def convert(
        self,
        paths: List[str],
        store: Optional[bool] = None,
    ) -> responses.DocumentConvertResponse:
        url = self._build_url()

        data = {
            "paths": paths,
        }
        if isinstance(store, bool):
            data["store"] = str(store).lower()  # type: ignore

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
    def _generate_secure_signature(secret: str, expire: int):
        return hmac.new(
            secret.encode("utf-8"), str(expire).encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def upload(
        self,
        files: RequestFiles,
        secure_upload: bool = False,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        store: Optional[str] = "auto",
        expire: Optional[int] = None,
    ) -> Dict[str, Any]:
        data = {}

        data["UPLOADCARE_STORE"] = store

        if public_key is None:
            public_key = self.public_key

        data["UPLOADCARE_PUB_KEY"] = public_key

        if secure_upload:
            if secret_key is None:
                secret_key = self.secret_key

            if expire is None:
                expire = int(time()) + self.signed_uploads_ttl
            data["expire"] = str(expire)

            signature = self._generate_secure_signature(secret_key, expire)  # type: ignore
            data["signature"] = signature

        url = self._build_url()
        document = self._client.post(url, data=data, files=files)
        return document.json()

    def start_multipart_upload(
        self,
        file_name: str,
        file_size: int,
        content_type: str,
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

        if secure_upload:
            expire = (
                (int(time()) + self.signed_uploads_ttl)
                if expire is None
                else expire
            )

            data["expire"] = str(expire)
            data["signature"] = self._generate_secure_signature(
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

    def upload_from_url(
        self,
        source_url,
        store="auto",
        filename=None,
        secure_upload: bool = False,
        expire: Optional[int] = None,
    ) -> str:
        data = {
            "source_url": source_url,
            "store": store,
            "pub_key": self.public_key,
        }
        if filename:
            data["filename"] = filename

        if secure_upload:
            expire = (
                (int(time()) + self.signed_uploads_ttl)
                if expire is None
                else expire
            )

            data["expire"] = str(expire)
            data["signature"] = self._generate_secure_signature(
                self.secret_key, expire  # type: ignore
            )

        url = self._build_url(base="/from_url")
        document = self._client.post(url, data=data)
        response = document.json()
        if "token" not in response:
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
            data["signature"] = self._generate_secure_signature(
                self.secret_key, expire  # type: ignore
            )

        url = self._build_url(base="/group/")
        document = self._client.post(url, data=data)
        return document.json()
