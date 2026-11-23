"""Project API endpoints.

The Project API works with every project the user owns or is a team member
of, where the REST API works with one project. Requests are authorized with
the user's OAuth access token (``pyuploadcare.api.auth.UploadcareOAuth``).
"""

import re
from datetime import date, datetime, timezone
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Pattern,
    Union,
    cast,
)

from pydantic import ValidationError

from pyuploadcare.api.base import API, _iterate_pages
from pyuploadcare.api.client import Client
from pyuploadcare.api.project_entities import (
    CombinedUsage,
    ModerationThreshold,
    ModerationThresholdsResponse,
    Project,
    ProjectListResponse,
    UsageMetric,
    UsageMetricName,
)
from pyuploadcare.api.utils import require_optional_int, require_range
from pyuploadcare.exceptions import InvalidParamError
from pyuploadcare.helpers import ensure_aware_datetime


# Maximum page size of the list endpoints.
PROJECT_API_MAX_PAGE_SIZE = 100

# Characters the server accepts in a project public key.
RE_PUB_KEY: Pattern[str] = re.compile(r"[a-zA-Z0-9_]+\Z")


ProjectOrPubKey = Union[Project, str]
ProjectPayload = Union[Project, Dict[str, Any]]
DateLike = Union[date, datetime, str]


def _pub_key(project: ProjectOrPubKey) -> str:
    if isinstance(project, Project):
        if not project.pub_key:
            raise InvalidParamError("project has no `pub_key`")
        return project.pub_key
    return project


def validate_project_data(data: ProjectPayload) -> Project:
    """Validate request data as a ``Project``.

    A dict is validated strictly: a misspelled key raises an error rather
    than being dropped.
    """
    if isinstance(data, Project):
        return data
    if not isinstance(data, dict):
        raise InvalidParamError(
            "project data must be a `Project` or a dict, "
            f"got {type(data).__name__}"
        )
    try:
        return Project.model_validate(data, extra="forbid")
    except ValidationError as exc:
        raise InvalidParamError(f"Invalid project data: {exc}") from exc


def _project_payload(data: ProjectPayload) -> Dict[str, Any]:
    return validate_project_data(data).to_payload()


def _utc_date(name: str, value: datetime) -> date:
    # The server counts days in UTC.
    try:
        aware = ensure_aware_datetime(value)
    except ValueError:
        raise InvalidParamError(
            f"`{name}` must be a timezone-aware datetime, got {value!r}"
        ) from None
    return aware.astimezone(timezone.utc).date()


def _to_date(name: str, value: DateLike) -> date:
    # `datetime` is a subclass of `date`, so check it first.
    if isinstance(value, datetime):
        return _utc_date(name, value)
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise InvalidParamError(
            f"`{name}` must be a date or an ISO 8601 date string "
            f"(YYYY-MM-DD), got {value!r}"
        )


def _validate_threshold(
    item: Union[ModerationThreshold, Dict[str, Any]],
) -> ModerationThreshold:
    try:
        return ModerationThreshold.model_validate(item, extra="forbid")
    except ValidationError as exc:
        raise InvalidParamError(
            f"Invalid moderation threshold {item!r}: {exc}"
        ) from exc


def _check_page_limits(
    limit: Optional[int], request_limit: Optional[int]
) -> None:
    require_optional_int("limit", limit)
    require_optional_int("request_limit", request_limit)
    require_range("limit", limit, minimum=0)
    require_range(
        "request_limit",
        request_limit,
        minimum=1,
        maximum=PROJECT_API_MAX_PAGE_SIZE,
    )


class ProjectAPIBase(API):
    """Base for Project API endpoints.

    Takes only the HTTP client, which carries the OAuth access token. Project
    API requests need no project key pair.
    """

    resource_type = "projects"
    resource_id_pattern = RE_PUB_KEY

    def __init__(self, client: Client) -> None:
        super().__init__(client=client, public_key="")

    def _project_url(
        self,
        project: ProjectOrPubKey,
        suffix: Optional[str] = None,
        query_parameters: Optional[Dict[str, Any]] = None,
    ) -> str:
        return self._build_url(
            _pub_key(project),
            suffix=suffix,
            query_parameters=query_parameters,
        )

    def _iterate(
        self,
        first_url: str,
        action: str,
        limit: Optional[int] = None,
    ) -> Iterator[Any]:
        response_class = self._get_response_class(action)
        return _iterate_pages(
            first_url,
            lambda url: self._client.get(url).json(),
            lambda raw: self._parse_response(raw, response_class),
            limit=limit,
        )

    @staticmethod
    def _page_query(request_limit: Optional[int]) -> Dict[str, Any]:
        if request_limit is None:
            return {}
        return {"limit": request_limit}


