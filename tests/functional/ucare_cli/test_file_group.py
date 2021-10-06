import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.commands.create_group import create_group
from pyuploadcare.ucare_cli.commands.list_groups import list_groups


@pytest.mark.vcr
def test_group_create_by_uuid_and_cdn_url(capsys, uploadcare):
    create_group(
        arg_namespace(
            "create_group a42464a4-b57a-458e-8b9d-3e6d72db9d60"
            " https://api.uploadcare.com/files/7ac0a1c3-5476-4d6a-b03d-0acf7ae6d4ae/"
        ),
        uploadcare,
    )
    captured = capsys.readouterr()
    assert '"files_count": 2' in captured.out
    assert "a42464a4-b57a-458e-8b9d-3e6d72db9d60" in captured.out
    assert "7ac0a1c3-5476-4d6a-b03d-0acf7ae6d4ae" in captured.out


@pytest.mark.vcr
def test_groups_list_without_params(capsys, uploadcare):
    list_groups(arg_namespace("list_groups"), uploadcare)
    captured = capsys.readouterr()
    assert (
        """{
    "id": "8b1362ed-b477-4a15-819a-2c6bb497d8bd~3",
    "datetime_created": "2013-04-16T14:13:42.600051+00:00",
    "datetime_stored": "2015-02-03T11:23:47.824683+00:00",
    "files_count": 3,
    "cdn_url": "https://ucarecdn.com/8b1362ed-b477-4a15-819a-2c6bb497d8bd~3/",
    "url": "https://api.uploadcare.com/groups/8b1362ed-b477-4a15-819a-2c6bb497d8bd~3/"
  },"""
        in captured.out
    )
    assert captured.out.count("{") == 100


@pytest.mark.vcr
def test_groups_list_with_params(capsys, uploadcare):
    list_groups(
        arg_namespace(
            "list_groups "
            "--starting_point=2015-10-21 "
            "--ordering=-datetime_created "
            "--limit 10 "
            "--request_limit 5"
        ),
        uploadcare,
    )
    captured = capsys.readouterr()
    assert (
        """{
    "id": "5873ad80-9959-44e8-8eb5-783bad67e3a0~1",
    "datetime_created": "2015-10-20T14:41:41.891200+00:00",
    "datetime_stored": null,
    "files_count": 1,
    "cdn_url": "https://ucarecdn.com/5873ad80-9959-44e8-8eb5-783bad67e3a0~1/",
    "url": "https://api.uploadcare.com/groups/5873ad80-9959-44e8-8eb5-783bad67e3a0~1/"
  },"""
        in captured.out
    )
    assert captured.out.count("{") == 10


@pytest.mark.vcr
def test_groups_list_empty_result(capsys, uploadcare):
    list_groups(arg_namespace("list_groups --limit 0"), uploadcare)
    captured = capsys.readouterr()
    assert "{" not in captured.out
