# coding: utf-8

import time
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Union
from uuid import UUID, uuid4

import pytest

from pyuploadcare import File, FileGroup, conf
from pyuploadcare.exceptions import InvalidParamError, InvalidRequestError

from .utils import create_file_group, upload_tmp_txt_file


# increase throttle retries for Travis CI
conf.retry_throttled = 10

IMAGE_URL = (
    "https://github.githubassets.com/images/modules/logos_page/Octocat.png"
)

ASSETS_PATH = Path(__file__).parent / "assets"
IMAGE_PATH = ASSETS_PATH / "img.png"


@pytest.fixture
def group(uploadcare) -> Iterator[FileGroup]:
    group = create_file_group(uploadcare, files_qty=1)
    yield group
    for file in group:
        file.delete()


@pytest.fixture
def group_to_delete(uploadcare) -> Iterator[FileGroup]:
    group = create_file_group(uploadcare, files_qty=1)
    files = [file for file in group]

    yield group

    for file in files:
        file.delete()


@pytest.fixture()
def input_collection(uploadcare) -> Iterator[List[Union[str, File, UUID]]]:
    u = uuid4()
    yield [str(u), uploadcare.file(u), u]


@pytest.fixture()
def expected_uuids(
    input_collection: List[Union[str, File, UUID]]
) -> Iterator[str]:
    yield [
        input_collection[0],
        input_collection[1].uuid,  # type: ignore
        str(input_collection[2]),  # type: ignore
    ]


def test_successful_upload_when_file_is_opened_in_txt_mode(
    small_file, uploadcare
):
    with open(small_file.name, "rt") as fh:
        file = uploadcare.upload(fh)

    assert isinstance(file, File)


def test_successful_upload_when_file_is_opened_in_binary_mode(
    small_file, uploadcare
):
    with open(small_file.name, "rb") as fh:
        file = uploadcare.upload(fh)

    assert isinstance(file, File)


def test_get_some_token(uploadcare):
    file_from_url = uploadcare.upload_from_url(IMAGE_URL)
    assert file_from_url.token


def test_successful_upload_from_url(uploadcare):
    file_from_url = uploadcare.upload_from_url(IMAGE_URL)

    timeout = 30
    time_started = time.time()

    while time.time() - time_started < timeout:
        status = file_from_url.update_info()["status"]
        if status in ("success", "failed", "error"):
            break
        time.sleep(1)

    assert isinstance(file_from_url.get_file(), File)


def test_successful_upload_from_url_sync_autostore(uploadcare):
    file = uploadcare.upload_from_url_sync(IMAGE_URL, interval=1)
    assert isinstance(file, File)
    assert file.filename == "Octocat.png"
    assert file.datetime_stored is not None


def test_successful_upload_by_url(uploadcare):
    file = uploadcare.upload(IMAGE_URL)
    assert isinstance(file, File)
    assert file.filename == "Octocat.png"


def test_successful_upload_from_url_signed(uploadcare):
    file_from_url = uploadcare.upload_from_url(IMAGE_URL)

    timeout = 30
    time_started = time.time()

    while time.time() - time_started < timeout:
        status = file_from_url.update_info()["status"]
        if status in ("success", "failed", "error"):
            break
        time.sleep(1)

    assert isinstance(file_from_url.get_file(), File)


def test_successful_upload_from_url_sync_autostore_signed(uploadcare):
    file = uploadcare.upload_from_url_sync(IMAGE_URL, interval=1)
    assert isinstance(file, File)
    assert file.filename == "Octocat.png"
    assert file.datetime_stored is not None


def test_successful_upload_from_url_sync_dont_store(uploadcare):
    file = uploadcare.upload_from_url_sync(IMAGE_URL, store=False, interval=1)
    assert isinstance(file, File)
    assert file.filename == "Octocat.png"
    assert file.datetime_stored is None


def test_successful_upload_from_url_sync_store(uploadcare):
    file = uploadcare.upload_from_url_sync(IMAGE_URL, store=True, interval=1)
    assert isinstance(file, File)
    assert file.datetime_stored is not None


def test_successful_upload_from_url_sync_with_filename(uploadcare):
    file = uploadcare.upload_from_url_sync(
        IMAGE_URL, filename="meh.png", interval=1
    )
    assert isinstance(file, File)
    assert file.filename == "meh.png"


@pytest.fixture(scope="module")
def uploaded_file(uploadcare):
    file = upload_tmp_txt_file(uploadcare, content="hello")
    yield file
    file.delete()


def test_info_is_non_empty_dict(uploaded_file):
    assert isinstance(uploaded_file.info, dict)
    assert uploaded_file.info


def test_original_filename_starts_with_tmp(uploaded_file):
    assert uploaded_file.filename.startswith("tmp")


def test_datetime_stored_is_none(uploaded_file):
    assert uploaded_file.datetime_stored is None


def test_datetime_removed_is_none(uploaded_file):
    assert uploaded_file.datetime_removed is None


def test_datetime_uploaded_is_datetime_instance(uploaded_file):
    assert isinstance(uploaded_file.datetime_uploaded, datetime)


def test_file_is_not_stored(uploaded_file):
    assert not uploaded_file.is_stored


