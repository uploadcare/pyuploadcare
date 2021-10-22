from pyuploadcare.transformations.image import (
    ColorAdjustment,
    CropAlignment,
    Gif2VideoFormat,
    Gif2VideoQuality,
    ImageFilter,
    ImageFormat,
    ImageQuality,
    ImageTransformation,
    OverlayOffset,
    ScaleCropMode,
    SRGBConversion,
    StretchMode,
)


def test_image_transformation_path():
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

    assert str(transformation) == ("smart_resize/440x600/-/quality/smart/")


def test_image_crop():
    transformation = ImageTransformation().crop(
        2000, 1325, alignment=CropAlignment.center
    )

    assert str(transformation) == "crop/2000x1325/center/"


def test_image_crop_offset():
    transformation = ImageTransformation().crop(
        640, 424, offset_x=2560, offset_y=830
    )

    assert str(transformation) == "crop/640x424/2560,830/"


def test_image_scale_crop():
    transformation = ImageTransformation().scale_crop(
        1024, 1024, mode=ScaleCropMode.center
    )

    assert str(transformation) == "scale_crop/1024x1024/center/"


def test_setfill():
    transformation = (
        ImageTransformation().setfill("ece3d2").format(ImageFormat.jpeg)
    )

    assert str(transformation) == "setfill/ece3d2/-/format/jpeg/"


def test_image_progressive():
    transformation = (
        ImageTransformation()
        .preview()
        .quality(ImageQuality.best)
        .progressive()
    )

    assert str(transformation) == "preview/-/quality/best/-/progressive/yes/"


def test_image_gif2video():
    transformation = (
        ImageTransformation()
        .gif2video()
        .gif2video_quality(Gif2VideoQuality.lighter)
        .gif2video_format(Gif2VideoFormat.webm)
    )

    assert str(transformation) == "gif2video/-/quality/lighter/-/format/webm/"

    assert transformation.path("af0136cc-c60a-49a3-a10f-f9319f0ce7e1") == (
        "af0136cc-c60a-49a3-a10f-f9319f0ce7e1/gif2video/-/quality/lighter/-/format/webm/"
    )


def test_image_color_adjustment():
    transformation = (
        ImageTransformation()
        .preview()
        .adjust_color(ColorAdjustment.saturation, -80)
        .adjust_color(ColorAdjustment.contrast, 80)
        .adjust_color(ColorAdjustment.warmth, 50)
    )

    assert (
        str(transformation)
        == "preview/-/saturation/-80/-/contrast/80/-/warmth/50/"
    )


def test_image_enhance():
    transformation = ImageTransformation().preview().enhance(50)

    assert str(transformation) == "preview/-/enhance/50/"


def test_image_grayscale():
    transformation = ImageTransformation().preview().grayscale()

    assert str(transformation) == "preview/-/grayscale/"


def test_image_invert():
    transformation = ImageTransformation().preview().invert()

    assert str(transformation) == "preview/-/invert/"


def test_image_filter():
    transformation = (
        ImageTransformation().preview().filter(ImageFilter.briaril)
    )

    assert str(transformation) == "preview/-/filter/briaril/"


def test_image_color_profile():
    transformation = ImageTransformation().preview().srgb(SRGBConversion.fast)

    assert str(transformation) == "preview/-/srgb/fast/"


def test_image_max_icc_size():
    transformation = (
        ImageTransformation()
        .max_icc_size(0)
        .srgb(SRGBConversion.fast)
        .preview()
    )

    assert str(transformation) == "max_icc_size/0/-/srgb/fast/-/preview/"


def test_image_blur():
    transformation = ImageTransformation().preview().blur(20)

    assert str(transformation) == "preview/-/blur/20/"


def test_image_blur_region():
    transformation = (
        ImageTransformation()
        .preview(440, 400)
        .blur_region(130, 180, offset_x=220, offset_y=25)
    )
    assert (
        str(transformation) == "preview/440x400/-/blur_region/130x180/220,25/"
    )


