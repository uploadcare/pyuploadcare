import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from pyuploadcare import File, FileGroup, FileList, GroupList
from pyuploadcare.resources.file import UploadProgress
from pyuploadcare.transformations.document import (
    DocumentFormat,
    DocumentTransformation,
)
from pyuploadcare.transformations.image import ImageTransformation
from pyuploadcare.transformations.video import VideoFormat, VideoTransformation


TEST_RESOURCE_METADATA = {
    "one_key": "has rather string, but the neighbour has almost number",
    "score": "56",
}


@pytest.mark.vcr
def test_file_upload(small_file, uploadcare):
    with open(small_file.name, "rb") as fh:
        file = uploadcare.upload(fh)

    assert isinstance(file, File)
    assert file.is_stored


def test_file_upload_callback(small_file, vcr, uploadcare):
    progresses = []

    def callback(upload_progress: UploadProgress):
        progresses.append(upload_progress)

    with open(small_file.name, "rb") as fh:
        with vcr.use_cassette("test_file_upload"):
            file = uploadcare.upload(fh, callback=callback)

    assert isinstance(file, File)
    assert progresses
    assert isinstance(progresses[0], UploadProgress)


@pytest.mark.vcr
def test_file_upload_big_file(big_file, uploadcare):
    with open(big_file.name, "rb") as fh:
        file = uploadcare.upload(fh, store=True)

    assert isinstance(file, File)
    assert file.is_ready


@pytest.mark.vcr
def test_file_upload_with_metadata(memo_file, uploadcare, vcr):
    stream, size = memo_file

    file = uploadcare.upload(
        stream, store=True, metadata=TEST_RESOURCE_METADATA, size=size
    )

    assert isinstance(file, File)

    file.update_info()

    assert file.is_ready
    assert file.info["metadata"] == TEST_RESOURCE_METADATA


@pytest.mark.vcr
def test_file_upload_big_file_callback(big_file, vcr, uploadcare):
    progresses = []

    def callback(upload_progress: UploadProgress):
        progresses.append(upload_progress)

    with open(big_file.name, "rb") as fh:
        with vcr.use_cassette("test_file_upload_big_file"):
            file = uploadcare.upload(fh, store=True, callback=callback)

    assert isinstance(file, File)
    assert progresses
    assert isinstance(progresses[0], UploadProgress)


@pytest.mark.vcr
def test_file_upload_by_url(uploadcare):
    file = uploadcare.upload(
        "https://github.githubassets.com/images/modules/logos_page/Octocat.png"
    )
    assert isinstance(file, File)
    assert file.is_ready


@pytest.mark.vcr
def test_file_upload_by_url_with_metadata(uploadcare):
    file = uploadcare.upload(
        "https://github.githubassets.com/images/modules/logos_page/Octocat.png",
        metadata=TEST_RESOURCE_METADATA,
        store=False,
    )
    assert isinstance(file, File)
    assert file.is_ready
    assert file.info["metadata"] == TEST_RESOURCE_METADATA


@pytest.mark.vcr
def test_file_upload_by_url_callback(vcr, uploadcare):
    progresses = []

    def callback(upload_progress: UploadProgress):
        progresses.append(upload_progress)

    with vcr.use_cassette("test_file_upload_by_url"):
        file = uploadcare.upload(
            "https://github.githubassets.com/images/modules/logos_page/Octocat.png",
            callback=callback,
        )
    assert isinstance(file, File)


@pytest.mark.vcr
def test_file_upload_multiple(small_file, small_file2, uploadcare):
    with open(small_file.name, mode="rb") as file1, open(
        small_file2.name, mode="rb"
    ) as file2:
        files = uploadcare.upload_files([file1, file2])
        created_filenames = [file.filename for file in files]
        assert sorted(created_filenames) == sorted(
            [
                os.path.basename(input_file.name)
                for input_file in [small_file, small_file2]
            ]
        )


