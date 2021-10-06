from collections import OrderedDict
from enum import Enum
from typing import List


class StrEnum(str, Enum):
    pass


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
        raise NotImplementedError

    def path(self, file_id: str) -> str:
        path_ = self._prefix(file_id)

        for (
            transformation_name,
            transformation_parameters,
        ) in self._transformation_parameters.items():
            path_ += f"-/{transformation_name}/"
            if transformation_parameters:
                path_ += f"{transformation_parameters}/"

        return path_