class ProjectsAPI(ProjectAPIBase):
    """Projects and their settings."""

    response_classes = {
        "list": ProjectListResponse,
        "retrieve": Project,
        "create": Project,
        "update": Project,
    }

    def list(
        self,
        limit: Optional[int] = None,
        request_limit: Optional[int] = None,
    ) -> Iterator[Project]:
        """Iterate over the projects available to the token's user.

        Args:
            - limit: total number of projects to yield. ``None`` yields all.
            - request_limit: number of projects per request (page), 1 to 100.
        """
        _check_page_limits(limit, request_limit)
        url = self._build_url(query_parameters=self._page_query(request_limit))
        return self._iterate(url, "list", limit=limit)

    def count(self) -> int:
        url = self._build_url(query_parameters={"limit": 1})
        response_class = self._get_response_class("list")
        json_response = self._client.get(url).json()
        response = self._parse_response(json_response, response_class)
        return cast(ProjectListResponse, response).total

    def retrieve(self, project: ProjectOrPubKey) -> Project:
        url = self._project_url(project)
        response_class = self._get_response_class("retrieve")
        json_response = self._client.get(url).json()
        response = self._parse_response(json_response, response_class)
        return cast(Project, response)

    def create(self, data: ProjectPayload) -> Project:
        payload = _project_payload(data)
        if not payload.get("name"):
            raise InvalidParamError("`name` is required to create a project")

        url = self._build_url()
        response_class = self._get_response_class("create")
        json_response = self._client.post(url, json=payload).json()
        response = self._parse_response(json_response, response_class)
        return cast(Project, response)

    def update(
        self, project: ProjectOrPubKey, data: ProjectPayload
    ) -> Project:
        """Change only the fields present in ``data``.

        The Project API updates projects with ``POST``.
        """
        payload = _project_payload(data)
        url = self._project_url(project)
        response_class = self._get_response_class("update")
        json_response = self._client.post(url, json=payload).json()
        response = self._parse_response(json_response, response_class)
        return cast(Project, response)

    def delete(self, project: ProjectOrPubKey) -> None:
        """Delete a project. Only the project owner can do this."""
        self._client.delete(self._project_url(project))


class ProjectUsageAPI(ProjectAPIBase):
    """Daily usage statistics of a project.

    Dates are ``date`` objects, ``YYYY-MM-DD`` strings or timezone-aware
    datetimes, which are converted to their UTC date. The server only serves
    complete days of the last 90 days in UTC: ``date_to`` must be earlier
    than today, and ``date_from`` no more than 90 days back, today included.
    """

    response_classes = {
        "combined": CombinedUsage,
        "metric": UsageMetric,
    }

    @staticmethod
    def _date_range(date_from: DateLike, date_to: DateLike) -> Dict[str, str]:
        from_ = _to_date("date_from", date_from)
        to = _to_date("date_to", date_to)
        if from_ > to:
            raise InvalidParamError(
                f"`date_from` must not be after `date_to`: {from_} > {to}"
            )
        return {"from": from_.isoformat(), "to": to.isoformat()}

    def combined(
        self,
        project: ProjectOrPubKey,
        date_from: DateLike,
        date_to: DateLike,
    ) -> CombinedUsage:
        """All metrics (traffic, storage, operations) day by day."""
        url = self._project_url(
            project,
            suffix="usage",
            query_parameters=self._date_range(date_from, date_to),
        )
        response_class = self._get_response_class("combined")
        json_response = self._client.get(url).json()
        response = self._parse_response(json_response, response_class)
        return cast(CombinedUsage, response)

    def metric(
        self,
        project: ProjectOrPubKey,
        metric: Union[UsageMetricName, str],
        date_from: DateLike,
        date_to: DateLike,
    ) -> UsageMetric:
        """One metric day by day.

        ``operations`` is only available when the owner's plan includes it,
        otherwise the server responds with 404.
        """
        try:
            metric_name = UsageMetricName(metric).value
        except ValueError:
            known = ", ".join(m.value for m in UsageMetricName)
            raise InvalidParamError(
                f"Unknown usage metric {metric!r}, expected one of: {known}"
            )

        url = self._project_url(
            project,
            suffix=f"usage/{metric_name}",
            query_parameters=self._date_range(date_from, date_to),
        )
        response_class = self._get_response_class("metric")
        json_response = self._client.get(url).json()
        response = self._parse_response(json_response, response_class)
        return cast(UsageMetric, response)


class ProjectModerationAPI(ProjectAPIBase):
    """Content moderation thresholds of a project.

    Requires the unsafe content detection feature on the owner's plan.
    """

    response_classes = {
        "get": ModerationThresholdsResponse,
        "set": ModerationThresholdsResponse,
    }

    _SUFFIX = "moderation/thresholds"

    @staticmethod
    def _thresholds_payload(
        thresholds: Iterable[Union[ModerationThreshold, Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        if isinstance(thresholds, (dict, str, bytes)):
            raise InvalidParamError(
                "`thresholds` must be a collection of thresholds"
            )

        payload: List[Dict[str, Any]] = []
        seen = set()
        for item in thresholds:
            threshold = _validate_threshold(item)
            key = (threshold.category_id, threshold.file_type)
            if key in seen:
                raise InvalidParamError(
                    f"Duplicate (category_id, file_type) combination: {key}"
                )
            seen.add(key)
            payload.append(threshold.to_payload())
        return payload

    def get(self, project: ProjectOrPubKey) -> List[ModerationThreshold]:
        url = self._project_url(project, suffix=self._SUFFIX)
        response_class = self._get_response_class("get")
        json_response = self._client.get(url).json()
        response = self._parse_response(json_response, response_class)
        return cast(ModerationThresholdsResponse, response).thresholds

    def set(
        self,
        project: ProjectOrPubKey,
        thresholds: Iterable[Union[ModerationThreshold, Dict[str, Any]]],
    ) -> List[ModerationThreshold]:
        """Replace all moderation thresholds of a project.

        Thresholds not included are deleted, so an empty collection clears
        them all.
        """
        payload = self._thresholds_payload(thresholds)
        url = self._project_url(project, suffix=self._SUFFIX)
        response_class = self._get_response_class("set")
        json_response = self._client.put(url, json=payload).json()
        response = self._parse_response(json_response, response_class)
        return cast(ModerationThresholdsResponse, response).thresholds
