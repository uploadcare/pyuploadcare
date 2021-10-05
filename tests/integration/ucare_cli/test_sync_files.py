import os
import tempfile

import pytest
from tests.functional.ucare_cli.helpers import arg_namespace

from pyuploadcare.ucare_cli.main import main


@pytest.fixture
def temp_directory():
    return tempfile.TemporaryDirectory()


@pytest.fixture
def sync_path(temp_directory):
    return os.path.join(temp_directory.name, "downloads")


def test_sync_created_directory_for_upload(sync_path):
    assert not os.path.exists(sync_path)

    main(
        arg_namespace(
            f"--pub_key demopublickey --secret demosecretkey "
            f"sync --limit 1 --no-input {sync_path}"
        )
    )

    assert os.path.exists(sync_path)

    assert len(os.listdir(sync_path)) == 1


def test_sync_file_exists_and_replace_flag(sync_path):
    main(
        arg_namespace(
            f"--pub_key demopublickey --secret demosecretkey "
            f"sync --limit 1 --no-input {sync_path}"
        )
    )

    filename = os.listdir(sync_path)[0]
    filepath = os.path.join(sync_path, filename)
    created_time = os.path.getmtime(filepath)
    main(
        arg_namespace(
            f"--pub_key demopublickey --secret demosecretkey "
            f"sync --limit 1 --replace --no-input {sync_path}"
        )
    )
    assert os.path.getmtime(filepath) > created_time


def test_sync_uuids(sync_path, uploadcare):
    file_list = list(uploadcare.list_files(limit=2))
    uuids = [str(file.uuid) for file in file_list]

    main(
        arg_namespace(
            f"--pub_key demopublickey --secret demosecretkey "
            f"sync --no-input {sync_path} --uuids {' '.join(uuids)}"
        )
    )

    synced_filenames = {
        os.path.splitext(filename)[0] for filename in os.listdir(sync_path)
    }
    for uuid in uuids:
        assert uuid in synced_filenames


def test_sync_patterns(sync_path, uploadcare):
    file_list = list(uploadcare.list_files(limit=2))
    uuids = [str(file.uuid) for file in file_list]

    expected_filenames = [
        "{}_{}".format(
            str(file.uuid),
            os.path.splitext(file.filename)[1],
        )
        for file in file_list
    ]

    main(
        arg_namespace(
            "--pub_key demopublickey --secret demosecretkey "
            "sync --no-input {} --uuids {}".format(
                sync_path + "/${uuid}_${ext}", " ".join(uuids)
            )
        )
    )

    for synced_filename in os.listdir(sync_path):
        assert synced_filename in expected_filenames
