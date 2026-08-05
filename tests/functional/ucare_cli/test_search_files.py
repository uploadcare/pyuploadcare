from datetime import datetime

import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.exceptions import InvalidParamError
from pyuploadcare.ucare_cli.commands.search_files import (
    _build_request,
    search_files,
)
from pyuploadcare.ucare_cli.main import main


@pytest.mark.vcr
def test_cli_search_files(capsys, uploadcare):
    search_files(
        arg_namespace("search_files --query sunset --tags_any cat --limit 1"),
        uploadcare,
    )
    captured = capsys.readouterr()

    assert '"total": 1' in captured.out
    assert '"sunset-cat.jpg"' in captured.out
    assert '"<em>sunset</em>-cat.jpg"' in captured.out


def test_cli_search_files_without_conditions_prints_error(capsys):
    """A `ValidationError` must not surface as a traceback."""
    main(
        arg_namespace(
            "--pub_key demopublickey --secret demosecretkey search_files"
        ),
        config_file_names=(),
    )
    captured = capsys.readouterr()

    assert "ERROR:" in captured.out


def test_cli_search_files_without_conditions_raises(uploadcare):
    with pytest.raises(InvalidParamError):
        search_files(arg_namespace("search_files"), uploadcare)


def test_cli_builds_nested_conditions():
    parsed = arg_namespace(
        "search_files"
        " --phrase_original_filename sunset"
        " --exact_detected_mime_type image/jpeg image/png"
        " --size_gt 1000 --size_lte 5000"
        " --uploaded_gte 2024-01-02"
        " --tags_any cat dog --tags_none old"
        " --is_image true"
        " --fuzziness"
    )

    assert _build_request(parsed) == {
        "fuzziness": True,
        "is_image": True,
        "phrase": {"original_filename": "sunset"},
        "exact": {"detected_mime_type": ["image/jpeg", "image/png"]},
        "size": {"gt": 1000, "lte": 5000},
        "datetime_uploaded": {"gte": datetime(2024, 1, 2)},
        "tags": {"any": ["cat", "dog"], "none": ["old"]},
    }


def test_cli_omits_unset_conditions():
    parsed = arg_namespace("search_files --query sunset")

    assert _build_request(parsed) == {"query": "sunset"}


def test_cli_sort_accepts_repeated_keys():
    parsed = arg_namespace("search_files --query sunset --sort=-score")
    parsed_two = arg_namespace(
        "search_files --query sunset --sort=-score --sort=size"
    )

    assert parsed.sort == ["-score"]
    assert parsed_two.sort == ["-score", "size"]


def test_cli_sort_rejects_unknown_key():
    with pytest.raises(SystemExit):
        arg_namespace("search_files --query sunset --sort=relevance")


@pytest.mark.parametrize("value", ["true", "false", "TRUE", " False "])
def test_cli_is_image_accepts_booleans(value):
    parsed = arg_namespace(["search_files", "--is_image", value])
    assert parsed.is_image is (value.strip().lower() == "true")


@pytest.mark.parametrize("value", ["yes", "1", "maybe", ""])
def test_cli_is_image_rejects_other_values(value):
    """Unlike `bool_or_none`, unknown input must not become `None`."""
    with pytest.raises(SystemExit):
        arg_namespace(["search_files", "--is_image", value])


def test_cli_uploaded_bound_rejects_unparsable_datetime():
    with pytest.raises(SystemExit):
        arg_namespace("search_files --uploaded_gte not-a-date")
