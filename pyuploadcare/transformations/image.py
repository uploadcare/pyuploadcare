import warnings
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
    """
    https://uploadcare.com/docs/transformations/image/compression/#operation-format
    """

    jpeg = "jpeg"
    png = "png"
    webp = "webp"
    auto = "auto"
    preserve = "preserve"


class ImageQuality(StrEnum):
    normal = "normal"
    better = "better"
    best = "best"
    lighter = "lighter"
    lightest = "lightest"
    smart = "smart"
    smart_retina = "smart_retina"


class StripMetaMode(StrEnum):
    all = "all"
    none = "none"
    sensitive = "sensitive"


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


class HorizontalTextAlignment(StrEnum):
    """
    https://uploadcare.com/docs/transformations/image/overlay/#text-alignment
    """

    left = "left"
    center = "center"  # type: ignore
    right = "right"


class VerticalTextAlignment(StrEnum):
    """
    https://uploadcare.com/docs/transformations/image/overlay/#text-alignment
    """

    top = "top"
    center = "center"  # type: ignore
    bottom = "bottom"


class TextBoxMode(StrEnum):
    """
    https://uploadcare.com/docs/transformations/image/overlay/#text-background-box
    """

    none = "none"
    fit = "fit"
    line = "line"
    fill = "fill"


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

    def border_radius(
        self,
        radii: Union[int, str, List[Union[int, str]]],
        vertical_radii: Optional[
            Union[int, str, List[Union[int, str]]]
        ] = None,
    ) -> "ImageTransformation":
        def _format_radii(
            radii: Union[int, str, List[Union[int, str]]]
        ) -> str:
            """
            >>> _format_radii(10)
            '10'
            >>> _format_radii([10, "20%"])
            '10,20p'
            """
            radii_as_list: List[str] = (
                [str(r) for r in radii]
                if isinstance(radii, list)
                else [str(radii)]
            )
            return ",".join(self._escape_percent(r) for r in radii_as_list)

        parameters: List[str] = [_format_radii(radii)]

        if vertical_radii:
            parameters.append(_format_radii(vertical_radii))

        self.set("border_radius", parameters)
        return self

    def setfill(self, color: str) -> "ImageTransformation":
        self.set("setfill", [color])
        return self

    def zoom_objects(self, amount: int) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/resize-crop/#operation-zoom-objects
        """
        self.set("zoom_objects", [str(amount)])
        return self

    def format(self, image_format: ImageFormat) -> "ImageTransformation":
        self.set("format", [image_format])
        return self

    def rasterize(self) -> "ImageTransformation":
        self.set("rasterize", [])
        return self

    def quality(self, image_quality: ImageQuality) -> "ImageTransformation":
        self.set("quality", [image_quality])
        return self

    def progressive(self, is_progressive=True) -> "ImageTransformation":
        self.set("progressive", ["yes" if is_progressive else "no"])
        return self

    def detect_faces(self) -> "ImageTransformation":
        self.set("detect_faces", [])
        return self

    def strip_meta(self, mode: StripMetaMode) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/compression/#meta-information-control
        """
        self.set("strip_meta", [mode])
        return self

    def gif2video(
        self,
        format: Optional[Gif2VideoFormat] = None,
        quality: Optional[Gif2VideoQuality] = None,
    ) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/gif-to-video/
        """
        self.set("gif2video", [])
        if format:
            self._gif2video_format(format)
        if quality:
            self._gif2video_quality(quality)
        return self

    def _gif2video_format(
        self, format: Gif2VideoFormat
    ) -> "ImageTransformation":
        self.set("format", [format])
        return self

    def _gif2video_quality(
        self, quality: Gif2VideoQuality
    ) -> "ImageTransformation":
        self.set("quality", [quality])
        return self

    def gif2video_format(
        self, format: Gif2VideoFormat
    ) -> "ImageTransformation":
        warnings.warn(
            "The method `gif2video_format` is deprecated. "
            "Use the `format` parameter of `gif2video` instead.",
            DeprecationWarning,
        )
        return self._gif2video_format(format)

    def gif2video_quality(
        self, quality: Gif2VideoQuality
    ) -> "ImageTransformation":
        warnings.warn(
            "The method `gif2video_quality` is deprecated. "
            "Use the `quality` parameter of `gif2video` instead.",
            DeprecationWarning,
        )
        return self._gif2video_quality(quality)

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

    def _get_parameters_for_overlay_position(
        self,
        overlay_width: Optional[Union[str, int]],
        overlay_height: Optional[Union[str, int]],
        offset: Optional[OverlayOffset],
        offset_x: Optional[Union[str, int]],
        offset_y: Optional[Union[str, int]],
    ) -> List[str]:
        """
        relative_dimensions and relative_coordinates for overlays.
        https://uploadcare.com/docs/transformations/image/overlay/#overlay-image
        """

        parameters: List[str] = []
        if overlay_width is not None and overlay_height is not None:
            overlay_width = self._escape_percent(overlay_width)
            overlay_height = self._escape_percent(overlay_height)
            parameters.append(f"{overlay_width}x{overlay_height}")

        if offset:
            parameters.append(str(offset))
        elif offset_x is not None and offset_y is not None:
            offset_x = self._escape_percent(offset_x)
            offset_y = self._escape_percent(offset_y)
            parameters.append(f"{offset_x},{offset_y}")

        return parameters

    def overlay(
        self,
        uuid: str,
        overlay_width: Optional[Union[str, int]] = None,
        overlay_height: Optional[Union[str, int]] = None,
        offset: Optional[OverlayOffset] = None,
        offset_x: Optional[Union[str, int]] = None,
        offset_y: Optional[Union[str, int]] = None,
        strength: Optional[int] = None,
    ) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/overlay/#overlay-image
        """

        parameters: List[str] = [
            uuid,
            *self._get_parameters_for_overlay_position(
                overlay_width, overlay_height, offset, offset_x, offset_y
            ),
        ]

        if strength is not None:
            parameters.append(f"{strength}p")

        self.set("overlay", parameters)
        return self

    def overlay_self(
        self,
        overlay_width: Optional[Union[str, int]] = None,
        overlay_height: Optional[Union[str, int]] = None,
        offset: Optional[OverlayOffset] = None,
        offset_x: Optional[Union[str, int]] = None,
        offset_y: Optional[Union[str, int]] = None,
        strength: Optional[int] = None,
    ) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/overlay/#overlay-self
        """
        return self.overlay(
            uuid="self",
            overlay_width=overlay_width,
            overlay_height=overlay_height,
            offset=offset,
            offset_x=offset_x,
            offset_y=offset_y,
            strength=strength,
        )

    def text(
        self,
        text: str,
        overlay_width: Union[str, int],
        overlay_height: Union[str, int],
        offset: Optional[OverlayOffset] = None,
        offset_x: Optional[str] = None,
        offset_y: Optional[str] = None,
        horizontal_alignment: Optional[HorizontalTextAlignment] = None,
        vertical_alignment: Optional[VerticalTextAlignment] = None,
        font_size: Optional[int] = None,
        font_color: Optional[str] = None,
        box_mode: Optional[TextBoxMode] = None,
        box_color: Optional[str] = None,
        box_padding: Optional[int] = None,
    ) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/overlay/#overlay-text
        """

        if horizontal_alignment and vertical_alignment:
            self._text_align(
                horizontal_alignment=horizontal_alignment,
                vertical_alignment=vertical_alignment,
            )

        if font_size or font_color:
            self._font(font_size=font_size, font_color=font_color)

        if box_mode:
            self._text_box(
                box_mode=box_mode, box_color=box_color, box_padding=box_padding
            )

        self._text(
            text=text,
            overlay_width=overlay_width,
            overlay_height=overlay_height,
            offset=offset,
            offset_x=offset_x,
            offset_y=offset_y,
        )
        return self

    def _text_align(
        self,
        horizontal_alignment: HorizontalTextAlignment,
        vertical_alignment: VerticalTextAlignment,
    ) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/overlay/#text-alignment
        """
        self.set("text_align", [horizontal_alignment, vertical_alignment])
        return self

    def _font(
        self, font_size: Optional[int], font_color: Optional[str]
    ) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/overlay/#font-size-and-color
        """
        parameters: List[str] = []
        if font_size:
            parameters.append(str(font_size))
        if font_color:
            parameters.append(font_color)
        self.set("font", parameters)
        return self

    def _text_box(
        self,
        box_mode: TextBoxMode,
        box_color: Optional[str],
        box_padding: Optional[int],
    ) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/overlay/#text-background-box
        """
        parameters: List[str] = [box_mode]
        if box_color:
            parameters.append(box_color)
        if box_padding:
            parameters.append(str(box_padding))
        self.set("text_box", parameters)
        return self

    def _text(
        self,
        text: str,
        overlay_width: Union[str, int],
        overlay_height: Union[str, int],
        offset: Optional[OverlayOffset],
        offset_x: Optional[str],
        offset_y: Optional[str],
    ) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/overlay/#overlay-text
        """
        parameters: List[str] = [
            *self._get_parameters_for_overlay_position(
                overlay_width, overlay_height, offset, offset_x, offset_y
            ),
            self._escape_text(text),
        ]

        self.set("text", parameters)
        return self

    def rect(
        self,
        color: str,
        overlay_width: Union[str, int],
        overlay_height: Union[str, int],
        offset: Optional[OverlayOffset] = None,
        offset_x: Optional[str] = None,
        offset_y: Optional[str] = None,
    ) -> "ImageTransformation":
        """
        https://uploadcare.com/docs/transformations/image/overlay/#overlay-solid
        """
        parameters: List[str] = [
            color,
            *self._get_parameters_for_overlay_position(
                overlay_width, overlay_height, offset, offset_x, offset_y
            ),
        ]

        self.set("rect", parameters)
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
        path_ = path_.replace("/-/detect_faces", "/detect_faces")
        return path_
