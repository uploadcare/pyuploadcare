from collections import OrderedDict
from enum import Enum
from typing import List


class StrEnum(str, Enum):
    def __str__(self):
        return self.value


class BaseTransformation:
    def __init__(
        self,
    ):
        self._transformation_parameters = OrderedDict()

    def unset(self, transformation_name: str) -> "BaseTransformation":
        """Remove transformations"""
        if transformation_name in self._transformation_parameters:
            self._transformation_parameters.pop(transformation_name)
        return self

    def set(
        self, transformation_name: str, parameters: List[str]
    ) -> "BaseTransformation":
        self._transformation_parameters[transformation_name] = "/".join(
            parameters
        )
        return self

    def _prefix(self, file_id: str) -> str:
        return f"{file_id}/"

    def __str__(self):
        return self.effects

    @property
    def effects(self):
        effects_ = ""
        for (
            transformation_name,
            transformation_parameters,
        ) in self._transformation_parameters.items():
            effects_ += f"-/{transformation_name}/"
            if transformation_parameters:
                effects_ += f"{transformation_parameters}/"
        return effects_.lstrip("-/")

    def path(self, file_id: str) -> str:
        path_ = self._prefix(file_id)

        effects = self.effects
        if effects:
            path_ += "-/" + effects

        return path_
