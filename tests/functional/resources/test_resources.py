import pytest

from pyuploadcare import File, FileList


@pytest.mark.vcr
def test_file_upload(small_file):
    with open(small_file.name, "rb") as fh:
        file = File.upload(fh)

    assert isinstance(file, File)
    assert file.is_stored()


@pytest.mark.vcr
def test_file_upload_secure(small_file, signed_uploads):

    with open(small_file.name, "rb") as fh:
        file = File.upload(fh)

    assert isinstance(file, File)
    assert file.is_stored()


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
