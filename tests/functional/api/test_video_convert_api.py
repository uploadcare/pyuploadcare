import pytest

from pyuploadcare.api import api
from pyuploadcare.transformations.video import VideoFormat, VideoTransformation


@pytest.mark.vcr
def test_convert_video():
    video_convert_api = api.VideoConvertAPI()
    transformation = VideoTransformation().format(VideoFormat.webm).thumbs(2)

    path = transformation.path("740e1b8c-1ad8-4324-b7ec-112c79d8eac2")

    response = video_convert_api.convert([path])

    assert not response.problems

    video_convert_info = response.result[0]

    response = video_convert_api.status(video_convert_info.token)

    assert response.result.uuid
