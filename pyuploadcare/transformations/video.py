from typing import Optional, Union

from pyuploadcare.transformations.base import BaseTransformation, StrEnum


class VideoFormat(StrEnum):
    webm = "webm"
    ogg = "ogg"
    mp4 = "mp4"


class ResizeMode(StrEnum):
    preserve_ratio = "preserve_ratio"
    change_ratio = "change_ratio"
    scale_crop = "scale_crop"
    add_padding = "add_padding"


class Quality(StrEnum):
    normal = "normal"
    better = "better"
    best = "best"
    lighter = "lighter"
    lightest = "lightest"


class VideoTransformation(BaseTransformation):
    def format(
        self, file_format: Union[VideoFormat, str]
    ) -> "VideoTransformation":
        self.set("format", [file_format])
        return self

    def size(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        resize_mode: Optional[Union[str, ResizeMode]] = None,
    ) -> "VideoTransformation":
        parameters = [f'{width or ""}x{height or ""}']
        if resize_mode:
            parameters.append(resize_mode)
        self.set("size", parameters)
        return self

    def quality(self, file_quality: Quality) -> "VideoTransformation":
        self.set("quality", [file_quality])
        return self

    def cut(self, start_time: str, length: str) -> "VideoTransformation":
        self.set("cut", [start_time, length])
        return self

    def thumbs(self, amount: int) -> "VideoTransformation":
        self.set("thumbs", [str(amount)])
        return self

    def _prefix(self, file_id: str) -> str:
        return f"{file_id}/video/"

    def path(self, file_id: str) -> str:
        path_ = super().path(file_id)
        path_ = path_.replace("thumbs/", "thumbs~")
        return path_