@pytest.mark.freeze_time("2021-10-12")
def test_file_upload_signature(small_file, uploadcare, signed_uploads):
    assert uploadcare.signed_uploads
    fake_response = MagicMock()
    fake_response.json.return_value = {
        "sample1.txt": "96e0a8f8-91f3-4162-907d-2d67d36ebae8"
    }
    with open(small_file.name, "rb") as fh:
        with patch.object(
            uploadcare.upload_api._client, "post", return_value=fake_response
        ) as mocked_post:
            uploadcare.upload(fh)

    assert mocked_post.called
    data = mocked_post.call_args[1]["data"]
    expected_expire = datetime.now() + timedelta(
        seconds=uploadcare.signed_uploads_ttl
    )
    assert data["expire"] == str(int(expected_expire.timestamp()))
    assert (
        data["signature"]
        == "f7d27174ad85736b9a4ace81a3cf420b99b2ddc78415b00adfc0c326a39cb490"
    )


@pytest.mark.vcr
def test_file_create_local_copy(uploadcare):
    file = uploadcare.file("35ea470d-216c-4752-91d2-5176b34c1225")
    copied_file = file.create_local_copy(
        effects="effect/flip/-/effect/mirror/", store=True
    )
    assert copied_file.is_stored

    copied_file = file.create_local_copy(
        effects="effect/flip/-/effect/mirror/", store=False
    )
    assert not copied_file.is_stored


@pytest.mark.vcr
def test_file_delete(uploadcare):
    file = uploadcare.file(
        "35ea470d-216c-4752-91d2-5176b34c1225"
    ).create_local_copy(
        effects="effect/flip/-/effect/mirror/",
        store=True,
    )
    assert file.is_stored
    assert not file.is_removed
    file.delete()
    assert file.is_removed


@pytest.mark.vcr
def test_file_list_iterate(uploadcare):
    count = 10
    iterated_count = 0
    for file in uploadcare.list_files(limit=10):
        assert isinstance(file, File)
        assert file.is_stored
        iterated_count += 1

    assert iterated_count == count


@pytest.mark.vcr
def test_file_convert_video(uploadcare):
    file = uploadcare.file("740e1b8c-1ad8-4324-b7ec-112c79d8eac2")
    transformation = VideoTransformation().format(VideoFormat.webm).thumbs(2)
    converted_file = file.convert(transformation)
    assert not converted_file.is_ready
    assert converted_file.thumbnails_group_uuid


@pytest.mark.vcr
def test_file_convert_document(uploadcare):
    file = uploadcare.file("0e1cac48-1296-417f-9e7f-9bf13e330dcf")
    transformation = DocumentTransformation().format(DocumentFormat.pdf)
    converted_file = file.convert(transformation)
    assert not converted_file.is_ready


@pytest.mark.vcr
def test_file_convert_document_with_save_in_group(uploadcare):
    file = uploadcare.file("da288a95-3029-4044-b902-5107e8579c5c")
    transformation = DocumentTransformation().format(DocumentFormat.jpg)
    converted_file = file.convert(transformation, save_in_group=True)
    assert not converted_file.is_ready


@pytest.mark.vcr
def test_file_get_converted_document_group(uploadcare):
    file = uploadcare.file("da288a95-3029-4044-b902-5107e8579c5c")
    group = file.get_converted_document_group(DocumentFormat.jpg)
    assert isinstance(group, FileGroup)
    assert group.id == "f56f1e80-31f8-426e-9213-690861252070~4"


@pytest.mark.vcr
def test_file_info_has_new_structure(uploadcare):
    """
    Test new structure of response since API v0.7

    """
    (file,) = list(
        uploadcare.list_files(limit=1)
    )  # uploadcare.file("35ea470d-216c-4752-91d2-5176b34c1225")
    info = file.info

    assert "rekognition_info" not in info
    assert "image_info" not in info
    assert "video_info" not in info

    assert "content_info" in info

    content_info = info.get("content_info")
    assert "mime" in content_info

    assert "appdata" in info


@pytest.mark.vcr
def test_file_convert_document_page(uploadcare):
    file = uploadcare.file("5dddafa0-a742-4a51-ac40-ae491201ff97")
    transformation = (
        DocumentTransformation().format(DocumentFormat.png).page(1)
    )
    converted_file = file.convert(transformation)
    assert not converted_file.is_ready


