import hashlib
import hmac
from time import time
from typing import Iterable, Optional, Union
from uuid import UUID

from httpx._types import RequestFiles

from pyuploadcare import entities
from pyuploadcare.base import (
    API,
    CreateMixin,
    DeleteMixin,
    ListMixin,
    RetrieveMixin,
)
from pyuploadcare.config import settings


class FilesAPI(API, ListMixin, RetrieveMixin, DeleteMixin):
    resource_type = "files"
    entity_class = entities.FileInfo

    def store(self, file_uuid: Union[UUID, str]) -> entities.Entity:
        url = self._build_url(file_uuid, suffix="storage")
        document = self._client.put(url).json()
        return self._resource_to_entity(document)

    def batch_store(
        self, file_uuids: Iterable[Union[UUID, str]]
    ) -> Iterable[entities.Entity]:
        url = self._build_url(suffix="storage")
        document = self._client.put(url, json=file_uuids).json()
        for resource in document["results"]:
            yield self._resource_to_entity(resource)

    def batch_delete(self, file_uuids: Iterable) -> Iterable[entities.Entity]:
        url = self._build_url(suffix="storage")
        document = self._client.delete_with_payload(
            url, json=file_uuids
        ).json()
        for resource in document["results"]:
            yield self._resource_to_entity(resource)

    def local_copy(
        self, source: Union[UUID, str], store: bool = False
    ) -> entities.Entity:
        url = self._build_url(suffix="local_copy")
        data = {"source": source, "store": store}
        document = self._client.post(url, json=data).json()
        return document["result"]

    def remote_copy(
        self,
        source: Union[UUID, str],
        target: str,
        make_public: bool = True,
        pattern: str = "${default}",
    ) -> entities.Entity:
        url = self._build_url(suffix="remote_copy")
        data = {
            "source": source,
            "target": target,
            "make_public": make_public,
            "pattern": pattern,
        }
        document = self._client.post(url, json=data).json()
        return document["result"]


class GroupsAPI(API, ListMixin, RetrieveMixin):
    resource_type = "groups"
    entity_class = entities.GroupInfo

    def store(self, file_uuid: Union[UUID, str]) -> entities.Entity:
        url = self._build_url(file_uuid, suffix="storage")
        document = self._client.put(url).json()
        return self._resource_to_entity(document)


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
        return self._resource_to_entity(document["result"])

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
        return self._resource_to_entity(document["result"])

    def status(self, video_convert_info: entities.VideoConvertInfo):
        url = self._build_url(suffix=f"status/{video_convert_info.token}")
        document = self._client.get(url).json()
        return self._resource_to_entity(document["result"])


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
        store: Optional[str] = None,
        expire: Optional[int] = None,
    ):
        data = {}

        data["UPLOADCARE_STORE"] = store

        if public_key is None:
            data["UPLOADCARE_PUB_KEY"] = settings.PUBLIC_KEY

        if secure_upload:
            if secret_key is None:
                secret_key = settings.SECRET_KEY

            if expire is None:
                expire = (
                    int(time()) + settings.SECURE_UPLOAD_DEFAULT_EXPIRE_DELTA
                )
            data["expire"] = str(expire)

            signature = self._generate_secure_signature(secret_key, expire)
            data["signature"] = signature
        return self._post(data=data, files=files)

    def start_multipart_upload(
        self,
        file_name: str,
        file_size: int,
        content_type: str,
        secure_upload: bool = False,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        store: Optional[str] = None,
        expire: Optional[int] = None,
    ):
        data = {}

        data["filename"] = file_name
        data["size"] = str(file_size)
        data["content_type"] = content_type

        if store is not None:
            data["UPLOADCARE_STORE"] = store

        data["UPLOADCARE_PUB_KEY"] = (
            settings.PUBLIC_KEY if public_key is None else public_key
        )

        if secure_upload:
            if secret_key is None:
                secret_key = settings.SECRET_KEY

            expire = (
                (int(time()) + settings.SECURE_UPLOAD_DEFAULT_EXPIRE_DELTA)
                if expire is None
                else expire
            )
            data["expire"] = str(expire)

            data["signature"] = self._generate_secure_signature(
                secret_key, expire
            )

        url = self._build_url(base="multipart/start")
        document = self._client.post(url, json=data)
        return document.json()

    def multipart_upload_chunk(self, url: str, chunk: bytes):
        document = self._client.put(
            url,
            content=chunk,
            headers={"Content-Type": "application/octet-stream"},
        )
        return document.content

    def multipart_complete(self, uuid: UUID, public_key: Optional[str] = None):
        data = {"uuid": str(uuid)}

        data["UPLOADCARE_PUB_KEY"] = (
            settings.PUBLIC_KEY if public_key is None else public_key
        )

        url = self._build_url(base="multipart/complete")
        document = self._client.post(url, json=data)
        return document.json()
