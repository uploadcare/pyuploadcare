"""Tests for ``ProjectAPIClient``.

Requests go through the real HTTP client stack with a mocked transport, so
the tests check URLs, methods, headers, bodies and error handling as sent.
"""

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlsplit

import httpx2
import pytest

from pyuploadcare import (
    AdaptiveBitrateStreamingFeature,
    AdaptiveBitrateStreamingProfile,
    AdaptiveBitrateStreamingProfiles,
    AdaptiveBitrateStreamingResolution,
    ModerationThreshold,
    Project,
    ProjectAPIClient,
    ProjectFeature,
    ProjectFeatures,
    UploadsFeature,
    UsageMetricName,
)
from pyuploadcare.exceptions import (
    APIError,
    AuthenticationError,
    InvalidParamError,
    InvalidRequestError,
    ThrottledRequestError,
)


API_BASE = "https://api.uploadcare.com/"
TOKEN = "test-project-api-token"
PUB_KEY = "a1dddc498fb8a82c6276"

PROJECT_JSON: Dict[str, Any] = {
    "pub_key": PUB_KEY,
    "name": "Production",
    "is_blocked": False,
    "is_search_index_allowed": False,
    "is_shared_project": False,
    "features": {
        "gif_to_video_conversion": {"is_enabled": True},
        "mime_type_filtering": {
            "mime_types": ["image/jpeg"],
            "is_enabled": False,
        },
        "team_members": {"team_size": 2},
        "uploads": {
            "filesize_limit": None,
            "autostore": True,
            "image_resolution_limit": 75000000,
            "is_signed_upload_enabled": False,
        },
        "video_processing": {"is_enabled": True},
        "malware_protection": {"is_enabled": True},
        "svg_validation": {"is_enabled": False},
        "unsafe_content_detection": {
            "is_enabled": True,
            "auto_moderation": "disabled",
        },
        "adaptive_bitrate_streaming": {
            "is_enabled": False,
            "profiles": {"h264": {"resolutions": ["360p", "720p", "1080p"]}},
        },
        "document_conversion": {"is_enabled": True},
        "exif_metadata_removal": {"is_enabled": False},
        "ai_operations": {"is_enabled": False},
        # A feature unknown to this SDK version must not break parsing.
        "brand_new_feature": {"is_enabled": True},
    },
}