def test_file_is_not_removed(uploaded_file):
    assert not uploaded_file.is_removed


def test_file_is_not_image(uploaded_file):
    assert not uploaded_file.is_image


def test_file_should_be_ready_in_5_seconds_after_upload(uploadcare):
    timeout = 5

    file = upload_tmp_txt_file(uploadcare, content="hello")

    time_started = time.time()

    try:
        while time.time() - time_started < timeout:
            if file.is_ready:
                break
            time.sleep(1)
            file.update_info()

        assert file.is_ready
    finally:
        file.delete()


def test_file_size_is_5_bytes(uploaded_file):
    # "hello" + new line
    assert uploaded_file.size == 5


def test_mime_type_is_application_octet_stream(uploaded_file):
    assert uploaded_file.mime_type == "application/octet-stream"


def test_file_successful_store(uploadcare):
    file = upload_tmp_txt_file(uploadcare, content="temp")

    assert not file.is_stored

    file.store()

    assert file.is_stored


def test_file_successful_delete(uploadcare):
    file = upload_tmp_txt_file(uploadcare, content="привет")
    assert not file.is_removed
    file.delete()
    assert file.is_removed


def test_group_successful_create(uploadcare):
    files = [
        upload_tmp_txt_file(uploadcare, content="пока"),
    ]
    group = uploadcare.create_file_group(files)
    assert isinstance(group, FileGroup)


def test_group_info_is_non_empty_dict(group):
    assert isinstance(group.info, dict)
    assert group.info


def test_group_datetime_stored_is_none(group):
    assert group.datetime_stored is None


def test_group_datetime_created_is_datetime_instance(group):
    assert isinstance(group.datetime_created, datetime)


def test_group_is_not_stored(group):
    assert not group.is_stored


def test_successful_group_store(group: FileGroup):
    assert not group.is_stored

    group.store()

    assert group.is_stored


def test_group_successfully_deleted(group_to_delete):
    file_from_group = next(iter(group_to_delete))
    assert not group_to_delete.is_deleted

    group_to_delete.delete()

    with pytest.raises(InvalidRequestError, match="Not found"):
        group_to_delete.update_info()

    assert group_to_delete.is_deleted
    file_from_group.update_info()
    assert not file_from_group.is_removed


@pytest.fixture
def image_file(uploadcare):
    # create file to copy from
    file_from_url = uploadcare.upload_from_url(IMAGE_URL)

    timeout = 30
    time_started = time.time()

    while time.time() - time_started < timeout:
        status = file_from_url.update_info()["status"]
        if status in ("success", "failed", "error"):
            break
        time.sleep(1)

    file = file_from_url.get_file()
    time_started = time.time()
    while time.time() - time_started < timeout:
        if file.is_ready:
            break
        time.sleep(1)
        file.update_info()

    yield file

    file.delete()


def test_local_copy(image_file):
    file = image_file.copy(effects="resize/50x/")
    assert isinstance(file, File)


def test_create_local_copy(image_file):
    file = image_file.create_local_copy()
    assert isinstance(file, File)

    file = image_file.create_local_copy(effects="resize/50x/")
    assert not file.is_stored

    file = image_file.create_local_copy(effects="resize/50x/", store=True)
    time.sleep(2)
    file.update_info()
    assert file.is_stored

    file = image_file.create_local_copy(store=False)
    time.sleep(2)
    file.update_info()
    assert not file.is_stored


def test_iteration_over_all_files(uploadcare):
    files = list(uploadcare.list_files(limit=10))
    assert len(files) >= 0


def test_iteration_over_limited_count_of_files(uploadcare):
    files = list(uploadcare.list_files(limit=2))
    assert len(files) == 2


def test_iteration_over_stored_files(uploadcare):
    for file_ in uploadcare.list_files(stored=True, limit=10):
        assert file_.is_stored


def test_iteration_over_not_stored_files(uploadcare):
    for file_ in uploadcare.list_files(stored=False, limit=10):
        assert not file_.is_stored


def test_iteration_over_removed_files(uploadcare):
    for file_ in uploadcare.list_files(removed=True, limit=10):
        assert file_.is_removed


def test_iteration_over_not_removed_files(uploadcare):
    for file_ in uploadcare.list_files(removed=False, limit=10):
        assert not file_.is_removed


def test_iteration_over_stored_removed_files(uploadcare):
    files = list(uploadcare.list_files(stored=True, removed=True, limit=10))
    assert not files


def test_uploaded_image_mime_type_determined(uploadcare):
    with open(IMAGE_PATH, "rb") as fh:
        file = uploadcare.upload(fh)

    mime_type = file.mime_type
    file.delete()

    assert mime_type == "image/png"


def test_uuid_extraction(uploadcare, input_collection, expected_uuids):
    extracted_uuids = uploadcare._extract_uuids(input_collection)
    assert extracted_uuids == expected_uuids
    assert all(isinstance(item, str) for item in extracted_uuids)


def test_corrupted_uuid_extraction(uploadcare):
    with pytest.raises(InvalidParamError, match="Couldn't find UUID"):
        uploadcare._extract_uuids(["456"])
