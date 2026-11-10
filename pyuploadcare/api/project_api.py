"""Project API endpoints.

The Project API works with every project the user owns or is a team member
of, where the REST API works with one project. Requests are authorized with
the user's OAuth access token (``pyuploadcare.api.auth.UploadcareOAuth``).
"""

import re
from typing import Any, Dict, Iterator, Optional, Pattern, Union, cast

from pydantic import ValidationError

from pyuploadcare.api.base import API, _iterate_pages
from pyuploadcare.api.client import Client
from pyuploadcare.api.project_entities import Project, ProjectListResponse
from pyuploadcare.api.utils import require_optional_int, require_range
from pyuploadcare.exceptions import InvalidParamError


# Maximum page size of the list endpoints.
PROJECT_API_MAX_PAGE_SIZE = 100

# Characters the server accepts in a project public key.
RE_PUB_KEY: Pattern[str] = re.compile(r"[a-zA-Z0-9_]+\Z")


ProjectOrPubKey = Union[Project, str]
ProjectPayload = Union[Project, Dict[str, Any]]


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
