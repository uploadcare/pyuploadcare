import json
from datetime import date

import pytest
from httpx2 import MockTransport, Response

from pyuploadcare import Uploadcare
from pyuploadcare.api.account_project_entities import (
    AccountProject,
    AccountProjectCreate,
    ModerationThreshold,
    ProjectFeatures,
    TeamMembers,
    UploadSettings,
)
from pyuploadcare.api.account_projects import AccountProjectsAPI
from pyuploadcare.api.api import ProjectAPI
from pyuploadcare.api.auth import BearerTokenAuth
from pyuploadcare.api.client import Client
from pyuploadcare.exceptions import (
    AuthenticationError,
    InvalidParamError,
    InvalidRequestError,
)


PUB_KEY = "demopublickey"


def _api(handler):
    client = Client(
        base_url="https://api.uploadcare.com/",
        auth=BearerTokenAuth("account-token"),
        transport=MockTransport(handler),
        retry_throttled=0,
        public_key="",
    )
    return AccountProjectsAPI(token="account-token", client=client)


def _capture(payload, status_code=200):
    seen = []

    def handler(request):
        seen.append(request)
        return Response(status_code, json=payload)

    return _api(handler), seen


def _assert_call(request, method, path):
    assert request.method == method
    assert request.url.path == path
    assert request.headers["Authorization"] == "Bearer account-token"


def _project_page():
    return {
        "next": None,
        "previous": None,
        "total": 1,
        "per_page": 100,
        "results": [{"pub_key": PUB_KEY, "name": "Production"}],
    }


def test_list_projects():
    api, seen = _capture(_project_page())

    projects = list(api.list_projects())

    assert len(projects) == 1
    assert projects[0].name == "Production"
    assert projects[0].pub_key == PUB_KEY
    _assert_call(seen[0], "GET", "/projects/")
    assert "limit" not in seen[0].url.params

    list(api.list_projects(request_limit=2))
    assert seen[1].url.params["limit"] == "2"
    _assert_call(seen[1], "GET", "/projects/")


def test_create_project():
    api, seen = _capture({"pub_key": PUB_KEY, "name": "Production"})
    created = api.create_project(
        AccountProjectCreate(
            name="Production",
            pub_key="omit-me",
            is_shared_project=True,
            features=ProjectFeatures(
                uploads=UploadSettings(autostore=False),
                team_members=TeamMembers(team_size=3),
            ),
        )
    )

    assert created.name == "Production"
    _assert_call(seen[0], "POST", "/projects/")
    body = json.loads(seen[0].content)
    assert body["name"] == "Production"
    assert body["features"]["uploads"]["autostore"] is False
    assert "is_enabled" not in body["features"]["uploads"]
    assert "team_members" not in body["features"]
    assert "pub_key" not in body
    assert "is_shared_project" not in body
    assert "is_blocked" not in body


def test_get_project():
    api, seen = _capture({"pub_key": PUB_KEY, "name": "Production"})

    project = api.get_project(PUB_KEY)

    assert project.pub_key == PUB_KEY
    _assert_call(seen[0], "GET", f"/projects/{PUB_KEY}/")


def test_update_project():
    api, seen = _capture({"pub_key": PUB_KEY, "name": "Renamed"})

    updated = api.update_project(PUB_KEY, AccountProject(name="Renamed"))

    assert updated.name == "Renamed"
    _assert_call(seen[0], "POST", f"/projects/{PUB_KEY}/")
    assert json.loads(seen[0].content) == {"name": "Renamed"}


def test_delete_project():
    api, seen = _capture(None, status_code=204)

    api.delete_project(PUB_KEY)

    _assert_call(seen[0], "DELETE", f"/projects/{PUB_KEY}/")


def test_list_secrets():
    api, seen = _capture(
        {
            "next": None,
            "previous": None,
            "total": 1,
            "per_page": 100,
            "results": [{"id": "sec-1", "hint": "ea94"}],
        }
    )

    secrets = list(api.list_secrets(PUB_KEY))

    assert secrets[0].id == "sec-1"
    assert secrets[0].hint == "ea94"
    _assert_call(seen[0], "GET", f"/projects/{PUB_KEY}/secrets/")


def test_create_secret():
    api, seen = _capture({"id": "sec-1", "secret": "ea9464b47affc143c22c"})

    secret = api.create_secret(PUB_KEY)

    assert secret.id == "sec-1"
    assert secret.secret == "ea9464b47affc143c22c"
    _assert_call(seen[0], "POST", f"/projects/{PUB_KEY}/secrets/")
    assert seen[0].content == b""


def test_delete_secret():
    api, seen = _capture(None, status_code=204)

    api.delete_secret(PUB_KEY, "sec-1")

    _assert_call(seen[0], "DELETE", f"/projects/{PUB_KEY}/secrets/sec-1/")


def test_get_moderation_thresholds():
    api, seen = _capture(
        {
            "thresholds": [
                {
                    "category_id": 4,
                    "file_type": "image",
                    "threshold_percentage": "37.00",
                }
            ]
        }
    )

    thresholds = api.get_moderation_thresholds(PUB_KEY)

    assert thresholds.thresholds[0].category_id == 4
    _assert_call(seen[0], "GET", f"/projects/{PUB_KEY}/moderation/thresholds/")


