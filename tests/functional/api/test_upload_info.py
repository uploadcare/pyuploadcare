"""``UploadAPI.info`` and ``Uploadcare.get_upload_info`` (``GET /info/``)."""

from typing import Any
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import httpx2
import pytest

from pyuploadcare import Uploadcare
from pyuploadcare.api import UploadAPI
from pyuploadcare.api.client import Client
from pyuploadcare.api.entities import ColorMode, ImageInfo, UploadFileInfo
from pyuploadcare.exceptions import (
    AuthenticationError,
    InvalidParamError,
    InvalidRequestError,
    ThrottledRequestError,
)


PUB_KEY = "demopublickey"
FILE_UUID = "a42464a4-b57a-458e-8b9d-3e6d72db9d60"

# The `/info/` response as built by `File.get_upload_info()` in the platform:
# `done` and `total` equal `size`, `image_info` is `content_info.image`.
INFO_JSON: dict[str, Any] = {
    "size": 191176,
    "total": 191176,
    "done": 191176,
    "uuid": FILE_UUID,
    "file_id": FILE_UUID,
    "original_filename": "camera.jpg",
    "is_image": True,
    "is_stored": True,
    "image_info": {
        "width": 1280,
        "height": 720,
        "format": "JPEG",
        "color_mode": "RGB",
        "geo_location": None,
        "orientation": None,
        "dpi": None,
        "datetime_original": None,
        "sequence": False,
    },
    "video_info": None,
    "content_info": {
        "mime": {"mime": "image/jpeg", "type": "image", "subtype": "jpeg"},
        "image": {
            "width": 1280,
            "height": 720,
            "format": "JPEG",
            "color_mode": "RGB",
            "geo_location": None,
            "orientation": None,
            "dpi": None,
            "datetime_original": None,
            "sequence": False,
        },
    },
    "metadata": {"pet": "cat", "subsystem": "uploader"},
    "is_ready": True,
    "filename": "camera.jpg",
    "mime_type": "image/jpeg",
}


class FakeServer:
    def __init__(self, status: int = 200, payload: Any = None) -> None:
        self.status = status
        self.payload = INFO_JSON if payload is None else payload
        self.requests: list[httpx2.Request] = []

    def __call__(self, request: httpx2.Request) -> httpx2.Response:
        self.requests.append(request)
        return httpx2.Response(self.status, json=self.payload)

    @property
    def last(self) -> httpx2.Request:
        return self.requests[-1]


def make_uploadcare(server: FakeServer, **kwargs) -> Uploadcare:
    uploadcare = Uploadcare(public_key=PUB_KEY, retry_throttled=0, **kwargs)
    uploadcare.upload_client._transport = httpx2.MockTransport(server)
    return uploadcare


def query(request: httpx2.Request) -> dict[str, list[str]]:
    return parse_qs(urlsplit(str(request.url)).query)


def test_get_upload_info():
    server = FakeServer()
    uploadcare = make_uploadcare(server, secret_key="demosecretkey")

    info = uploadcare.get_upload_info(FILE_UUID)

    assert isinstance(info, UploadFileInfo)
    assert info.uuid == UUID(FILE_UUID)
    assert info.file_id == UUID(FILE_UUID)
    assert info.original_filename == "camera.jpg"
    assert info.filename == "camera.jpg"
    assert info.mime_type == "image/jpeg"
    assert info.size == 191176
    assert info.done == info.total == 191176
    assert info.is_image is True
    assert info.is_ready is True
    assert info.is_stored is True
    assert isinstance(info.image_info, ImageInfo)
    assert (info.image_info.width, info.image_info.height) == (1280, 720)
    assert info.video_info is None
    assert info.content_info is not None
    assert info.content_info.mime is not None
    assert info.content_info.mime.mime == "image/jpeg"
    assert info.content_info.image is not None
    assert info.content_info.image.width == 1280
    assert info.content_info.video is None
    assert info.metadata == {"pet": "cat", "subsystem": "uploader"}
    assert info.s3_bucket is None

    request = server.last
    assert request.method == "GET"
    assert urlsplit(str(request.url)).path == "/info/"
    assert query(request) == {"pub_key": [PUB_KEY], "file_id": [FILE_UUID]}
    assert "Authorization" not in request.headers


def test_get_upload_info_file_not_ready():
    # A file not yet analyzed: no content info, `is_image` unknown.
    payload = {
        **INFO_JSON,
        "is_ready": False,
        "is_stored": False,
        "is_image": None,
        "image_info": None,
        "video_info": None,
        "content_info": None,
        "metadata": {},
    }
    uploadcare = make_uploadcare(FakeServer(payload=payload))

    info = uploadcare.get_upload_info(FILE_UUID)

    assert info.is_ready is False
    assert info.is_image is None
    assert info.image_info is None
    assert info.content_info is None
    assert info.metadata == {}


