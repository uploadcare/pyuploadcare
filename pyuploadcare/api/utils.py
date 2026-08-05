from typing import Any, Optional

from pyuploadcare.exceptions import InvalidParamError


def require_optional_int(name: str, value: Any) -> None:
    """Reject a value that is neither ``None`` nor a real int.

    Type annotations are not enforced at runtime, and ``bool`` is a subclass
    of ``int``, so ``limit=True`` would otherwise reach the query string
    verbatim as ``limit=True``.
    """
    if value is None:
        return

    if isinstance(value, bool) or not isinstance(value, int):
        raise InvalidParamError(
            f"`{name}` must be an int, got {type(value).__name__}"
        )


def require_range(
    name: str,
    value: Optional[int],
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> None:
    """Reject an out-of-range value. ``None`` always passes."""
    if value is None:
        return

    if minimum is not None and value < minimum:
        raise InvalidParamError(f"`{name}` must be >= {minimum}, got {value}")

    if maximum is not None and value > maximum:
        raise InvalidParamError(f"`{name}` must be <= {maximum}, got {value}")


def flatten_dict(simple_mapping, attribute_base="metadata") -> dict:
    """
    Straightforward way to use nested dict for multipart/form-data
    """
    result = dict()
    for key, val in simple_mapping.items():
        if not isinstance(val, str):
            raise TypeError(
                f"Expect 'string' for dict to be flatten, got {type(val)} instead"
            )
        result[f"{attribute_base}[{key}]"] = val

    return result
