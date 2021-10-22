import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.commands.store_files import store_files


def test_store_parse_wait_arg():
    args = arg_namespace("store --wait f4d55a4d-dda5-4fca-ace8-c87799d77a3c")
    assert args.wait


def test_store_wait_is_true_by_default():
    args = arg_namespace("store f4d55a4d-dda5-4fca-ace8-c87799d77a3c")
    assert args.wait


def test_store_parse_no_wait_arg():
    args = arg_namespace("store --nowait f4d55a4d-dda5-4fca-ace8-c87799d77a3c")
    assert not args.wait


@pytest.mark.vcr
def test_store_one_file(uploadcare):
    store_files(
        arg_namespace("store --nowait f4d55a4d-dda5-4fca-ace8-c87799d77a3c"),
        uploadcare,
    )

    file = uploadcare.file("f4d55a4d-dda5-4fca-ace8-c87799d77a3c")
    assert file.is_stored


@pytest.mark.vcr
def test_store_several_files(uploadcare):
    store_files(
        arg_namespace(
            "store --nowait f4d55a4d-dda5-4fca-ace8-c87799d77a3c "
            "ff75ad5f-be9a-4f28-8db8-fcd14aa3ee15"
        ),
        uploadcare,
    )

    for file_uuid in [
        "f4d55a4d-dda5-4fca-ace8-c87799d77a3c",
        "ff75ad5f-be9a-4f28-8db8-fcd14aa3ee15",
    ]:
        file = uploadcare.file(file_uuid)
        assert file.is_stored