def test_get_upload_info_parses_video_and_s3_bucket():
    video_info = {
        "duration": 3000,
        "format": "mp4",
        "bitrate": 1500,
        "audio": {"codec": "aac", "sample_rate": 44100, "channels": "2"},
        "video": {"width": 640, "height": 360, "frame_rate": 30.0},
    }
    payload = {
        **INFO_JSON,
        "is_image": False,
        "mime_type": "video/mp4",
        "image_info": None,
        "video_info": video_info,
        "content_info": {
            "mime": {"mime": "video/mp4", "type": "video", "subtype": "mp4"},
            "video": {
                "duration": 3000,
                "format": "mp4",
                "bitrate": 1500,
                "audio": [{"codec": "aac", "channels": 2}],
                "video": [{"width": 640, "height": 360, "frame_rate": 30.0}],
            },
        },
        "s3_bucket": "my-bucket",
    }
    uploadcare = make_uploadcare(FakeServer(payload=payload))

    info = uploadcare.get_upload_info(FILE_UUID)

    assert info.video_info == video_info
    assert info.content_info is not None
    assert info.content_info.video is not None
    assert info.content_info.video.format == "mp4"
    assert info.content_info.video.video[0].width == 640
    assert info.s3_bucket == "my-bucket"


def test_get_upload_info_ignores_unknown_fields():
    payload = {**INFO_JSON, "new_field": 1}
    uploadcare = make_uploadcare(FakeServer(payload=payload))

    info = uploadcare.get_upload_info(FILE_UUID)

    assert info.uuid == UUID(FILE_UUID)
    assert not hasattr(info, "new_field")


def test_get_upload_info_accepts_file_and_uuid():
    server = FakeServer()
    uploadcare = make_uploadcare(server)

    uploadcare.get_upload_info(uploadcare.file(FILE_UUID))
    uploadcare.get_upload_info(UUID(FILE_UUID))
    uploadcare.get_upload_info(FILE_UUID.upper())

    assert [query(r)["file_id"] for r in server.requests] == [[FILE_UUID]] * 3


@pytest.mark.parametrize(
    "status,error",
    [
        (400, InvalidRequestError),
        (404, InvalidRequestError),
        (401, AuthenticationError),
        (403, AuthenticationError),
        (429, ThrottledRequestError),
    ],
)
def test_get_upload_info_errors(status, error):
    server = FakeServer(status=status, payload={"detail": "File not found"})
    uploadcare = make_uploadcare(server)

    with pytest.raises(error):
        uploadcare.get_upload_info(FILE_UUID)


@pytest.mark.parametrize(
    "file_id",
    [
        "not-a-uuid",
        f"{FILE_UUID}/../project",
        f"{FILE_UUID}~2",
        "",
    ],
)
def test_get_upload_info_rejects_invalid_file_id(file_id):
    server = FakeServer()
    uploadcare = make_uploadcare(server)

    with pytest.raises(InvalidParamError):
        uploadcare.upload_api.info(file_id)

    assert server.requests == []


@pytest.mark.parametrize("public_key", ["", None])
def test_upload_api_info_requires_public_key(public_key):
    server = FakeServer()
    client = Client(
        base_url="https://upload.uploadcare.com/",
        transport=httpx2.MockTransport(server),
    )
    upload_api = UploadAPI(client=client, public_key=public_key)

    with pytest.raises(ValueError, match="public_key"):
        upload_api.info(FILE_UUID)

    assert server.requests == []


@pytest.mark.parametrize(
    "image",
    [
        {"color_mode": "I;16", "dpi": None},
        {"color_mode": "1", "dpi": [72, 72]},
        {"color_mode": "RGB", "dpi": [299.9994, 299.9994]},
    ],
)
def test_get_upload_info_parses_any_color_mode_and_dpi(image):
    image_info = {**INFO_JSON["image_info"], **image}
    payload = {
        **INFO_JSON,
        "image_info": image_info,
        "content_info": {**INFO_JSON["content_info"], "image": image_info},
    }
    uploadcare = make_uploadcare(FakeServer(payload=payload))

    info = uploadcare.get_upload_info(FILE_UUID)

    assert info.image_info is not None
    assert info.image_info.color_mode == image["color_mode"]
    expected_dpi = None if image["dpi"] is None else tuple(image["dpi"])
    assert info.image_info.dpi == expected_dpi
    assert info.content_info is not None
    assert info.content_info.image == info.image_info


def test_known_color_mode_stays_enum():
    uploadcare = make_uploadcare(FakeServer())

    info = uploadcare.get_upload_info(FILE_UUID)

    assert info.image_info is not None
    assert info.image_info.color_mode is ColorMode.RGB
    assert info.image_info.dpi is None
