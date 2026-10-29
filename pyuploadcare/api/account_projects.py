"""Account-level Project API client (spec v1.0)."""

import socket
from datetime import date, datetime
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union,
)

from pydantic import EmailStr, TypeAdapter

from pyuploadcare import conf
from pyuploadcare.api.account_project_entities import (
    AccountProject,
    AccountProjectCreate,
    AccountProjectPage,
    CombinedUsage,
    MimeTypes,
    ModerationCategories,
    ModerationThreshold,
    ModerationThresholds,
    PartnerAuthorization,
    SecretKey,
    SecretKeyInfo,
    SecretKeyPage,
    UsageMetric,
)
from pyuploadcare.api.auth import BearerTokenAuth
from pyuploadcare.api.base import API, RE_SAFE_RESOURCE_ID, _iterate_pages
from pyuploadcare.api.client import Client
from pyuploadcare.api.entities import Entity
from pyuploadcare.exceptions import InvalidParamError


_USAGE_METRICS = frozenset({"traffic", "storage", "operations"})
_THRESHOLD_WRITE_FIELDS = {
    "category_id",
    "file_type",
    "threshold_percentage",
}


def _format_usage_date(value: Union[date, str]) -> str:
    if isinstance(value, datetime):
        raise InvalidParamError(
            "from_date and to_date must be a date or YYYY-MM-DD string, "
            "not a datetime"
        )
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value
    raise InvalidParamError(
        "from_date and to_date must be a date or YYYY-MM-DD string"
    )


def _build_default_client(
    token: str,
    api_base,
    verify,
    timeout,
    retry_throttled,
    user_agent_extension,
) -> Client:
    if verify is conf.DEFAULT:
        verify = conf.verify_api_ssl
    if timeout is conf.DEFAULT:
        timeout = socket.getdefaulttimeout()
    if retry_throttled is None:
        retry_throttled = conf.retry_throttled
    return Client(
        base_url=api_base or conf.api_base,
        auth=BearerTokenAuth(token),
        verify=verify,
        timeout=timeout,
        retry_throttled=retry_throttled,
        user_agent_extension=user_agent_extension,
        public_key="",
    )


