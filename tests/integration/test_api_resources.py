# coding: utf-8
from __future__ import unicode_literals

import time
from datetime import datetime

import pytest

from pyuploadcare import File, FileGroup, FileList, conf

from .utils import create_file_group, upload_tmp_txt_file


# increase throttle retries for Travis CI
conf.retry_throttled = 10

IMAGE_URL = (
    "https://github.githubassets.com/images/modules/logos_page/Octocat.png"
)


@pytest.fixture
def group():
    group = create_file_group(files_qty=1)
    yield group
    for file in group:
        file.delete()


def test_successful_upload_when_file_is_opened_in_txt_mode(small_file):
    with open(small_file.name, "rt") as fh:
        file = File.upload(fh)

    assert isinstance(file, File)


def test_successful_upload_when_file_is_opened_in_binary_mode(small_file):
    with open(small_file.name, "rb") as fh:
        file = File.upload(fh)

    assert isinstance(file, File)


def test_get_some_token():
    file_from_url = File.upload_from_url(IMAGE_URL)
    assert file_from_url.token


def test_successful_upload_from_url():
    file_from_url = File.upload_from_url(IMAGE_URL)

    timeout = 30
    time_started = time.time()

    while time.time() - time_started < timeout:
        status = file_from_url.update_info()["status"]
        if status in ("success", "failed", "error"):
            break
        time.sleep(1)

    assert isinstance(file_from_url.get_file(), File)


def test_successful_upload_from_url_sync_autostore():
    file = File.upload_from_url_sync(IMAGE_URL, interval=1)
    assert isinstance(file, File)
    assert file.filename == "Octocat.png"
    assert file.datetime_stored is not None


def test_successful_upload_by_url():
    file = File.upload(IMAGE_URL)
    assert isinstance(file, File)
    assert file.filename == "Octocat.png"


def test_successful_upload_from_url_signed(signed_uploads):
    file_from_url = File.upload_from_url(IMAGE_URL)

    timeout = 30
    time_started = time.time()

    while time.time() - time_started < timeout:
        status = file_from_url.update_info()["status"]
        if status in ("success", "failed", "error"):
            break
        time.sleep(1)

    assert isinstance(file_from_url.get_file(), File)


def test_successful_upload_from_url_sync_autostore_signed(signed_uploads):
    file = File.upload_from_url_sync(IMAGE_URL, interval=1)
    assert isinstance(file, File)
    assert file.filename == "Octocat.png"
    assert file.datetime_stored is not None


def test_successful_upload_from_url_sync_dont_store():
    file = File.upload_from_url_sync(IMAGE_URL, store=False, interval=1)
    assert isinstance(file, File)
    assert file.filename == "Octocat.png"
    assert file.datetime_stored is None


def test_successful_upload_from_url_sync_store():
    file = File.upload_from_url_sync(IMAGE_URL, store=True, interval=1)
    assert isinstance(file, File)
    assert file.datetime_stored is not None


def test_successful_upload_from_url_sync_with_filename():
    file = File.upload_from_url_sync(IMAGE_URL, filename="meh.png", interval=1)
    assert isinstance(file, File)
    assert file.filename == "meh.png"


@pytest.fixture(scope="module")
def uploaded_file():
    file = upload_tmp_txt_file(content="hello")
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


def test_file_should_be_ready_in_5_seconds_after_upload():
    timeout = 5

    file = upload_tmp_txt_file(content="hello")

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


def test_file_successful_store():
    file = upload_tmp_txt_file(content="temp")

    assert not file.is_stored

    file.store()

    assert file.is_stored


def test_file_successful_delete():
    file = upload_tmp_txt_file(content="привет")
    assert not file.is_removed
    file.delete()
    assert file.is_removed


def test_group_successful_create():
    files = [
        upload_tmp_txt_file(content="пока"),
    ]
    group = FileGroup.create(files)
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


def test_successful_group_store(group):
    assert not group.is_stored

    group.store()

    assert group.is_stored


@pytest.fixture
def image_file():
    # create file to copy from
    file_from_url = File.upload_from_url(IMAGE_URL)

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


def test_iteration_over_all_files():
    files = list(FileList(limit=10))
    assert len(files) >= 0


def test_iteration_over_limited_count_of_files():
    files = list(FileList(limit=2))
    assert len(files) == 2


def test_iteration_over_stored_files():
    for file_ in FileList(stored=True, limit=10):
        assert file_.is_stored


def test_iteration_over_not_stored_files():
    for file_ in FileList(stored=False, limit=10):
        assert not file_.is_stored


def test_iteration_over_removed_files():
    for file_ in FileList(removed=True, limit=10):
        assert file_.is_removed


def test_iteration_over_not_removed_files():
    for file_ in FileList(removed=False, limit=10):
        assert not file_.is_removed


def test_iteration_over_stored_removed_files():
    files = list(FileList(stored=True, removed=True, limit=10))
    assert not files
