from typing import Dict, Optional, Protocol, Type, Union
from urllib.parse import urljoin
from uuid import UUID

from httpx._types import URLTypes

from pyuploadcare.auth import AuthBase
from pyuploadcare.client import Client
from pyuploadcare.entities import Entity, UUIDEntity


class API:
    resource_type: str
    entity_class: Type[UUIDEntity]

    def __init__(
        self,
        base_url: URLTypes,
        client: Optional[Client] = None,
        auth: Optional[AuthBase] = None,
    ) -> None:
        if not (base_url and auth or client):
            raise ValueError("client or auth and base_url are required")

        if not client:
            client = Client(base_url=base_url, auth=auth)
        self._client = client

    def _resource_to_entity(self, resource: dict) -> UUIDEntity:
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
        self,
        data: Optional[Dict] = None,
    ) -> dict:
        url = self._build_url()
        document = self._client.post(url, json=data)
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
    def _resource_to_entity(self, resource: dict) -> UUIDEntity:
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
