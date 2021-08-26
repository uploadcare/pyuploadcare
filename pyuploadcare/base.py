from typing import Dict, Optional, Protocol, Type, Union
from urllib.parse import urljoin
from uuid import UUID

from httpx._types import RequestFiles, URLTypes

from pyuploadcare.auth import AuthBase, UploadcareSimpleAuth
from pyuploadcare.client import Client
from pyuploadcare.config import settings
from pyuploadcare.entities import Entity, UUIDEntity


class API:
    resource_type: str
    entity_class: Type[Entity]

    def __init__(
        self,
        base_url: URLTypes = settings.BASE_URL,
        client: Optional[Client] = None,
        auth: Optional[AuthBase] = None,
    ) -> None:
        if auth is None:
            auth = UploadcareSimpleAuth(
                settings.PUBLIC_KEY, settings.SECRET_KEY
            )
        if client is None:
            client = Client(base_url=base_url, auth=auth)
        self._client = client

    def _resource_to_entity(self, resource: dict) -> Entity:
        entity = self.entity_class.parse_obj(resource)
        entity._fetched = True
        return entity

    def _build_url(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        suffix: Optional[str] = None,
    ) -> str:
        url = urljoin(str(self._client.base_url), self.resource_type) + "/"
        if resource_uuid is not None:
            if isinstance(resource_uuid, UUIDEntity):
                resource_uuid = resource_uuid.uuid
            url = urljoin(url, str(resource_uuid)) + "/"
        if suffix:
            url = urljoin(url, suffix) + "/"
        return url

    def _post(
        self, data: Optional[Dict] = None, files: Optional[RequestFiles] = None
    ) -> dict:
        url = self._build_url()
        document = self._client.post(url, json=data, files=files)
        return document.json()

    def _get(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
    ) -> dict:
        url = self._build_url(resource_uuid)
        document = self._client.get(url)
        return document.json()

    def _put(
        self,
        resource_uuid: Union[UUID, str, UUIDEntity] = None,
        data: Optional[Dict] = None,
    ) -> dict:
        url = self._build_url(resource_uuid)
        document = self._client.put(url, json=data)
        return document.json()

    def _delete(
        self, resource_uuid: Union[UUID, str, UUIDEntity] = None
    ) -> dict:
        url = self._build_url(resource_uuid)
        document = self._client.delete(url)
        return document.json()


class APIProtocol(Protocol):
    def _resource_to_entity(self, resource: dict) -> Entity:
        ...

    def _post(self, data: Optional[Dict] = None) -> dict:
        ...

    def _get(
        self, resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None
    ) -> dict:
        ...

    def _put(
        self,
        resource_uuid: Union[UUID, str, UUIDEntity] = None,
        data: Optional[Dict] = None,
    ) -> dict:
        ...

    def _delete(
        self, resource_uuid: Union[UUID, str, UUIDEntity] = None
    ) -> dict:
        ...


class RetrieveMixin(APIProtocol):
    def retrieve(
        self,
        resource_uuid: Union[UUID, str, UUIDEntity],
    ):
        if isinstance(resource_uuid, UUIDEntity):
            resource_uuid = resource_uuid.uuid

        document = self._get(resource_uuid)
        return self._resource_to_entity(document)


class ListMixin(APIProtocol):
    def list(
        self,
    ):
        document = self._get()
        for resource in document["results"]:
            yield self._resource_to_entity(resource)


class CreateMixin(APIProtocol):
    def create(
        self,
        data: Optional[Dict] = None,
    ):
        document = self._post(data)
        return self._resource_to_entity(document)


class UpdateMixin(APIProtocol):
    def update(
        self,
        resource_uuid: Union[UUID, str, UUIDEntity],
        data: Optional[Dict] = None,
    ):
        document = self._put(resource_uuid, data)
        return self._resource_to_entity(document)


class DeleteMixin(APIProtocol):
    def delete(self, resource_uuid: Union[UUID, str, UUIDEntity]):
        document = self._delete(resource_uuid)
        return self._resource_to_entity(document)