class FakeServer:
    """Answers requests from a queue and records them."""

    def __init__(self) -> None:
        self.requests: List[httpx2.Request] = []
        self._responses: List[Tuple[int, Any, Dict[str, str]]] = []

    def respond(
        self,
        status: int = 200,
        payload: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self._responses.append((status, payload, headers or {}))

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        status, payload, headers = self._responses.pop(0)
        if payload is None:
            return httpx2.Response(status, headers=headers)
        return httpx2.Response(status, json=payload, headers=headers)

    @property
    def last(self) -> httpx2.Request:
        return self.requests[-1]

    def last_json(self) -> Any:
        return json.loads(self.last.content)


def query(request: httpx2.Request) -> Dict[str, List[str]]:
    return parse_qs(urlsplit(str(request.url)).query)


def url_without_query(request: httpx2.Request) -> str:
    split = urlsplit(str(request.url))
    return f"{split.scheme}://{split.netloc}{split.path}"


@pytest.fixture
def server() -> FakeServer:
    return FakeServer()


def make_client(server: FakeServer, **kwargs) -> ProjectAPIClient:
    kwargs.setdefault("api_base", API_BASE)
    client = ProjectAPIClient(token=TOKEN, **kwargs)
    client.http_client._transport = httpx2.MockTransport(server)
    return client


@pytest.fixture
def client(server: FakeServer) -> ProjectAPIClient:
    return make_client(server, retry_throttled=0)


def page(results, next_=None, total=None, per_page=20):
    return {
        "next": next_,
        "previous": None,
        "total": len(results) if total is None else total,
        "per_page": per_page,
        "results": results,
    }


# Client and auth


def test_token_is_required():
    with pytest.raises(ValueError):
        ProjectAPIClient(token=None)


def test_requests_carry_bearer_token_and_json_headers(client, server):
    server.respond(payload=PROJECT_JSON)

    client.get_project(PUB_KEY)

    headers = server.last.headers
    assert headers["Authorization"] == f"Bearer {TOKEN}"
    assert headers["Accept"] == "application/json"
    # There is no project key to report in the user agent.
    assert headers["User-Agent"].startswith("PyUploadcare/")
    assert "/None" not in headers["User-Agent"]


def test_custom_api_base_with_path(server):
    client = make_client(
        server, api_base="http://localhost:8000/apps/api/project-api/v1/"
    )
    server.respond(payload=PROJECT_JSON)

    client.get_project(PUB_KEY)

    assert str(server.last.url) == (
        "http://localhost:8000/apps/api/project-api/v1/projects/" f"{PUB_KEY}/"
    )


@pytest.mark.parametrize(
    "status,error",
    [
        (400, InvalidRequestError),
        (401, AuthenticationError),
        (403, AuthenticationError),
        (404, InvalidRequestError),
        (429, ThrottledRequestError),
        (500, APIError),
    ],
)
def test_error_statuses(client, server, status, error):
    server.respond(status, {"message": "nope", "code": "some_error"})

    with pytest.raises(error):
        client.get_project(PUB_KEY)


def test_throttled_request_is_retried(server, monkeypatch):
    monkeypatch.setattr("pyuploadcare.api.client.time.sleep", lambda _: None)
    client = make_client(server, retry_throttled=1)
    server.respond(429, {"code": "throttled_error"}, {"Retry-After": "1"})
    server.respond(payload=PROJECT_JSON)

    project = client.get_project(PUB_KEY)

    assert project.pub_key == PUB_KEY
    assert len(server.requests) == 2


# Projects


def test_get_project(client, server):
    server.respond(payload=PROJECT_JSON)

    project = client.get_project(PUB_KEY)

    assert server.last.method == "GET"
    assert str(server.last.url) == f"{API_BASE}projects/{PUB_KEY}/"
    assert isinstance(project, Project)
    assert project.name == "Production"
    features = project.features
    assert features is not None
    assert features.uploads is not None
    assert features.uploads.filesize_limit is None
    assert features.uploads.autostore is True
    assert features.team_members is not None
    assert features.team_members.team_size == 2
    abs_feature = features.adaptive_bitrate_streaming
    assert abs_feature is not None
    assert abs_feature.profiles is not None
    assert abs_feature.profiles.h264 == AdaptiveBitrateStreamingProfile(
        resolutions=["360p", "720p", "1080p"]
    )


def test_get_project_accepts_project_instance(client, server):
    server.respond(payload=PROJECT_JSON)

    client.get_project(Project(pub_key=PUB_KEY))

    assert str(server.last.url) == f"{API_BASE}projects/{PUB_KEY}/"


@pytest.mark.parametrize(
    "pub_key", ["", "../secrets", "key/other", "key?x=1", "https://evil"]
)
def test_invalid_pub_key_is_rejected(client, server, pub_key):
    with pytest.raises(InvalidParamError):
        client.get_project(pub_key)

    assert server.requests == []


def test_list_projects_follows_next(client, server):
    server.respond(
        payload=page(
            [{"pub_key": "a"}, {"pub_key": "b"}],
            next_=f"{API_BASE}projects/?from=b&limit=2",
            total=3,
        )
    )
    server.respond(payload=page([{"pub_key": "c"}], total=3))

    projects = list(client.list_projects(request_limit=2))

    assert [p.pub_key for p in projects] == ["a", "b", "c"]
    assert query(server.requests[0]) == {"limit": ["2"]}
    assert query(server.requests[1]) == {"from": ["b"], "limit": ["2"]}


def test_list_projects_limit_stops_early(client, server):
    server.respond(
        payload=page(
            [{"pub_key": "a"}, {"pub_key": "b"}],
            next_=f"{API_BASE}projects/?from=b",
        )
    )

    projects = list(client.list_projects(limit=1))

    assert [p.pub_key for p in projects] == ["a"]
    assert len(server.requests) == 1


def test_list_projects_refuses_foreign_next(client, server):
    server.respond(
        payload=page(
            [{"pub_key": "a"}], next_="https://evil.example/projects/"
        )
    )

    with pytest.raises(InvalidRequestError):
        list(client.list_projects())

    assert len(server.requests) == 1


@pytest.mark.parametrize("request_limit", [0, 101, True, "10"])
def test_list_projects_validates_request_limit(client, request_limit):
    with pytest.raises(InvalidParamError):
        client.list_projects(request_limit=request_limit)


def test_count_projects(client, server):
    server.respond(payload=page([{"pub_key": "a"}], total=42, per_page=1))

    assert client.count_projects() == 42
    assert query(server.last) == {"limit": ["1"]}


def test_create_project_sends_only_passed_fields(client, server):
    server.respond(payload=PROJECT_JSON)

    project = client.create_project(
        "Production",
        features=ProjectFeatures(uploads=UploadsFeature(autostore=False)),
    )

    assert server.last.method == "POST"
    assert str(server.last.url) == f"{API_BASE}projects/"
    assert server.last.headers["Content-Type"] == "application/json"
    assert server.last_json() == {
        "name": "Production",
        "features": {"uploads": {"autostore": False}},
    }
    assert project.pub_key == PUB_KEY


def test_create_project_requires_name(client, server):
    with pytest.raises(InvalidParamError):
        client.projects_api.create({"is_blocked": False})

    assert server.requests == []


def test_update_project_is_partial_post(client, server):
    server.respond(payload=PROJECT_JSON)

    client.update_project(
        PUB_KEY,
        is_search_index_allowed=True,
        features={
            "uploads": {"filesize_limit": None},
            "svg_validation": {"is_enabled": True},
        },
    )

    assert server.last.method == "POST"
    assert str(server.last.url) == f"{API_BASE}projects/{PUB_KEY}/"
    # An explicit `None` resets the limit to the plan's value and is sent.
    assert server.last_json() == {
        "is_search_index_allowed": True,
        "features": {
            "uploads": {"filesize_limit": None},
            "svg_validation": {"is_enabled": True},
        },
    }


def test_update_project_never_sends_read_only_fields(client, server):
    server.respond(payload=PROJECT_JSON)

    client.projects_api.update(
        PUB_KEY,
        Project(
            pub_key=PUB_KEY,
            name="Renamed",
            is_shared_project=False,
            features=ProjectFeatures(
                team_members={"team_size": 3},
                video_processing=ProjectFeature(is_enabled=False),
            ),
        ),
    )

    assert server.last_json() == {
        "name": "Renamed",
        "features": {"video_processing": {"is_enabled": False}},
    }


def test_update_project_adaptive_bitrate_streaming_profiles(client, server):
    server.respond(payload=PROJECT_JSON)
    resolution = AdaptiveBitrateStreamingResolution

    client.update_project(
        PUB_KEY,
        features=ProjectFeatures(
            adaptive_bitrate_streaming=AdaptiveBitrateStreamingFeature(
                is_enabled=True,
                profiles=AdaptiveBitrateStreamingProfiles(
                    h264=AdaptiveBitrateStreamingProfile(
                        resolutions=[resolution.R360P, resolution.R720P]
                    ),
                    h265=AdaptiveBitrateStreamingProfile(
                        resolutions=[resolution.R2160P]
                    ),
                ),
            )
        ),
    )

    assert server.last_json() == {
        "features": {
            "adaptive_bitrate_streaming": {
                "is_enabled": True,
                "profiles": {
                    "h264": {"resolutions": ["360p", "720p"]},
                    "h265": {"resolutions": ["2160p"]},
                },
            }
        }
    }


@pytest.mark.parametrize(
    "features",
    [
        {"uploads": {"autostor": False}},  # misspelled key
        {"no_such_feature": {"is_enabled": True}},
        {"uploads": {"image_resolution_limit": 10}},  # below the minimum
    ],
)
def test_update_project_rejects_invalid_features(client, server, features):
    with pytest.raises(InvalidParamError):
        client.update_project(PUB_KEY, features=features)

    assert server.requests == []


def test_update_project_requires_changes(client, server):
    with pytest.raises(InvalidParamError):
        client.update_project(PUB_KEY)

    assert server.requests == []


def test_delete_project(client, server):
    server.respond(204)

    assert client.delete_project(PUB_KEY) is None

    assert server.last.method == "DELETE"
    assert str(server.last.url) == f"{API_BASE}projects/{PUB_KEY}/"


# Usage


def test_get_usage(client, server):
    server.respond(
        payload={
            "units": {
                "traffic": "bytes",
                "storage": "bytes",
                "operations": "operations",
            },
            "data": [
                {
                    "date": "2025-03-01",
                    "traffic": 123456,
                    "storage": 2048,
                    "operations": 10,
                }
            ],
        }
    )

    usage = client.get_usage(PUB_KEY, date(2025, 3, 1), "2025-03-02")

    assert url_without_query(server.last) == (
        f"{API_BASE}projects/{PUB_KEY}/usage/"
    )
    assert query(server.last) == {"from": ["2025-03-01"], "to": ["2025-03-02"]}
    assert usage.units["traffic"] == "bytes"
    assert usage.data[0].date == date(2025, 3, 1)
    assert usage.data[0].traffic == 123456


@pytest.mark.parametrize(
    "metric", [UsageMetricName.TRAFFIC, "traffic"], ids=["enum", "str"]
)
def test_get_usage_metric(client, server, metric):
    server.respond(
        payload={
            "metric": "traffic",
            "unit": "bytes",
            "data": [{"date": "2025-03-01", "value": 123456}],
        }
    )

    usage = client.get_usage_metric(
        PUB_KEY,
        metric,
        datetime(2025, 3, 1, 12, 0, tzinfo=timezone.utc),
        date(2025, 3, 1),
    )

    assert url_without_query(server.last) == (
        f"{API_BASE}projects/{PUB_KEY}/usage/traffic/"
    )
    assert query(server.last) == {"from": ["2025-03-01"], "to": ["2025-03-01"]}
    assert usage.unit == "bytes"
    assert usage.data[0].value == 123456


@pytest.mark.parametrize(
    "metric,date_from,date_to",
    [
        ("bandwidth", "2025-03-01", "2025-03-02"),
        ("traffic", "2025-03-02", "2025-03-01"),  # from after to
        ("traffic", "03/01/2025", "2025-03-02"),
        ("traffic", None, "2025-03-02"),
        ("traffic", datetime(2025, 3, 1), "2025-03-02"),  # naive
    ],
)
def test_get_usage_metric_validates_arguments(
    client, server, metric, date_from, date_to
):
    with pytest.raises(InvalidParamError):
        client.get_usage_metric(PUB_KEY, metric, date_from, date_to)

    assert server.requests == []


def test_usage_aware_datetimes_use_utc_date(client, server):
    server.respond(payload={"units": {}, "data": []})
    moscow = timezone(timedelta(hours=3))

    client.get_usage(
        PUB_KEY,
        # 2025-03-01 22:00 UTC
        datetime(2025, 3, 2, 1, 0, tzinfo=moscow),
        datetime(2025, 3, 2, 12, 0, tzinfo=moscow),
    )

    assert query(server.last) == {"from": ["2025-03-01"], "to": ["2025-03-02"]}


# Moderation

THRESHOLDS_JSON = {
    "thresholds": [
        {
            "category_id": 4,
            "file_type": "image",
            "threshold_percentage": "37.00",
            "created_at": "2024-12-30T11:24:28.604307Z",
            "updated_at": "2024-12-30T12:14:02.028743Z",
        }
    ]
}


def test_get_moderation_thresholds(client, server):
    server.respond(payload=THRESHOLDS_JSON)

    thresholds = client.get_moderation_thresholds(PUB_KEY)

    assert server.last.method == "GET"
    assert str(server.last.url) == (
        f"{API_BASE}projects/{PUB_KEY}/moderation/thresholds/"
    )
    assert thresholds[0].category_id == 4
    assert thresholds[0].threshold_percentage == Decimal("37.00")
    assert isinstance(thresholds[0].created_at, datetime)


def test_set_moderation_thresholds(client, server):
    server.respond(payload=THRESHOLDS_JSON)

    thresholds = client.set_moderation_thresholds(
        PUB_KEY,
        [
            ModerationThreshold(category_id=4, threshold_percentage="30.5"),
            {
                "category_id": 5,
                "file_type": "image",
                "threshold_percentage": Decimal("100"),
            },
            {"category_id": 6, "threshold_percentage": 45},
        ],
    )

    assert server.last.method == "PUT"
    assert str(server.last.url) == (
        f"{API_BASE}projects/{PUB_KEY}/moderation/thresholds/"
    )
    assert server.last_json() == [
        {
            "category_id": 4,
            "file_type": "image",
            "threshold_percentage": "30.5",
        },
        {
            "category_id": 5,
            "file_type": "image",
            "threshold_percentage": "100",
        },
        {
            "category_id": 6,
            "file_type": "image",
            "threshold_percentage": "45",
        },
    ]
    assert len(thresholds) == 1


def test_set_empty_moderation_thresholds_clears_them(client, server):
    server.respond(payload={"thresholds": []})

    assert client.set_moderation_thresholds(PUB_KEY, []) == []
    assert server.last_json() == []


@pytest.mark.parametrize(
    "thresholds",
    [
        [{"category_id": 4, "threshold_percentage": "100.01"}],
        [{"category_id": 4, "threshold_percentage": "-1"}],
        [{"category_id": 4, "threshold_percentage": "1.234"}],
        [{"category_id": 4, "threshold_percentage": "1", "extra": 1}],
        [{"threshold_percentage": "1"}],
        [
            {"category_id": 4, "threshold_percentage": "1"},
            {"category_id": 4, "threshold_percentage": "2"},
        ],
        {"category_id": 4, "threshold_percentage": "1"},  # not a list
    ],
)
def test_set_moderation_thresholds_validates(client, server, thresholds):
    with pytest.raises(InvalidParamError):
        client.set_moderation_thresholds(PUB_KEY, thresholds)

    assert server.requests == []


# Meta


def test_list_moderation_categories(client, server):
    server.respond(
        payload={
            "categories": [
                {
                    "id": 7,
                    "parent_id": None,
                    "name": "Alcohol",
                    "description": "",
                    "level": 1,
                },
                {
                    "id": 8,
                    "parent_id": 7,
                    "name": "Alcoholic Beverages",
                    "description": "Bottles.",
                    "level": 2,
                },
            ]
        }
    )

    categories = client.list_moderation_categories()

    assert server.last.method == "GET"
    assert str(server.last.url) == f"{API_BASE}meta/moderation/categories/"
    assert server.last.headers["Authorization"] == f"Bearer {TOKEN}"
    assert [(c.id, c.parent_id, c.level, c.name) for c in categories] == [
        (7, None, 1, "Alcohol"),
        (8, 7, 2, "Alcoholic Beverages"),
    ]


def test_list_mime_types(client, server):
    server.respond(payload={"mime_types": ["application/cbor", "image/png"]})

    assert client.list_mime_types() == ["application/cbor", "image/png"]
    assert server.last.method == "GET"
    assert str(server.last.url) == f"{API_BASE}meta/mime/types/"


def test_meta_with_custom_api_base(server):
    client = make_client(
        server, api_base="http://localhost:8000/apps/api/project-api/v1/"
    )
    server.respond(payload={"mime_types": []})

    client.list_mime_types()

    assert str(server.last.url) == (
        "http://localhost:8000/apps/api/project-api/v1/meta/mime/types/"
    )
