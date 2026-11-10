import socket
import ssl
from collections.abc import Iterable, Iterator
from typing import Any

from pyuploadcare import conf
from pyuploadcare.api.auth import UploadcareOAuth
from pyuploadcare.api.client import Client
from pyuploadcare.api.project_api import (
    DateLike,
    ProjectMetaAPI,
    ProjectModerationAPI,
    ProjectOrPubKey,
    ProjectsAPI,
    ProjectUsageAPI,
    validate_project_data,
)
from pyuploadcare.api.project_entities import (
    CombinedUsage,
    ModerationCategory,
    ModerationThreshold,
    Project,
    ProjectFeatures,
    UsageMetric,
    UsageMetricName,
)
from pyuploadcare.exceptions import InvalidParamError


DEFAULT_SSL_CONTEXT = ssl.create_default_context()


class ProjectAPIClient:
    """Project API client: manage the projects of an account.

    ``Uploadcare`` works with one project and its key pair. This client is
    authorized with an OAuth access token issued for a user and works with
    every project the user owns or is a team member of::

        >>> projects = ProjectAPIClient(token='<access-token>')
        >>> project = projects.create_project('Production')
        >>> projects.update_project(project, is_search_index_allowed=True)

    Refreshing the token is up to the caller; pass the new one with
    ``set_access_token()``::

        >>> projects.set_access_token('<new-access-token>')

    Args:
        - token: OAuth access token.
        - api_base: Project API base url.
        - verify_api_ssl: Verify Project API SSL certificate.
        - retry_throttled: Amount of retries after throttling header received.
        - user_agent_extension: Extra suffix to user agent to identify client.
        - timeout: HTTP requests timeout. If not set, default socket timeout
          is used.

    """

    def __init__(
        self,
        token: str | None = conf.oauth_token,
        api_base=conf.project_api_base,
        verify_api_ssl=conf.verify_api_ssl,
        retry_throttled=conf.retry_throttled,
        user_agent_extension=conf.user_agent_extension,
        timeout=conf.timeout,
    ):
        if not token:
            raise ValueError("token is required")

        self.api_base = api_base
        self.verify_api_ssl = verify_api_ssl
        self.retry_throttled = retry_throttled
        self.user_agent_extension = user_agent_extension

        if timeout is conf.DEFAULT:
            timeout = socket.getdefaulttimeout()

        self.timeout = timeout

        self.auth = UploadcareOAuth(token)

        self.http_client = Client(
            base_url=api_base,
            auth=self.auth,
            headers={"Accept": "application/json"},
            verify=(
                DEFAULT_SSL_CONTEXT
                if verify_api_ssl is True
                else verify_api_ssl
            ),
            timeout=timeout,
            user_agent_extension=user_agent_extension,
            retry_throttled=retry_throttled,
        )

        self.projects_api = ProjectsAPI(client=self.http_client)
        self.usage_api = ProjectUsageAPI(client=self.http_client)
        self.moderation_api = ProjectModerationAPI(client=self.http_client)
        self.meta_api = ProjectMetaAPI(client=self.http_client)

    def set_access_token(self, token: str) -> str:
        """Replace the access token used for the following requests."""
        return self.auth.set_access_token(token)

    @staticmethod
    def _project_data(
        name: str | None = None,
        is_blocked: bool | None = None,
        is_search_index_allowed: bool | None = None,
        features: ProjectFeatures | dict[str, Any] | None = None,
    ) -> Project:
        # Arguments left as `None` are not set on the model, so they are not
        # sent.
        fields: dict[str, Any] = {
            "name": name,
            "is_blocked": is_blocked,
            "is_search_index_allowed": is_search_index_allowed,
            "features": features,
        }
        return validate_project_data(
            {key: value for key, value in fields.items() if value is not None}
        )

    def list_projects(
        self,
        limit: int | None = None,
        request_limit: int | None = None,
    ) -> Iterator[Project]:
        """Iterate over the projects available to the token's user.

        Args:
            - limit: total number of projects to yield. ``None`` yields all.
            - request_limit: number of projects per request (page), 1 to 100.
        """
        return self.projects_api.list(limit=limit, request_limit=request_limit)

    def count_projects(self) -> int:
        """Number of projects available to the token's user."""
        return self.projects_api.count()

    def get_project(self, project: ProjectOrPubKey) -> Project:
        """Get the settings of a project."""
        return self.projects_api.retrieve(project)

    def create_project(
        self,
        name: str,
        is_blocked: bool | None = None,
        is_search_index_allowed: bool | None = None,
        features: ProjectFeatures | dict[str, Any] | None = None,
    ) -> Project:
        """Create a project.

        Project names are unique within an account.
        """
        data = self._project_data(
            name=name,
            is_blocked=is_blocked,
            is_search_index_allowed=is_search_index_allowed,
            features=features,
        )
        return self.projects_api.create(data)

    def update_project(
        self,
        project: ProjectOrPubKey,
        name: str | None = None,
        is_blocked: bool | None = None,
        is_search_index_allowed: bool | None = None,
        features: ProjectFeatures | dict[str, Any] | None = None,
    ) -> Project:
        """Update project settings.

        Only the passed arguments are changed, and within ``features`` only
        the fields that were set: e.g. to turn off autostore and keep the
        rest as is::

            >>> projects.update_project(
            ...     pub_key,
            ...     features=ProjectFeatures(
            ...         uploads=UploadsFeature(autostore=False),
            ...     ),
            ... )

        Setting ``filesize_limit`` or ``image_resolution_limit`` to ``None``
        explicitly resets the limit to the plan's value.

        The server rejects changes to features the owner's plan does not
        include, so do not pass back the ``features`` returned by
        ``get_project()``.
        """
        data = self._project_data(
            name=name,
            is_blocked=is_blocked,
            is_search_index_allowed=is_search_index_allowed,
            features=features,
        )
        if not data.model_fields_set:
            raise InvalidParamError("nothing to update")
        return self.projects_api.update(project, data)

    def delete_project(self, project: ProjectOrPubKey) -> None:
        """Delete a project. Only the project owner can do this."""
        self.projects_api.delete(project)

    def get_usage(
        self,
        project: ProjectOrPubKey,
        date_from: DateLike,
        date_to: DateLike,
    ) -> CombinedUsage:
        """Daily traffic, storage and operations usage of a project.

        Only complete days of the last 90 days in UTC are available:
        ``date_to`` must be before today. Datetimes must be timezone-aware.
        """
        return self.usage_api.combined(project, date_from, date_to)

    def get_usage_metric(
        self,
        project: ProjectOrPubKey,
        metric: UsageMetricName | str,
        date_from: DateLike,
        date_to: DateLike,
    ) -> UsageMetric:
        """Daily usage of one metric: traffic, storage or operations."""
        return self.usage_api.metric(project, metric, date_from, date_to)

    def get_moderation_thresholds(
        self, project: ProjectOrPubKey
    ) -> list[ModerationThreshold]:
        """Content moderation thresholds of a project."""
        return self.moderation_api.get(project)

    def set_moderation_thresholds(
        self,
        project: ProjectOrPubKey,
        thresholds: Iterable[ModerationThreshold | dict[str, Any]],
    ) -> list[ModerationThreshold]:
        """Replace all content moderation thresholds of a project.

        Thresholds not included are deleted::

            >>> projects.set_moderation_thresholds(pub_key, [
            ...     ModerationThreshold(category_id=4,
            ...                         threshold_percentage="30.5"),
            ... ])
        """
        return self.moderation_api.set(project, thresholds)

    def list_moderation_categories(self) -> list[ModerationCategory]:
        """Available content moderation categories.

        Their ids are what ``ModerationThreshold.category_id`` takes.
        """
        return self.meta_api.moderation_categories()

    def list_mime_types(self) -> list[str]:
        """MIME types accepted by MIME type filtering."""
        return self.meta_api.mime_types()
