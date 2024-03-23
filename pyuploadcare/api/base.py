from typing import Any, Dict, Optional, Type, Union, cast
from urllib.parse import urlencode, urljoin
from uuid import UUID

from httpx._types import RequestFiles
from pydantic import TypeAdapter
from typing_extensions import Protocol, TypeVar

from pyuploadcare.api.client import Client
from pyuploadcare.api.entities import Entity, UUIDEntity
from pyuploadcare.api.responses import PaginatedResponse, Response
from pyuploadcare.exceptions import DefaultResponseClassNotDefined


ResponseOrEntity = TypeVar("ResponseOrEntity", bound=Union[Response, Entity])


class API:
    resource_type: str
    response_classes: Dict[str, Union[Type[Response], Type[Entity]]]
    _client: Client

    def __init__(
        self,
        client: Client,
        public_key: str,
        secret_key: Optional[str] = None,
        signed_uploads_ttl: int = 60,
    ) -> None:
        self.public_key = public_key
        self.secret_key = secret_key
        self.signed_uploads_ttl = signed_uploads_ttl
        self._client = client

    def _parse_response(
        self,
        raw_resource: Dict[str, Any],
        response_class: Type[ResponseOrEntity],
    ) -> ResponseOrEntity:
        return TypeAdapter(response_class).validate_python(raw_resource)

    def _build_url(  # noqa: C901
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        base: Optional[str] = None,
        suffix: Optional[str] = None,
        query_parameters: Optional[Dict[str, Any]] = None,
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
        if query_parameters:
            url += "?" + urlencode(query_parameters)
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
    ) -> Dict[str, Any]:
        url = self._build_url()
        document = self._client.post(url, data=data, files=files)
        return document.json()

    def _get(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        **query_parameters,
    ) -> Dict[str, Any]:
        url = self._build_url(resource_uuid, query_parameters=query_parameters)
        document = self._client.get(url)
        return document.json()

    def _put(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        url = self._build_url(resource_uuid)
        document = self._client.put(url, json=data)
        return document.json()

    def _delete(
        self, resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None
    ) -> None:
        url = self._build_url(resource_uuid)
        self._client.delete(url)

    def _delete_with_response(
        self, resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None
    ) -> Dict[str, Any]:
        url = self._build_url(resource_uuid, suffix="storage")
        document = self._client.delete(url)
        return document.json()


class APIProtocol(Protocol):
    resource_type: str
    response_classes: Dict[str, Union[Type[Response], Type[Entity]]]
    _client: Client

    def _parse_response(
        self,
        raw_resource: Dict[str, Any],
        response_class: Type[ResponseOrEntity],
    ) -> ResponseOrEntity: ...

    def _build_url(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        base: Optional[str] = None,
        suffix: Optional[str] = None,
        query_parameters: Optional[Dict[str, Any]] = None,
    ) -> str: ...

    def _get_response_class(
        self, action: str
    ) -> Union[Type[Response], Type[Entity]]: ...

    def _post(self, data: Optional[Dict] = None) -> Dict[str, Any]: ...

    def _get(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        **query_parameters,
    ) -> Dict[str, Any]: ...

    def _put(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        data: Optional[Dict] = None,
    ) -> Dict[str, Any]: ...

    def _delete(
        self, resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None
    ) -> None: ...

    def _delete_with_response(
        self, resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None
    ) -> Dict[str, Any]: ...


class RetrieveMixin(APIProtocol):
    def retrieve(
        self,
        resource_uuid: Optional[Union[UUID, str, UUIDEntity]] = None,
        include_appdata: bool = False,
    ):
        response_class = self._get_response_class("retrieve")

        if isinstance(resource_uuid, UUIDEntity):
            resource_uuid = resource_uuid.uuid

        query_params = {}
        if include_appdata:
            query_params["include"] = "appdata"

        json_response = self._get(resource_uuid, **query_params)
        return self._parse_response(json_response, response_class)


class ListMixin(APIProtocol):
    def list(  # noqa: C901
        self,
        limit=None,
        request_limit=None,
        **query_parameters,
    ):
        response_class = self._get_response_class("list")

        if request_limit is not None:
            query_parameters["limit"] = request_limit

        next_: Optional[str] = self._build_url(
            query_parameters=query_parameters
        )

        while next_:
            document = self._client.get(next_)
            json_response = document.json()
            response = self._parse_response(json_response, response_class)

            if hasattr(response, "results"):
                results = response.results
            else:
                results = response

            for item in results:
                if limit is not None and limit <= 0:
                    break

                yield item

                if limit is not None:
                    limit -= 1

            if limit is not None and limit <= 0:
                break

            next_ = None
            if hasattr(response, "next"):
                next_ = response.next


class CountMixin(APIProtocol):
    def count(
        self,
        request_limit=None,
        **query_parameters,
    ) -> int:
        if request_limit is not None:
            query_parameters["limit"] = request_limit

        response_class = self._get_response_class("list")
        json_response = self._get(query_parameters=query_parameters)
        response = self._parse_response(json_response, response_class)
        response = cast(PaginatedResponse, response)
        return response.total


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
        self._delete(resource_uuid)


class DeleteWithResponseMixin(APIProtocol):
    def delete(self, resource_uuid: Union[UUID, str, UUIDEntity]):
        response_class = self._get_response_class("delete")

        json_response = self._delete_with_response(resource_uuid)
        return self._parse_response(json_response, response_class)


class ListCountMixin(ListMixin, CountMixin):
    pass
