from datetime import datetime
from typing import Optional, Union

import dateutil.parser


def coerce_to_optional_datetime(
    value: Optional[Union[str, datetime]]
) -> Optional[datetime]:
    if not value:
        return None
    elif isinstance(value, datetime):
        return value
    elif isinstance(value, str):
        return dateutil.parser.parse(value)
    else:
        raise ValueError(f"Failed to coerce {value} into datetime")


def max_for_optional_datetimes(
    left: Optional[datetime], right: Optional[datetime]
) -> Optional[datetime]:
    if not left and not right:
        return None

    if not right:
        return left
    elif not left:
        return right
    else:
        return max(left, right)
