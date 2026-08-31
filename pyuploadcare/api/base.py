from typing import Any, Callable, Dict, Iterator, Optional, Type, Union, cast
from urllib.parse import urlencode, urljoin, urlsplit
from uuid import UUID

from pydantic import TypeAdapter
from typing_extensions import Protocol, TypeVar

from pyuploadcare.api._httpx import RequestFiles
from pyuploadcare.api.client import Client
from pyuploadcare.api.entities import Entity, UUIDEntity
from pyuploadcare.api.responses import PaginatedResponse, Response
from pyuploadcare.exceptions import (
    DefaultResponseClassNotDefined,
    InvalidRequestError,
)


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


def _iterate_pages(  # noqa: C901
    first_url: str,
    fetch_page: Callable[[str], Dict[str, Any]],
    parse: Callable[[Dict[str, Any]], Any],
    limit: Optional[int] = None,
) -> Iterator[Any]:
    """Walk a paginated endpoint, yielding up to ``limit`` results.

    Fetching is delegated to ``fetch_page`` so that endpoints paged with a
    ``GET`` and endpoints paged by re-sending a ``POST`` body share the same
    engine: the loop only decides *which* URL to request, following the
    response's ``next`` URL until it runs out.

    ``next`` is only followed within the origin of ``first_url``: the HTTP
    client attaches credentials to whatever URL it is given, so a foreign
    ``next`` (a compromised or misbehaving server) fails loudly instead of
    leaking them.
    """
    origin = urlsplit(first_url)[:2]
    next_: Optional[str] = first_url

    while next_:
        response = parse(fetch_page(next_))
        results = getattr(response, "results", response)

        for item in results:
            if limit is not None and limit <= 0:
                break

            yield item

            if limit is not None:
                limit -= 1

        if limit is not None and limit <= 0:
            break

        # An empty page cannot get any fuller further on; stop even if the
        # server claims there is more.
        if not results:
            break

        next_ = getattr(response, "next", None)
        if next_ and urlsplit(next_)[:2] != origin:
            raise InvalidRequestError(
                f"refusing to follow `next` outside {origin[1]}: {next_}"
            )


class ListMixin(APIProtocol):
    def list(
        self,
        limit=None,
        request_limit=None,
        **query_parameters,
    ):
        response_class = self._get_response_class("list")

        if request_limit is not None:
            query_parameters["limit"] = request_limit

        first_url = self._build_url(query_parameters=query_parameters)

        return _iterate_pages(
            first_url,
            lambda url: self._client.get(url).json(),
            lambda raw: self._parse_response(raw, response_class),
            limit=limit,
        )


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