def test_image_blur_region_percent():
    transformation = (
        ImageTransformation()
        .preview(440, 400)
        .blur_region("30p", "80p", offset_x="50p", offset_y="10p", strength=20)
    )
    assert (
        str(transformation)
        == "preview/440x400/-/blur_region/30px80p/50p,10p/20/"
    )


def test_image_blur_faces():
    transformation = ImageTransformation().preview(440, 440).blur_faces(250)
    assert str(transformation) == "preview/440x440/-/blur_region/faces/250/"


def test_image_unsharp():
    transformation = ImageTransformation().scale_crop(880, 600).blur(200, -120)
    assert str(transformation) == "scale_crop/880x600/-/blur/200/-120/"


def tes_image_sharp():
    transformation = ImageTransformation().preview(600, 600).sharp(20)
    assert str(transformation) == "preview/600x600/-/sharp/20/"


def test_overlay():
    transformation = (
        ImageTransformation()
        .overlay(
            "b18b5179-b9f6-4fdc-9920-5539f938fc44",
            "50p",
            "50p",
            offset=OverlayOffset.center,
        )
        .preview()
    )
    assert str(transformation) == (
        "overlay/b18b5179-b9f6-4fdc-9920-5539f938fc44/50px50p/"
        "center/-/preview/"
    )


def test_overlay_multiple():
    transformation = (
        ImageTransformation()
        .overlay(
            "efd02791-7511-42e9-850d-3b3d07f110ae",
            "35p",
            "35p",
            offset_x="10p",
            offset_y="10p",
            strength=40,
        )
        .overlay(
            "b18b5179-b9f6-4fdc-9920-5539f938fc44",
            "35p",
            "35p",
            offset_x="70p",
            offset_y="5p",
            strength=35,
        )
        .overlay(
            "b18b5179-b9f6-4fdc-9920-5539f938fc44",
            "35p",
            "35p",
            offset_x="15p",
            offset_y="70p",
            strength=55,
        )
        .overlay(
            "efd02791-7511-42e9-850d-3b3d07f110ae",
            "35p",
            "35p",
            offset_x="80p",
            offset_y="90p",
            strength=50,
        )
        .preview()
    )
    assert str(transformation) == (
        "overlay/efd02791-7511-42e9-850d-3b3d07f110ae/35px35p/10p,10p/40p/"
        "-/overlay/b18b5179-b9f6-4fdc-9920-5539f938fc44/35px35p/70p,5p/35p/"
        "-/overlay/b18b5179-b9f6-4fdc-9920-5539f938fc44/35px35p/15p,70p/55p/"
        "-/overlay/efd02791-7511-42e9-850d-3b3d07f110ae/35px35p/80p,90p/50p/"
        "-/preview/"
    )


def test_overlay_self():
    transformation = (
        ImageTransformation()
        .scale_crop(440, 440, mode=ScaleCropMode.center)
        .blur(60)
        .adjust_color(ColorAdjustment.gamma, 50)
        .overlay_self("100p", "100p", offset=OverlayOffset.center)
    )
    assert str(transformation) == (
        "scale_crop/440x440/center/-/blur/60/-/gamma/50/-/overlay/self/100px100p/center/"
    )


def test_image_autorotate():
    transformation = ImageTransformation().preview().autorotate(False)
    assert str(transformation) == "preview/-/autorotate/no/"


def test_image_rotate():
    transformation = ImageTransformation().preview().rotate(270)
    assert str(transformation) == "preview/-/rotate/270/"


def test_image_flip():
    transformation = ImageTransformation().preview().flip()
    assert str(transformation) == "preview/-/flip/"


def test_image_mirror():
    transformation = ImageTransformation().preview().mirror()
    assert str(transformation) == "preview/-/mirror/"


def test_transformation_create_from_another():
    transformation = ImageTransformation().preview().mirror()
    assert str(transformation) == "preview/-/mirror/"

    new_transformation = ImageTransformation(transformation)
    assert str(new_transformation) == transformation.effects


def test_transformation_create_from_str():
    transformation = "preview/-/mirror/"

    new_transformation = ImageTransformation(transformation)
    assert new_transformation.effects == transformation

    new_transformation = new_transformation.flip()
    assert str(new_transformation) == "preview/-/mirror/-/flip/"
