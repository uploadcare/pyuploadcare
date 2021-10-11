from typing import List, Optional, Union

from pyuploadcare.transformations.base import BaseTransformation, StrEnum


class StretchMode(StrEnum):
    on = "on"
    off = "off"
    fill = "fill"


class CropAlignment(StrEnum):
    center = "center"  # type: ignore
    top = "top"
    right = "right"
    bottom = "bottom"
    left = "left"


class ScaleCropMode(StrEnum):
    center = "center"  # type: ignore
    smart = "smart"
    smart_faces_objects = "smart_faces_objects"
    smart_faces_points = "smart_faces_points"
    smart_objects_faces_points = "smart_objects_faces_points"
    smart_objects_faces = "smart_objects_faces"
    smart_objects_points = "smart_objects_points"
    smart_points = "smart_points"
    smart_objects = "smart_objects"
    smart_faces = "smart_faces"


class ImageFormat(StrEnum):
    jpeg = "jpeg"
    png = "png"
    webp = "webp"
    auto = "auto"


class ImageQuality(StrEnum):
    normal = "normal"
    better = "better"
    best = "best"
    lighter = "lighter"
    lightest = "lightest"
    smart = "smart"
    smart_retina = "smart_retina"


class Gif2VideoFormat(StrEnum):
    mp4 = "mp4"
    webm = "webm"


class Gif2VideoQuality(StrEnum):
    lightest = "lightest"
    lighter = "lighter"
    normal = "normal"
    better = "better"
    best = "best"


class ColorAdjustment(StrEnum):
    brightness = "brightness"
    exposure = "exposure"
    gamma = "gamma"
    contrast = "contrast"
    saturation = "saturation"
    vibrance = "vibrance"
    warmth = "warmth"


class ImageFilter(StrEnum):
    adaris = "adaris"
    briaril = "briaril"
    calarel = "calarel"
    carris = "carris"
    cynarel = "cynarel"
    cyren = "cyren"
    elmet = "elmet"
    elonni = "elonni"
    enzana = "enzana"
    erydark = "erydark"
    fenralan = "fenralan"
    ferand = "ferand"
    galen = "galen"
    gavin = "gavin"
    gethriel = "gethriel"
    iorill = "iorill"
    iothari = "iothari"
    iselva = "iselva"
    jadis = "jadis"
    lavra = "lavra"
    misiara = "misiara"
    namala = "namala"
    nerion = "nerion"
    nethari = "nethari"
    pamaya = "pamaya"
    sarnar = "sarnar"
    sedis = "sedis"
    sewen = "sewen"
    sorahel = "sorahel"
    sorlen = "sorlen"
    tarian = "tarian"
    thellassan = "thellassan"
    varriel = "varriel"
    varven = "varven"
    vevera = "vevera"
    virkas = "virkas"
    yedis = "yedis"
    yllara = "yllara"
    zatvel = "zatvel"
    zevcen = "zevcen"


class SRGBConversion(StrEnum):
    fast = "fast"
    icc = "icc"
    keep_profile = "keep_profile"


class OverlayOffset(StrEnum):
    left = "left"
    right = "right"
    top = "top"
    bottom = "bottom"
    center = "center"  # type: ignore


