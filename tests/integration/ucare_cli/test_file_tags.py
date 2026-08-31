"""The tags and search CLI commands against the live REST API."""

import json

import pytest
from tests.functional.ucare_cli.helpers import arg_namespace
from tests.integration.utils import IMAGE_PATH, upload_image_file

from pyuploadcare.ucare_cli.main import main


@pytest.fixture
def keys(uploadcare):
    """Credentials as argv tokens. They take precedence over config files."""
    return [
        "--pub_key",
        uploadcare.public_key,
        "--secret",
        uploadcare.secret_key,
    ]


@pytest.fixture
def tagged_file(uploadcare):
    file_ = upload_image_file(uploadcare, tags=["cat", "animal"])
    yield file_
    file_.delete()


def _output(capsys):
    return json.loads(capsys.readouterr().out)


def test_get_file_tags(capsys, keys, tagged_file):
    main(arg_namespace([*keys, "get_file_tags", tagged_file.uuid]))

    assert _output(capsys) == ["cat", "animal"]


def test_get_file_tags_by_cdn_url(capsys, keys, tagged_file):
    main(arg_namespace([*keys, "get_file_tags", tagged_file.cdn_url]))

    assert _output(capsys) == ["cat", "animal"]


def test_set_file_tags(capsys, keys, tagged_file):
    main(
        arg_namespace(
            [*keys, "set_file_tags", tagged_file.uuid, "cat", "cute"]
        )
    )

    response = _output(capsys)
    assert response["tags"] == ["cat", "cute"]
    assert response["added"] == ["cute"]
    assert response["deleted"] == ["animal"]


def test_set_file_tags_without_tags_clears_them(capsys, keys, tagged_file):
    main(arg_namespace([*keys, "set_file_tags", tagged_file.uuid]))

    assert _output(capsys)["tags"] == []


def test_update_file_tags(capsys, keys, tagged_file):
    main(
        arg_namespace(
            [
                *keys,
                "update_file_tags",
                tagged_file.uuid,
                "--add",
                "cute",
                "--delete",
                "animal",
            ]
        )
    )

    response = _output(capsys)
    assert response["added"] == ["cute"]
    assert response["deleted"] == ["animal"]


def test_update_file_tags_without_flags_reports_an_error(
    capsys, keys, tagged_file
):
    main(arg_namespace([*keys, "update_file_tags", tagged_file.uuid]))

    assert "ERROR:" in capsys.readouterr().out


def test_upload_with_tags(capsys, keys, uploadcare):
    main(
        arg_namespace(
            [*keys, "upload", str(IMAGE_PATH), "--tags", "cli-test", "--info"]
        )
    )

    file_ = uploadcare.file(_output(capsys)["uuid"])

    try:
        assert uploadcare.tags_api.get(file_.uuid) == ["cli-test"]
    finally:
        file_.delete()


def test_search_files(capsys, keys):
    main(
        arg_namespace(
            [*keys, "search_files", "--is_image", "true", "--limit", "1"]
        )
    )

    results = _output(capsys)
    assert isinstance(results, list)
    assert len(results) <= 1
    assert all("uuid" in result for result in results)
