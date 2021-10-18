from pyuploadcare.transformations.video import (
    Quality,
    ResizeMode,
    VideoFormat,
    VideoTransformation,
)


def test_video_transformation():
    transformation = (
        VideoTransformation()
        .format(VideoFormat.mp4)
        .size(width=640, height=480, resize_mode=ResizeMode.add_padding)
        .quality(Quality.lighter)
        .cut(start_time="2:30.535", length="2:20.0")
        .thumbs(10)
    )

    assert transformation.path("a6efd840-076f-4227-9073-bbaef16cfe35") == (
        "a6efd840-076f-4227-9073-bbaef16cfe35/video/-/format/mp4/"
        "-/size/640x480/add_padding/-/quality/lighter/"
        "-/cut/2:30.535/2:20.0/-/thumbs~10/"
    )


def test_video_transformation_order_matters():
    transformation = (
        VideoTransformation()
        .size(width=640, height=480, resize_mode=ResizeMode.add_padding)
        .quality(Quality.lighter)
        .cut(start_time="2:30.535", length="2:20.0")
        .format(VideoFormat.mp4)
        .thumbs(10)
    )

    assert transformation.path("a6efd840-076f-4227-9073-bbaef16cfe35") == (
        "a6efd840-076f-4227-9073-bbaef16cfe35/video/"
        "-/size/640x480/add_padding/-/quality/lighter/"
        "-/cut/2:30.535/2:20.0/-/format/mp4/-/thumbs~10/"
    )


def test_video_transformation_custom_without_parameters():
    transformation = VideoTransformation().set("custom", []).thumbs(10)

    assert transformation.path("a6efd840-076f-4227-9073-bbaef16cfe35") == (
        "a6efd840-076f-4227-9073-bbaef16cfe35/video/" "-/custom/-/thumbs~10/"
    )