def test_set_moderation_thresholds():
    api, seen = _capture(
        {
            "thresholds": [
                {
                    "category_id": 4,
                    "file_type": "image",
                    "threshold_percentage": "30.0",
                    "created_at": "2024-12-30T11:24:28.604307Z",
                    "updated_at": "2024-12-30T12:14:02.028743Z",
                }
            ]
        }
    )

    result = api.set_moderation_thresholds(
        PUB_KEY,
        [
            ModerationThreshold(
                category_id=4,
                file_type="image",
                threshold_percentage="30.0",
                created_at=None,
            )
        ],
    )

    assert result.thresholds[0].threshold_percentage == "30.0"
    _assert_call(seen[0], "PUT", f"/projects/{PUB_KEY}/moderation/thresholds/")
    assert json.loads(seen[0].content) == [
        {
            "category_id": 4,
            "file_type": "image",
            "threshold_percentage": "30.0",
        }
    ]


def test_list_moderation_categories():
    api, seen = _capture(
        {
            "categories": [
                {
                    "id": 7,
                    "parent_id": None,
                    "name": "Alcohol",
                    "description": "",
                    "level": 1,
                }
            ]
        }
    )

    categories = api.list_moderation_categories()

    assert categories.categories[0].name == "Alcohol"
    assert categories.categories[0].parent_id is None
    _assert_call(seen[0], "GET", "/meta/moderation/categories/")


def test_list_mime_types():
    api, seen = _capture({"mime_types": ["image/jpeg"]})

    mime_types = api.list_mime_types()

    assert mime_types.mime_types == ["image/jpeg"]
    _assert_call(seen[0], "GET", "/meta/mime/types/")


def test_get_combined_usage():
    api, seen = _capture(
        {
            "units": {"traffic": "bytes", "storage": "bytes"},
            "data": [{"date": "2025-01-01", "traffic": 10, "storage": 20}],
        }
    )

    usage = api.get_combined_usage(
        PUB_KEY,
        from_date=date(2025, 1, 1),
        to_date=date(2025, 1, 31),
    )

    assert usage.units["traffic"] == "bytes"
    assert usage.data[0].traffic == 10
    _assert_call(seen[0], "GET", f"/projects/{PUB_KEY}/usage/")
    assert seen[0].url.params["from"] == "2025-01-01"
    assert seen[0].url.params["to"] == "2025-01-31"


def test_get_usage_metric():
    api, seen = _capture(
        {
            "metric": "traffic",
            "unit": "bytes",
            "data": [{"date": "2025-01-01", "value": 10}],
        }
    )

    metric = api.get_usage_metric(
        PUB_KEY,
        "traffic",
        from_date="2025-01-01",
        to_date="2025-01-31",
    )

    assert metric.metric == "traffic"
    assert metric.data[0].value == 10
    _assert_call(seen[0], "GET", f"/projects/{PUB_KEY}/usage/traffic/")
    assert seen[0].url.params["from"] == "2025-01-01"
    assert seen[0].url.params["to"] == "2025-01-31"


def test_authorize_partner():
    api, seen = _capture(
        {
            "redirect_uri": (
                "https://app.uploadcare.com/accounts/login/partners/?code=x"
            )
        }
    )

    authorization = api.authorize_partner(
        email="user@example.com",
        pub_keys=["key1", "key2"],
        redirect_to_pub_key="key1",
    )

    assert authorization.redirect_uri.startswith("https://app.uploadcare.com/")
    request = seen[0]
    _assert_call(request, "GET", "/oauth/authorize/")
    items = list(request.url.params.multi_items())
    assert ("response_type", "partner_redirect") in items
    assert ("email", "user@example.com") in items
    assert ("redirect_to_pub_key", "key1") in items
    assert [value for key, value in items if key == "pub_key"] == [
        "key1",
        "key2",
    ]


def test_invalid_usage_metric_does_not_call_transport():
    called = False

    def handler(request):
        nonlocal called
        called = True
        return Response(200, json={})

    api = _api(handler)

    with pytest.raises(InvalidParamError):
        api.get_usage_metric(
            PUB_KEY,
            "bandwidth",
            from_date="2025-01-01",
            to_date="2025-01-02",
        )

    assert called is False


def test_bad_request_raises_invalid_request_error():
    api, _seen = _capture({"detail": "bad"}, status_code=400)

    with pytest.raises(InvalidRequestError):
        api.get_project(PUB_KEY)


def test_unauthorized_raises_authentication_error():
    api, _seen = _capture({"detail": "unauthorized"}, status_code=401)

    with pytest.raises(AuthenticationError):
        api.get_project(PUB_KEY)


def test_uploadcare_without_account_token():
    uploadcare = Uploadcare(public_key="pub", secret_key="secret")

    assert isinstance(uploadcare.project_api, ProjectAPI)
    assert uploadcare.project_api.resource_type == "project"
    assert uploadcare.account_projects_api is None


def test_uploadcare_with_account_token():
    uploadcare = Uploadcare(
        public_key="pub", secret_key="secret", account_api_token="tok"
    )

    assert isinstance(uploadcare.account_projects_api, AccountProjectsAPI)


def test_unsafe_pub_key_raises():
    def handler(request):
        raise AssertionError("transport should not be called")

    api = _api(handler)

    with pytest.raises(InvalidParamError):
        api.get_project("bad/pub")
