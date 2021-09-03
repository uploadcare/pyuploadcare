from pyuploadcare.exceptions import DefaultResponseClassNotDefined
from pyuploadcare.response import Response
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
    response_classes: Dict[str, Union[Type[Response], Type[Entity]]]

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

    def _parse_response(
        self,
        raw_resource: dict,
        response_class: Union[Type[Response], Type[Entity]],
    ) -> Union[Response, Entity]:
        response = response_class.parse_obj(raw_resource)
        return response

    def _build_url(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        base: Optional[str] = None,
        suffix: Optional[str] = None,
    ) -> str:
        if base is not None:
            url = urljoin(str(self._client.base_url), base) + "/"
        else:
            url = urljoin(str(self._client.base_url), self.resource_type) + "/"
        if resource_uuid is not None:
            if isinstance(resource_uuid, UUIDEntity):
                resource_uuid = resource_uuid.uuid
            url = urljoin(url, str(resource_uuid)) + "/"
        if suffix:
            url = urljoin(url, suffix) + "/"
        return url

    def _get_response_class(
        self, action: str
    ) -> Union[Type[Response], Type[Entity]]:
        response_class = self.response_classes.get(
            action, self.response_classes.get("default")
        )
        if response_class is None:
            raise DefaultResponseClassNotDefined
        return response_class

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
    resource_type: str
    response_classes: Dict[str, Union[Type[Response], Type[Entity]]]

    def _parse_response(
        self,
        raw_resource: dict,
        response_class: Union[Type[Response], Type[Entity]],
    ) -> Union[Response, Entity]:
        ...

    def _build_url(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        base: Optional[str] = None,
        suffix: Optional[str] = None,
    ) -> str:
        ...

    def _get_response_class(
        self, action: str
    ) -> Union[Type[Response], Type[Entity]]:
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
        response_class = self._get_response_class("retrieve")

        if isinstance(resource_uuid, UUIDEntity):
            resource_uuid = resource_uuid.uuid

        json_response = self._get(resource_uuid)
        return self._parse_response(json_response, response_class)


class ListMixin(APIProtocol):
    def list(
        self,
    ):
        response_class = self._get_response_class("list")

        json_response = self._get()
        return self._parse_response(json_response, response_class)


class CreateMixin(APIProtocol):
    def create(
        self,
        data: Optional[Dict] = None,
    ):
        response_class = self._get_response_class("create")

        json_response = self._post(data)
        return self._parse_response(json_response, response_class)


class UpdateMixin(APIProtocol):
    def update(
        self,
        resource_uuid: Union[UUID, str, UUIDEntity],
        data: Optional[Dict] = None,
    ):
        response_class = self._get_response_class("update")

        json_response = self._put(resource_uuid, data)
        return self._parse_response(json_response, response_class)


class DeleteMixin(APIProtocol):
    def delete(self, resource_uuid: Union[UUID, str, UUIDEntity]):
        response_class = self._get_response_class("update")

        json_response = self._delete(resource_uuid)
        return self._parse_response(json_response, response_class)