class AccountProjectsAPI(API):
    """Account Project API spec v1.0, bearer token.

    Not REST ProjectAPI GET /project/.
    """

    resource_type = "projects"
    resource_id_pattern = RE_SAFE_RESOURCE_ID
    response_classes = {"default": AccountProject}

    def __init__(
        self,
        token: str,
        *,
        api_base=None,
        verify=conf.DEFAULT,
        timeout=conf.DEFAULT,
        retry_throttled=None,
        user_agent_extension=None,
        client=None,
    ):
        if not token:
            raise ValueError("token is required")
        if client is None:
            client = _build_default_client(
                token,
                api_base,
                verify,
                timeout,
                retry_throttled,
                user_agent_extension,
            )
        super().__init__(client=client, public_key="", secret_key=None)
        self.token = token

    def list_projects(
        self,
        limit: Optional[int] = None,
        request_limit: Optional[int] = None,
    ) -> Iterator[AccountProject]:
        """GET /projects/."""
        return self._iterate(
            self._collection_url(request_limit=request_limit),
            AccountProjectPage,
            limit=limit,
        )

    def create_project(self, project: AccountProjectCreate) -> AccountProject:
        """POST /projects/."""
        document = self._client.post(
            self._build_url(), json=self._dump_project(project)
        )
        return self._parse_response(document.json(), AccountProject)

    def get_project(self, pub_key: str) -> AccountProject:
        """GET /projects/{pub_key}/."""
        return self._parse_response(self._get(pub_key), AccountProject)

    def update_project(
        self, pub_key: str, project: AccountProject
    ) -> AccountProject:
        """POST /projects/{pub_key}/. The spec uses POST, not PUT."""
        document = self._client.post(
            self._build_url(pub_key), json=self._dump_project(project)
        )
        return self._parse_response(document.json(), AccountProject)

    def delete_project(self, pub_key: str) -> None:
        """DELETE /projects/{pub_key}/. 204, no JSON body."""
        self._client.delete(self._build_url(pub_key))

    def list_secrets(
        self,
        pub_key: str,
        limit: Optional[int] = None,
        request_limit: Optional[int] = None,
    ) -> Iterator[SecretKeyInfo]:
        """GET /projects/{pub_key}/secrets/."""
        url = self._collection_url(
            pub_key, suffix="secrets", request_limit=request_limit
        )
        return self._iterate(url, SecretKeyPage, limit=limit)

    def create_secret(self, pub_key: str) -> SecretKey:
        """POST /projects/{pub_key}/secrets/ with no JSON body."""
        document = self._client.post(
            self._build_url(pub_key, suffix="secrets")
        )
        return self._parse_response(document.json(), SecretKey)

    def delete_secret(self, pub_key: str, secret_id: str) -> None:
        """DELETE /projects/{pub_key}/secrets/{id}/."""
        self._validate_resource_id(secret_id)
        url = self._build_url(pub_key, suffix=f"secrets/{secret_id}")
        self._client.delete(url)

    def get_moderation_thresholds(self, pub_key: str) -> ModerationThresholds:
        """GET /projects/{pub_key}/moderation/thresholds/."""
        url = self._build_url(pub_key, suffix="moderation/thresholds")
        return self._read(url, ModerationThresholds)

    def set_moderation_thresholds(
        self,
        pub_key: str,
        thresholds: Sequence[ModerationThreshold],
    ) -> ModerationThresholds:
        """PUT /projects/{pub_key}/moderation/thresholds/."""
        body = [
            item.model_dump(mode="json", include=_THRESHOLD_WRITE_FIELDS)
            for item in thresholds
        ]
        url = self._build_url(pub_key, suffix="moderation/thresholds")
        document = self._client.put(url, json=body)
        return self._parse_response(document.json(), ModerationThresholds)

    def list_moderation_categories(self) -> ModerationCategories:
        """GET /meta/moderation/categories/."""
        url = self._build_url(base="meta/moderation/categories")
        return self._read(url, ModerationCategories)

    def list_mime_types(self) -> MimeTypes:
        """GET /meta/mime/types/."""
        url = self._build_url(base="meta/mime/types")
        return self._read(url, MimeTypes)

    def get_combined_usage(
        self,
        pub_key: str,
        *,
        from_date: Union[date, str],
        to_date: Union[date, str],
    ) -> CombinedUsage:
        """GET /projects/{pub_key}/usage/."""
        url = self._build_url(
            pub_key,
            suffix="usage",
            query_parameters=self._usage_query(from_date, to_date),
        )
        return self._read(url, CombinedUsage)

    def get_usage_metric(
        self,
        pub_key: str,
        metric: str,
        *,
        from_date: Union[date, str],
        to_date: Union[date, str],
    ) -> UsageMetric:
        """GET /projects/{pub_key}/usage/{metric}/."""
        if metric not in _USAGE_METRICS:
            raise InvalidParamError(
                "metric must be one of: traffic, storage, operations"
            )
        url = self._build_url(
            pub_key,
            suffix=f"usage/{metric}",
            query_parameters=self._usage_query(from_date, to_date),
        )
        return self._read(url, UsageMetric)

    def authorize_partner(
        self,
        *,
        email: str,
        pub_keys: Sequence[str],
        redirect_to_pub_key: Optional[str] = None,
        response_type: str = "partner_redirect",
    ) -> PartnerAuthorization:
        """GET /oauth/authorize/."""
        params = _partner_query(
            email=email,
            pub_keys=pub_keys,
            redirect_to_pub_key=redirect_to_pub_key,
            response_type=response_type,
        )
        url = self._build_url(base="oauth/authorize")
        document = self._client.get(url, params=params)
        return self._parse_response(document.json(), PartnerAuthorization)

    def _dump_project(self, project: AccountProject) -> Dict[str, Any]:
        data = project.model_dump(
            mode="json",
            exclude_unset=True,
            exclude={"pub_key", "is_shared_project"},
        )
        features = data.get("features")
        if isinstance(features, dict) and "team_members" in features:
            features.pop("team_members")
            if not features:
                data.pop("features")
        return data

    def _collection_url(
        self,
        pub_key: Optional[str] = None,
        suffix: Optional[str] = None,
        request_limit: Optional[int] = None,
    ) -> str:
        query = None
        if request_limit is not None:
            query = {"limit": request_limit}
        return self._build_url(pub_key, suffix=suffix, query_parameters=query)

    def _iterate(
        self,
        url: str,
        page_class: Type[Entity],
        limit: Optional[int] = None,
    ) -> Iterator[Any]:
        return _iterate_pages(
            url,
            lambda page_url: self._client.get(page_url).json(),
            lambda raw: self._parse_response(raw, page_class),
            limit=limit,
        )

    def _read(self, url: str, response_class: Type[Entity]) -> Any:
        return self._parse_response(
            self._client.get(url).json(), response_class
        )

    def _usage_query(
        self, from_date: Union[date, str], to_date: Union[date, str]
    ) -> Dict[str, str]:
        return {
            "from": _format_usage_date(from_date),
            "to": _format_usage_date(to_date),
        }


def _partner_query(
    *,
    email: str,
    pub_keys: Sequence[str],
    redirect_to_pub_key: Optional[str],
    response_type: str,
) -> List[Tuple[str, Union[str, int, float, bool, None]]]:
    if response_type != "partner_redirect":
        raise InvalidParamError("response_type must be partner_redirect")
    if not pub_keys:
        raise InvalidParamError("pub_keys must be non-empty")
    TypeAdapter(EmailStr).validate_python(email)
    params: List[Tuple[str, Union[str, int, float, bool, None]]] = [
        ("response_type", response_type),
        ("email", email),
    ]
    params.extend(("pub_key", pub_key) for pub_key in pub_keys)
    if redirect_to_pub_key is not None:
        params.append(("redirect_to_pub_key", redirect_to_pub_key))
    return params
