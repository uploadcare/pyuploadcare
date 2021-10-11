from enum import Enum
from typing import List


class StrEnum(str, Enum):
    def __str__(self):
        return self.value


class BaseTransformation:
    def __init__(
        self,
    ):
        self._effects = []

    def set(
        self, transformation_name: str, parameters: List[str]
    ) -> "BaseTransformation":
        effect = transformation_name
        if parameters:
            effect += "/" + "/".join(parameters)
        self._effects.append(effect)
        return self

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
