import re
from typing import Iterable, List, Optional

from pyuploadcare.exceptions import TagValidationError


TAG_PATTERN = r"[-_.A-Za-z0-9]"
TAG_MAX_LEN = 100

# Maximum amount of tags a single file can store.
MAX_TAGS_PER_FILE = 50

LENGTH = f"{{1,{TAG_MAX_LEN}}}"
# `\Z` rather than `$`, which would also match just before a trailing newline
# and let `"cat\n"` through.
tag_matcher = re.compile(rf"^{TAG_PATTERN}{LENGTH}\Z")


def normalize_tag(tag: str) -> str:
    """Apply the same normalization the REST API applies to a single tag."""
    return tag.strip().lower()


def normalize_tags(tags: Iterable[str]) -> List[str]:
    """Normalize a collection of tags the way the REST API does.

    Tags are lowercased and stripped, empty ones are discarded and duplicates
    are removed keeping the first occurrence, so the original order of the
    remaining tags is preserved.
    """
    if isinstance(tags, str):
        raise TagValidationError(
            "Tags must be a collection of strings, not a single string. "
            f"Got [{tags}], did you mean [{tags!r}.split(',')]?"
        )

    normalized: List[str] = []
    seen = set()

    for tag in tags:
        if not isinstance(tag, str):
            raise TagValidationError(
                f"Tag [{tag!s}] must be string not a {type(tag)}"
            )

        normalized_tag = normalize_tag(tag)

        if not normalized_tag or normalized_tag in seen:
            continue

        seen.add(normalized_tag)
        normalized.append(normalized_tag)

    return normalized


def validate_tag(tag: str) -> None:
    if not isinstance(tag, str):
        raise TagValidationError(
            f"Tag [{tag!s}] must be string not a {type(tag)}"
        )

    if not tag_matcher.match(tag):
        raise TagValidationError(
            f"Tag [{tag}] is not valid. Tags are limited to {TAG_MAX_LEN} "
            "characters and may contain Latin letters, digits, `-`, `_` "
            "and `.` only"
        )


def validate_tags(
    tags: Iterable[str],
    max_count: Optional[int] = MAX_TAGS_PER_FILE,
) -> List[str]:
    """Normalize and validate tags, returning the normalized list.

    Tags are normalized before validation, so values the API would accept
    after its own normalization (e.g. ``" Cat "``) are not rejected here.

    Args:
        - tags: collection of tags to validate.
        - max_count: maximum amount of tags allowed after normalization.
          ``MAX_TAGS_PER_FILE`` is a limit on tags stored on a single file;
          pass ``None`` where no such limit applies, e.g. for search filters.
    """
    tags = tags if isinstance(tags, str) else list(tags)
    normalized = normalize_tags(tags)

    if tags and not normalized:
        raise TagValidationError(
            "All given tags are empty after normalization. To clear the "
            "tags of a file, pass an empty collection instead"
        )

    for tag in normalized:
        validate_tag(tag)

    if max_count is not None and len(normalized) > max_count:
        raise TagValidationError(
            f"Too many tags: {len(normalized)}, maximum is {max_count}"
        )

    return normalized