class ImageTransformation(BaseTransformation):
    def preview(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> "ImageTransformation":
        parameters: List[str] = []

        if width or height:
            parameters.append(f'{width or ""}x{height or ""}')

        self.set("preview", parameters)
        return self

    def resize(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> "ImageTransformation":
        parameters = [f'{width or ""}x{height or ""}']
        self.set("resize", parameters)
        return self

    def stretch(self, mode: StretchMode) -> "ImageTransformation":
        self.set("stretch", [mode])
        return self

    def smart_resize(self, width: int, height: int) -> "ImageTransformation":
        parameters: List[str] = [f"{width}x{height}"]
        self.set("smart_resize", parameters)
        return self

    def crop(
        self,
        width: int,
        height: int,
        offset_x: Optional[Union[int, str]] = None,
        offset_y: Optional[Union[int, str]] = None,
        alignment: Optional[CropAlignment] = None,
    ) -> "ImageTransformation":
        parameters: List[str] = [f"{width}x{height}"]

        if alignment:
            parameters.append(alignment)
        elif offset_x and offset_y:
            parameters.append(f"{offset_x},{offset_y}")

        self.set("crop", parameters)
        return self

    def scale_crop(
        self,
        width: int,
        height: int,
        offset_x_percent: Optional[int] = None,
        offset_y_percent: Optional[int] = None,
        mode: Optional[ScaleCropMode] = None,
    ) -> "ImageTransformation":
        parameters: List[str] = [f"{width}x{height}"]

        if offset_x_percent and offset_y_percent:
            parameters.append(f"{offset_x_percent}p,{offset_y_percent}p")
        elif mode:
            parameters.append(mode)
        self.set("scale_crop", parameters)
        return self

    def setfill(self, color: str) -> "ImageTransformation":
        self.set("setfill", [color])
        return self

    def format(self, image_format: ImageFormat) -> "ImageTransformation":
        self.set("format", [image_format])
        return self

    def quality(self, image_quality: ImageQuality) -> "ImageTransformation":
        self.set("quality", [image_quality])
        return self

    def progressive(self, is_progressive=True) -> "ImageTransformation":
        self.set("progressive", ["yes" if is_progressive else "no"])
        return self

    def gif2video(self) -> "ImageTransformation":
        self.set("gif2video", [])
        return self

    def gif2video_format(
        self, format: Gif2VideoFormat
    ) -> "ImageTransformation":
        self.set("format", [format])
        return self

    def gif2video_quality(
        self, quality: Gif2VideoQuality
    ) -> "ImageTransformation":
        self.set("quality", [quality])
        return self

    def adjust_color(
        self, adjustment: ColorAdjustment, value: Optional[int] = None
    ) -> "ImageTransformation":
        parameters: List[str] = []
        if value is not None:
            parameters.append(str(value))
        self.set(str(adjustment), parameters)
        return self

    def enhance(self, value: Optional[int] = None) -> "ImageTransformation":
        parameters: List[str] = []
        if value is not None:
            parameters.append(str(value))
        self.set("enhance", parameters)
        return self

    def grayscale(self) -> "ImageTransformation":
        self.set("grayscale", [])
        return self

    def invert(self) -> "ImageTransformation":
        self.set("invert", [])
        return self

    def filter(
        self, image_filter: ImageFilter, value: Optional[int] = None
    ) -> "ImageTransformation":
        parameters: List[str] = [image_filter]
        if value is not None:
            parameters.append(str(value))
        self.set("filter", parameters)
        return self

    def srgb(self, conversion: SRGBConversion) -> "ImageTransformation":
        parameters: List[str] = [conversion]
        self.set("srgb", parameters)
        return self

    def max_icc_size(self, threshold: int) -> "ImageTransformation":
        parameters: List[str] = [str(threshold)]
        self.set("max_icc_size", parameters)
        return self

    def blur(
        self, strength: Optional[int] = None, amount: Optional[int] = None
    ) -> "ImageTransformation":
        parameters: List[str] = []
        if strength:
            parameters.append(str(strength))
            if amount:
                parameters.append(str(amount))
        self.set("blur", parameters)
        return self

    def blur_region(
        self,
        region_width: Union[str, int],
        region_height: Union[str, int],
        offset_x: Union[str, int],
        offset_y: Union[str, int],
        strength: Optional[int] = None,
    ) -> "ImageTransformation":
        parameters: List[str] = [
            f"{region_width}x{region_height}",
            f"{offset_x},{offset_y}",
        ]
        if strength is not None:
            parameters.append(str(strength))
        self.set("blur_region", parameters)
        return self

    def blur_faces(
        self, strength: Optional[int] = None
    ) -> "ImageTransformation":
        parameters: List[str] = ["faces"]
        if strength is not None:
            parameters.append(str(strength))
        self.set("blur_region", parameters)
        return self

    def sharp(self, strength: Optional[int] = None) -> "ImageTransformation":
        parameters: List[str] = []
        if strength is not None:
            parameters.append(str(strength))
        self.set("sharp", parameters)
        return self

    def overlay(
        self,
        uuid: str,
        overlay_width: Union[str, int],
        overlay_height: Union[str, int],
        offset: Optional[OverlayOffset] = None,
        offset_x: Optional[Union[str, int]] = None,
        offset_y: Optional[Union[str, int]] = None,
        strength: Optional[int] = None,
    ) -> "ImageTransformation":
        parameters: List[str] = [
            uuid,
            f"{overlay_width}x{overlay_height}",
        ]

        if offset:
            parameters.append(str(offset))
        else:
            parameters.append(f"{offset_x},{offset_y}")

        if strength is not None:
            parameters.append(f"{strength}p")

        self.set("overlay", parameters)
        return self

    def overlay_self(
        self,
        overlay_width: Union[str, int],
        overlay_height: Union[str, int],
        offset: Optional[OverlayOffset] = None,
        offset_x: Optional[Union[str, int]] = None,
        offset_y: Optional[Union[str, int]] = None,
        strength: Optional[int] = None,
    ) -> "ImageTransformation":
        parameters: List[str] = [
            "self",
            f"{overlay_width}x{overlay_height}",
        ]

        if offset:
            parameters.append(offset)
        else:
            parameters.append(f"{offset_x},{offset_y}")

        if strength is not None:
            parameters.append(f"{strength}p")

        self.set("overlay", parameters)
        return self

    def autorotate(self, enabled=True) -> "ImageTransformation":
        parameters: List[str] = ["yes" if enabled else "no"]
        self.set("autorotate", parameters)
        return self

    def rotate(self, angle: int) -> "ImageTransformation":
        parameters: List[str] = [str(angle)]
        self.set("rotate", parameters)
        return self

    def flip(self) -> "ImageTransformation":
        self.set("flip", [])
        return self

    def mirror(self) -> "ImageTransformation":
        self.set("mirror", [])
        return self

    def path(self, file_id: str) -> str:
        path_ = super().path(file_id)
        path_ = path_.replace("/-/gif2video", "/gif2video")
        return path_
