from enum import Enum
from typing import List, Optional, Union
from urllib.parse import quote

from typing_extensions import Self


class StrEnum(str, Enum):
    def __str__(self):
        return self.value


class BaseTransformation:
    def __init__(
        self, transformation: Optional[Union[str, "BaseTransformation"]] = None
    ):
        if isinstance(transformation, BaseTransformation):
            transformation = transformation.effects

        self._effects = []
        if transformation:
            transformation = transformation.rstrip("/")  # type: ignore
            self._effects.append(transformation)

    def set(self, transformation_name: str, parameters: List[str]) -> Self:
        effect = transformation_name
        if parameters:
            effect += "/" + "/".join(parameters)
        self._effects.append(effect)
        return self

    def _escape_percent(self, value: Union[str, int]) -> str:
        return str(value).replace("%", "p")

    def _escape_text(self, value: str) -> str:
        return quote(
            value.replace("~", "~~").replace("/", "~s").replace("\n", "~n")
        )

    def _prefix(self, file_id: str) -> str:
        return f"{file_id}/"

    def __str__(self):
        return self.effects

    @property
    def effects(self):
        effects_ = "/-/".join(self._effects)
        if effects_:
            effects_ += "/"
        return effects_

    def path(self, file_id: str) -> str:
        path_ = self._prefix(file_id)

        effects = self.effects
        if effects:
            path_ += "-/" + effects

        return path_
