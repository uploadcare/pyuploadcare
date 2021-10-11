from pyuploadcare.transformations.image import (
    ImageQuality,
    ImageTransformation,
    StretchMode, CropAlignment, ScaleCropMode, ImageFormat, Gif2VideoQuality, Gif2VideoFormat, ImageFilter,
    ColorAdjustment, SRGBConversion,
)


def test_image_quality_preview_setfill_stretch_resize():
    transformation = (
        ImageTransformation()
        .quality(ImageQuality.best)
        .preview(160, 160)
        .setfill("8d8578")
        .stretch(StretchMode.fill)
        .resize(220)
    )
    assert str(transformation) == (
        "quality/best/-/preview/160x160/"
        "-/setfill/8d8578/-/stretch/fill/-/resize/220x/"
    )
    assert transformation.path("52da3bfc-7cd8-4861-8b05-126fef7a6994") == (
        "52da3bfc-7cd8-4861-8b05-126fef7a6994/"
        "-/quality/best/-/preview/160x160/"
        "-/setfill/8d8578/-/stretch/fill/-/resize/220x/"
    )


def test_image_smart_resize():
    transformation = (
        ImageTransformation()
        .smart_resize(440, 600)
        .quality(ImageQuality.smart)
    )

    assert str(transformation) == (
        'smart_resize/440x600/-/quality/smart/'
    )


def test_image_crop():
    transformation = (
        ImageTransformation()
        .crop(2000, 1325, alignment=CropAlignment.center)
    )

    assert str(transformation) == 'crop/2000x1325/center/'


def test_image_crop_offset():
    transformation = (
        ImageTransformation()
        .crop(640, 424, offset_x=2560, offset_y=830)
    )

    assert str(transformation) == 'crop/640x424/2560,830/'


def test_image_scale_crop():
    transformation = (
        ImageTransformation()
        .scale_crop(1024, 1024, mode=ScaleCropMode.center)
    )

    assert str(transformation) == 'scale_crop/1024x1024/center/'


def test_setfill():
    transformation = (
        ImageTransformation()
        .setfill('ece3d2')
        .format(ImageFormat.jpeg)
    )

    assert str(transformation) == 'setfill/ece3d2/-/format/jpeg/'


def test_image_progressive():
    transformation = (
        ImageTransformation()
        .preview()
        .quality(ImageQuality.best)
        .progressive()
    )

    assert str(transformation) == 'preview/-/quality/best/-/progressive/yes/'


def test_image_gif2video():
    transformation = (
        ImageTransformation()
            .gif2video()
            .gif2video_quality(Gif2VideoQuality.lighter)
            .gif2video_format(Gif2VideoFormat.webm)
    )

    assert str(transformation) == 'gif2video/-/quality/lighter/-/format/webm/'

    assert transformation.path('af0136cc-c60a-49a3-a10f-f9319f0ce7e1') == (
        'af0136cc-c60a-49a3-a10f-f9319f0ce7e1/gif2video/-/quality/lighter/-/format/webm/'
    )


def test_image_color_adjustment():
    transformation = (
        ImageTransformation()
        .preview()
        .adjust_color(ColorAdjustment.saturation, -80)
        .adjust_color(ColorAdjustment.contrast, 80)
        .adjust_color(ColorAdjustment.warmth, 50)
    )

    assert str(transformation) == 'preview/-/saturation/-80/-/contrast/80/-/warmth/50/'


def test_image_enhance():
    transformation = ImageTransformation().preview().enhance(50)

    assert str(transformation) == 'preview/-/enhance/50/'


def test_image_grayscale():
    transformation = ImageTransformation().preview().grayscale()

    assert str(transformation) == 'preview/-/grayscale/'


def test_image_invert():
    transformation = ImageTransformation().preview().invert()

    assert str(transformation) == 'preview/-/invert/'


def test_image_filter():
    transformation = ImageTransformation().preview().filter(ImageFilter.briaril)

    assert str(transformation) == 'preview/-/filter/briaril/'


def test_image_color_profile():
    transformation = ImageTransformation().preview().srgb(SRGBConversion.fast)

    assert str(transformation) == 'preview/-/srgb/fast/'


def test_image_max_icc_size():
    transformation = ImageTransformation().max_icc_size(0).srgb(SRGBConversion.fast).preview()

    assert str(transformation) == 'max_icc_size/0/-/srgb/fast/-/preview/'


def test_image_blur():
    transformation = ImageTransformation().preview().blur(20)

    assert str(transformation) == 'preview/-/blur/20/'


def test_image_blur_region():
    transformation = (
        ImageTransformation()
        .preview(440, 400)
        .blur_region(130, 180, offset_x=220, offset_y=25)
    )
    assert str(transformation) == 'preview/440x400/-/blur_region/130x180/220,25/'


def test_image_blur_region_percent():
    transformation = (
        ImageTransformation()
        .preview(440, 400)
        .blur_region('30p', '80p', offset_x='50p', offset_y='10p', strength=20)
    )
    assert str(transformation) == 'preview/440x400/-/blur_region/30px80p/50p,10p/20/'


def test_image_blur_faces():
    transformation = (
        ImageTransformation()
        .preview(440, 440)
        .blur_faces(250)
    )
    assert str(transformation) == 'preview/440x440/-/blur_region/faces/250/'
