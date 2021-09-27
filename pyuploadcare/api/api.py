import hashlib
import hmac
from time import time
from typing import Any, Dict, Iterable, List, Optional, Union
from uuid import UUID

from httpx._types import RequestFiles, URLTypes

from pyuploadcare import conf
from pyuploadcare.api import entities, response
from pyuploadcare.api.base import (
    API,
    CreateMixin,
    DeleteMixin,
    ListCountMixin,
    ListMixin,
    RetrieveMixin,
)
from pyuploadcare.api.client import Client, get_timeout
from pyuploadcare.exceptions import APIError


class FilesAPI(API, ListCountMixin, RetrieveMixin, DeleteMixin):  # type: ignore
    resource_type = "files"
    response_classes = {
        "retrieve": entities.FileInfo,
        "list": response.FileListResponse,
        "count": response.FileListResponse,
        "store": entities.FileInfo,
        "update": entities.FileInfo,
        "batch_store": response.BatchFileOperationResponse,
        "batch_delete": response.BatchFileOperationResponse,
        "local_copy": response.CreateLocalCopyResponse,
        "remote_copy": response.CreateRemoteCopyResponse,
    }

    def store(
        self, file_uuid: Union[UUID, str]
    ) -> Union[response.Response, entities.Entity]:
        url = self._build_url(file_uuid, suffix="storage")
        response_class = self._get_response_class("store")
        json_response = self._client.put(url).json()
        return self._parse_response(json_response, response_class)

    def batch_store(
        self, file_uuids: Iterable[Union[UUID, str]]
    ) -> Union[response.Response, entities.Entity]:
        url = self._build_url(suffix="storage")
        response_class = self._get_response_class("batch_store")
        json_response = self._client.put(url, json=file_uuids).json()
        return self._parse_response(json_response, response_class)

    def batch_delete(
        self, file_uuids: Iterable
    ) -> Union[response.Response, entities.Entity]:
        url = self._build_url(suffix="storage")
        response_class = self._get_response_class("batch_delete")
        json_response = self._client.delete_with_payload(
            url, json=file_uuids
        ).json()
        return self._parse_response(json_response, response_class)

    def local_copy(
        self, source: Union[UUID, str], store: bool = False
    ) -> response.CreateLocalCopyResponse:
        url = self._build_url(suffix="local_copy")
        data = {"source": source, "store": store}
        response_class = self._get_response_class("local_copy")
        json_response = self._client.post(url, json=data).json()
        return self._parse_response(json_response, response_class)  # type: ignore

    def remote_copy(
        self,
        source: Union[UUID, str],
        target: str,
        make_public: bool = True,
        pattern: str = "${default}",
    ) -> response.CreateRemoteCopyResponse:
        url = self._build_url(suffix="remote_copy")
        data = {
            "source": source,
            "target": target,
            "make_public": make_public,
            "pattern": pattern,
        }
        response_class = self._get_response_class("remote_copy")
        json_response = self._client.post(url, json=data).json()
        return self._parse_response(json_response, response_class)  # type: ignore


class GroupsAPI(API, ListCountMixin, RetrieveMixin):
    resource_type = "groups"
    entity_class = entities.GroupInfo

    response_classes = {
        "retrieve": entities.GroupInfo,
        "list": response.GroupListResponse,
        "count": response.GroupListResponse,
    }

    def store(self, file_uuid: Union[UUID, str]) -> entities.Entity:
        url = self._build_url(file_uuid, suffix="storage")
        return self._client.put(url).json()


class ProjectAPI(API, RetrieveMixin):
    resource_type = "project"
    entity_class = entities.ProjectInfo


class WebhooksAPI(API, CreateMixin, ListMixin, RetrieveMixin, DeleteMixin):
    resource_type = "webhooks"
    entity_class = entities.WebhookInfo


class DocumentConvertAPI(API):
    resource_type = "convert/document"
    entity_class = entities.DocumentConvertInfo

    def convert(
        self, input_document: entities.DocumentConvertInput
    ) -> entities.Entity:
        url = self._build_url()
        document = self._client.post(url, json=input_document.dict()).json()
        return self._parse_response(document["result"])  # type: ignore

    def status(
        self, document_convert_info: entities.DocumentConvertInfo
    ) -> entities.DocumentConvertStatus:
        url = self._build_url(suffix=f"status/{document_convert_info.token}")
        document = self._client.get(url).json()
        return entities.DocumentConvertStatus.parse_obj(document["result"])


class VideoConvertAPI(API):
    resource_type = "convert/video"
    entity_class = entities.VideoConvertInfo

    def convert(
        self, input_document: entities.VideoConvertInput
    ) -> entities.Entity:
        url = self._build_url()
        document = self._client.post(url, json=input_document.dict()).json()
        return self._parse_response(document["result"])  # type: ignore

    def status(self, video_convert_info: entities.VideoConvertInfo):
        url = self._build_url(suffix=f"status/{video_convert_info.token}")
        document = self._client.get(url).json()
        return self._parse_response(document["result"])  # type: ignore


class UploadAPI(API):
    resource_type = "base"

    def __init__(
        self,
        base_url: URLTypes = conf.upload_base,
        client: Optional[Client] = None,
    ) -> None:
        if client is None:
            client = Client(
                base_url=base_url,
                verify=conf.verify_upload_ssl,
                timeout=get_timeout(conf.timeout),
            )
        self._client = client

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
            public_key = conf.pub_key

        data["UPLOADCARE_PUB_KEY"] = public_key

        if secure_upload:
            if secret_key is None:
                secret_key = conf.secret

            if expire is None:
                expire = int(time()) + conf.signed_uploads_ttl
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
            "UPLOADCARE_PUB_KEY": conf.pub_key,
        }

        if store is not None:
            data["UPLOADCARE_STORE"] = store

        if secure_upload:
            expire = (
                (int(time()) + conf.signed_uploads_ttl)
                if expire is None
                else expire
            )

            data["expire"] = str(expire)
            data["signature"] = self._generate_secure_signature(
                conf.secret, expire  # type: ignore
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
            "UPLOADCARE_PUB_KEY": conf.pub_key,
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
            "pub_key": conf.pub_key,
        }
        if filename:
            data["filename"] = filename

        if secure_upload:
            expire = (
                (int(time()) + conf.signed_uploads_ttl)
                if expire is None
                else expire
            )

            data["expire"] = str(expire)
            data["signature"] = self._generate_secure_signature(
                conf.secret, expire  # type: ignore
            )

        url = self._build_url(base="/from_url/")
        document = self._client.post(url, data=data)
        response = document.json()
        if "token" not in response:
            raise APIError(
                "could not find token in result: {0}".format(response)
            )
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
            raise APIError(
                "could not find status in result: {0}".format(response)
            )
        return response

    def create_group(
        self,
        files: List[Union[str, UUID]],
        secure_upload: bool = False,
        expire: Optional[int] = None,
    ):
        data = {
            "pub_key": conf.pub_key,
        }

        for index, file in enumerate(files):
            data[f"files[{index}]"] = file  # type: ignore

        if secure_upload:
            expire = (
                (int(time()) + conf.signed_uploads_ttl)
                if expire is None
                else expire
            )

            data["expire"] = str(expire)
            data["signature"] = self._generate_secure_signature(
                conf.secret, expire  # type: ignore
            )

        url = self._build_url(base="/group/")
        document = self._client.post(url, data=data)
        return document.json()
