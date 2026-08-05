import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.exceptions import InvalidParamError
from pyuploadcare.ucare_cli.commands.get_file_tags import get_file_tags
from pyuploadcare.ucare_cli.commands.set_file_tags import set_file_tags
from pyuploadcare.ucare_cli.commands.update_file_tags import update_file_tags
from pyuploadcare.ucare_cli.main import main


FILE_UUID = "a55d6b25-d03c-4038-9838-6e06bb7df598"


@pytest.mark.vcr
def test_cli_get_file_tags(capsys, uploadcare):
    get_file_tags(arg_namespace(f"get_file_tags {FILE_UUID}"), uploadcare)
    captured = capsys.readouterr()
    assert '"cat"' in captured.out
    assert '"animal"' in captured.out


def test_cli_get_file_tags_by_cdn_url(capsys, uploadcare, vcr):
    with vcr.use_cassette("test_cli_get_file_tags"):
        get_file_tags(
            arg_namespace(f"get_file_tags https://ucarecdn.com/{FILE_UUID}/"),
            uploadcare,
        )

    captured = capsys.readouterr()
    assert '"cat"' in captured.out


@pytest.mark.vcr
def test_cli_set_file_tags(capsys, uploadcare):
    set_file_tags(
        arg_namespace(f"set_file_tags {FILE_UUID} cat animal"), uploadcare
    )
    captured = capsys.readouterr()
    assert '"added"' in captured.out
    assert '"deleted"' in captured.out


@pytest.mark.vcr
def test_cli_update_file_tags(capsys, uploadcare):
    update_file_tags(
        arg_namespace(f"update_file_tags {FILE_UUID} --add cute --delete dog"),
        uploadcare,
    )
    captured = capsys.readouterr()
    assert '"cute"' in captured.out


def test_cli_update_file_tags_without_flags_raises(uploadcare):
    with pytest.raises(InvalidParamError):
        update_file_tags(
            arg_namespace(f"update_file_tags {FILE_UUID}"), uploadcare
        )


def test_cli_update_file_tags_without_flags_prints_error(capsys):
    """`main()` turns the error into a message instead of a traceback."""
    main(
        arg_namespace(
            "--pub_key demopublickey --secret demosecretkey "
            f"update_file_tags {FILE_UUID}"
        ),
        config_file_names=(),
    )
    captured = capsys.readouterr()
    assert "ERROR:" in captured.out


def test_cli_set_file_tags_accepts_no_tags():
    """Zero tags is a deliberate "clear the tags" request."""
    parsed = arg_namespace(f"set_file_tags {FILE_UUID}")
    assert parsed.tags == []


def test_cli_upload_parses_tags():
    parsed = arg_namespace("upload sample.txt --tags cat animal")
    assert parsed.tags == ["cat", "animal"]


def test_cli_upload_without_tags():
    parsed = arg_namespace("upload sample.txt")
    assert parsed.tags is None