@pytest.fixture
def image_transformation():
    return ImageTransformation().grayscale().flip()


def test_cdn_url_default_effects(uploadcare, image_transformation):
    file = uploadcare.file("5dddafa0-a742-4a51-ac40-ae491201ff97")
    file.set_effects(image_transformation)

    assert file.cdn_url == (
        "https://ucarecdn.com/5dddafa0-a742-4a51-ac40-ae491201ff97/"
        "-/grayscale/-/flip/"
    )


@pytest.mark.vcr
def test_create_local_copy_with_transformation(
    uploadcare, image_transformation
):
    file = uploadcare.file("463c38f7-8a27-46bb-bebc-2e0617d159a4")
    copied_file = file.create_local_copy(
        effects=image_transformation, store=True
    )
    assert copied_file


@pytest.mark.vcr
def test_create_file_group(uploadcare):
    file = uploadcare.file("94a2218e-3526-428a-945e-65fbc06e7b35")
    group = uploadcare.create_file_group([file])
    assert "files" in group.info


@pytest.mark.vcr
def test_delete_file_group_with_files(uploadcare):
    group = uploadcare.file_group("2e481e82-2e39-41be-a5a2-23802c6e341c~2")
    assert not group.is_deleted
    for file in group:
        file.update_info()
        assert not file.is_removed

    group.delete(delete_files=True)

    assert group.is_deleted
    for file in group:
        file.update_info()
        assert file.is_removed


@pytest.mark.vcr
def test_get_file_group(uploadcare):
    group = uploadcare.file_group("d496a4df-0b36-4281-8156-268ae9524d4a~1")
    assert group.info
    assert isinstance(group[0], File)


@pytest.mark.vcr
def test_get_group_with_deleted_files(uploadcare):
    group = uploadcare.file_group("8b1362ed-b477-4a15-819a-2c6bb497d8bd~3")
    assert group.info
    assert group[0] is None
    for file in group:
        assert file is None


@pytest.mark.vcr
def test_list_file_groups(uploadcare):
    groups_list = uploadcare.list_file_groups(limit=5)
    assert isinstance(groups_list, GroupList)

    with pytest.raises(IndexError):
        groups_list[10]

    groups = groups_list[0:2]
    assert len(groups) == 2
    assert isinstance(groups[0], FileGroup)


@pytest.mark.vcr
def test_list_files(uploadcare):
    file_list = uploadcare.list_files(limit=5)
    assert isinstance(file_list, FileList)

    with pytest.raises(IndexError):
        file_list[10]

    files = file_list[0:2]
    assert len(files) == 2
    assert isinstance(files[0], File)


@pytest.mark.vcr
def test_retrieve_fileinfo_with_metadata(uploadcare):
    file_ = uploadcare.file("a55d6b25-d03c-4038-9838-6e06bb7df598")
    assert isinstance(file_, File)
    assert file_.info

    metadata_dict = file_.info["metadata"]
    assert len(metadata_dict) == 2


@pytest.mark.vcr
def test_retrieve_fileinfo_with_appdata(uploadcare):
    file_ = uploadcare.file("04bd49fa-466d-49e7-afd7-bac108055371")
    assert isinstance(file_, File)
    file_.update_info(include_appdata=True)
    assert file_.info
    appdata = file_.info["appdata"]

    assert "aws_rekognition_detect_labels" in appdata
    labels_data = appdata["aws_rekognition_detect_labels"]
    labels_details = labels_data["data"]
    assert labels_details["label_model_version"]
    assert len(labels_details["labels"]) == 10
    label = labels_details["labels"][0]
    assert label["confidence"]
    assert label["name"] == "Accessories"

    assert "aws_rekognition_detect_moderation_labels" in appdata
    moderation_data = appdata["aws_rekognition_detect_moderation_labels"]
    moderation_details = moderation_data["data"]
    assert moderation_details["label_model_version"]
    assert len(moderation_details["labels"]) == 1
    moderation_label = moderation_details["labels"][0]
    assert moderation_label["confidence"]
    assert moderation_label["name"] == "Weapons"
    assert moderation_label["parent_name"] == "Violence"
