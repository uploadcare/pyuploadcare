import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare import File
from pyuploadcare.ucare_cli.main import delete_files


def test_delete_parse_wait_arg():
    args = arg_namespace("delete --wait 6c5e9526-b0fe-4739-8975-72e8d5ee6342")
    assert args.wait


def test_delete_wait_is_true_by_default():
    args = arg_namespace("delete 6c5e9526-b0fe-4739-8975-72e8d5ee6342")
    assert args.wait


def test_delete_parse_no_wait_arg():
    args = arg_namespace(
        "delete --nowait 6c5e9526-b0fe-4739-8975-72e8d5ee6342"
    )
    assert not args.wait


@pytest.mark.vcr
def test_delete_one_file():
    args = arg_namespace(
        "delete --nowait 23762be6-cfe3-4d27-86be-9ed7d403dd43"
    )

    delete_files(args)

    file = File("23762be6-cfe3-4d27-86be-9ed7d403dd43")
    assert file.is_removed


@pytest.mark.vcr
def test_delete_several_files():
    args = arg_namespace(
        "delete --nowait 630a1322-a3b4-4873-a0a0-0ba6d6668eb5 "
        "dda35f47-3add-4736-b406-f48af2548c5b"
    )

    delete_files(args)

    for file_uuid in [
        "630a1322-a3b4-4873-a0a0-0ba6d6668eb5",
        "dda35f47-3add-4736-b406-f48af2548c5b",
    ]:
        file = File(file_uuid)
        assert file.is_removed
