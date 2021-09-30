import os

import pytest

from pyuploadcare import File, FileList
from pyuploadcare.resources.file import UploadProgress


@pytest.mark.vcr
def test_file_upload(small_file):
    with open(small_file.name, "rb") as fh:
        file = File.upload(fh)

    assert isinstance(file, File)
    assert file.is_stored()


def test_file_upload_callback(small_file, vcr):
    progresses = []

    def callback(upload_progress: UploadProgress):
        progresses.append(upload_progress)

    with open(small_file.name, "rb") as fh:
        with vcr.use_cassette("test_file_upload"):
            file = File.upload(fh, callback=callback)

    assert isinstance(file, File)
    assert progresses
    assert isinstance(progresses[0], UploadProgress)


@pytest.mark.vcr
def test_file_upload_secure(small_file, signed_uploads):

    with open(small_file.name, "rb") as fh:
        file = File.upload(fh)

    assert isinstance(file, File)
    assert file.is_stored()


@pytest.mark.vcr
def test_file_upload_big_file(big_file):
    with open(big_file.name, "rb") as fh:
        file = File.upload(fh, store=True)

    assert isinstance(file, File)
    assert file.is_ready()


@pytest.mark.vcr
def test_file_upload_big_file_callback(big_file, vcr):
    progresses = []

    def callback(upload_progress: UploadProgress):
        progresses.append(upload_progress)

    with open(big_file.name, "rb") as fh:
        with vcr.use_cassette("test_file_upload_big_file"):
            file = File.upload(fh, store=True, callback=callback)

    assert isinstance(file, File)
    assert progresses
    assert isinstance(progresses[0], UploadProgress)


@pytest.mark.vcr
def test_file_upload_by_url():
    file = File.upload(
        "https://github.githubassets.com/images/modules/logos_page/Octocat.png"
    )
    assert isinstance(file, File)
    assert file.is_ready()


@pytest.mark.vcr
def test_file_upload_by_url_callback(vcr):
    progresses = []

    def callback(upload_progress: UploadProgress):
        progresses.append(upload_progress)

    with vcr.use_cassette("test_file_upload_by_url"):
        file = File.upload(
            "https://github.githubassets.com/images/modules/logos_page/Octocat.png",
            callback=callback,
        )
    assert isinstance(file, File)


@pytest.mark.vcr
def test_file_upload_multiple(small_file, small_file2):
    file1 = open(small_file.name)
    file2 = open(small_file2.name)

    files = File.upload_files([file1, file2])
    created_filenames = [file.filename() for file in files]
    assert sorted(created_filenames) == sorted(
        [
            os.path.basename(input_file.name)
            for input_file in [small_file, small_file2]
        ]
    )


@pytest.mark.vcr
def test_file_create_local_copy():
    file = File("35ea470d-216c-4752-91d2-5176b34c1225")
    copied_file = file.create_local_copy(
        effects="effect/flip/-/effect/mirror/", store=True
    )
    assert copied_file.is_stored()

    copied_file = file.create_local_copy(
        effects="effect/flip/-/effect/mirror/", store=False
    )
    assert not copied_file.is_stored()


@pytest.mark.vcr
def test_file_delete():
    file = File("35ea470d-216c-4752-91d2-5176b34c1225").create_local_copy(
        effects="effect/flip/-/effect/mirror/",
        store=True,
    )
    assert file.is_stored()
    assert not file.is_removed()
    file.delete()
    assert file.is_removed()


@pytest.mark.vcr
def test_file_list_iterate():
    count = 10
    iterated_count = 0
    for file in FileList(limit=10):
        assert isinstance(file, File)
        assert file.is_stored()
        iterated_count += 1

    assert iterated_count == count
