"""Request models for file search.

https://uploadcare.com/docs/file-search/
https://uploadcare.com/docs/api/rest/file/search-files/
"""

from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Tuple

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictInt,
    model_validator,
)

from .metadata import validate_meta_key
from .tags import validate_tags


# The shortest accepted full-text term, per the API reference.
MIN_TERM_LENGTH = 4

# `sort` accepts 1-4 unique keys.
MIN_SORT_KEYS = 1
MAX_SORT_KEYS = 4


class SearchSort(str, Enum):
    """Sort keys accepted by file search. `-` prefix means descending."""

    SCORE = "score"
    SCORE_DESC = "-score"
    DATETIME_UPLOADED = "datetime_uploaded"
    DATETIME_UPLOADED_DESC = "-datetime_uploaded"
    SIZE = "size"
    SIZE_DESC = "-size"
    ORIGINAL_FILENAME = "original_filename"
    ORIGINAL_FILENAME_DESC = "-original_filename"


class SearchRequestModel(BaseModel):
    """Base for search request models.

    ``extra="forbid"`` so a misspelled key is reported instead of silently
    dropped, which matters most when a request is built from a plain dict.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    def _set_field_names(self) -> List[str]:
        """Names of the fields that carry an actual condition."""
        return [
            name for name, value in self.__dict__.items() if value is not None
        ]


class DatetimeRange(SearchRequestModel):
    gt: Optional[datetime] = None
    gte: Optional[datetime] = None
    lt: Optional[datetime] = None
    lte: Optional[datetime] = None

    @model_validator(mode="after")
    def _at_least_one_bound(self) -> "DatetimeRange":
        if not self._set_field_names():
            raise ValueError(
                "at least one of `gt`, `gte`, `lt` or `lte` is required"
            )
        return self


class SizeRange(SearchRequestModel):
    # Strict, so `gt=True` is rejected instead of silently becoming `gt=1`.
    gt: Optional[StrictInt] = Field(None, ge=0)
    gte: Optional[StrictInt] = Field(None, ge=0)
    lt: Optional[StrictInt] = Field(None, ge=0)
    lte: Optional[StrictInt] = Field(None, ge=0)

    @model_validator(mode="after")
    def _at_least_one_bound(self) -> "SizeRange":
        if not self._set_field_names():
            raise ValueError(
                "at least one of `gt`, `gte`, `lt` or `lte` is required"
            )
        return self


class SearchPhrase(SearchRequestModel):
    """Ordered full-text match. Each value must be at least 4 characters."""

    original_filename: Optional[str] = Field(None, min_length=MIN_TERM_LENGTH)
    metadata: Optional[str] = Field(None, min_length=MIN_TERM_LENGTH)
    detected_mime_type: Optional[str] = Field(None, min_length=MIN_TERM_LENGTH)

    @model_validator(mode="after")
    def _at_least_one_field(self) -> "SearchPhrase":
        if not self._set_field_names():
            raise ValueError("`phrase` requires at least one field")
        return self


class SearchExact(SearchRequestModel):
    """Exact matching. Each key takes a non-empty array of values."""

    uuid: Optional[List[str]] = Field(None, min_length=1)
    detected_mime_type: Optional[List[str]] = Field(None, min_length=1)
    original_filename: Optional[List[str]] = Field(None, min_length=1)
    # Serialized as `metadata[<key>]` by `FileSearchRequest.to_payload()`.
    metadata: Optional[Dict[str, List[str]]] = None

    @model_validator(mode="after")
    def _validate_metadata(self) -> "SearchExact":
        if self.metadata is None:
            return self

        for key, values in self.metadata.items():
            # Keeps a `[` or `]` in a key from forging a different wire key.
            validate_meta_key(key)

            if not values:
                raise ValueError(
                    f"`exact.metadata[{key}]` requires a non-empty array"
                )

        return self

    @model_validator(mode="after")
    def _at_least_one_condition(self) -> "SearchExact":
        # An empty `metadata` mapping carries no condition, so it must not
        # count towards this check: it would serialize to `"exact": {}`.
        has_condition = (
            self.uuid is not None
            or self.detected_mime_type is not None
            or self.original_filename is not None
            or bool(self.metadata)
        )

        if not has_condition:
            raise ValueError("`exact` requires at least one condition")

        return self


class TagsFilter(SearchRequestModel):
    """Tag filters.

    ``any``, ``all`` and ``none`` shadow Python builtins and keywords, so the
    attributes are suffixed with an underscore and aliased to the wire names.
    Both ``TagsFilter(any_=[...])`` and ``TagsFilter(**{"any": [...]})`` work.
    """

    any_: Optional[List[str]] = Field(None, alias="any")
    all_: Optional[List[str]] = Field(None, alias="all")
    none_: Optional[List[str]] = Field(None, alias="none")

    @model_validator(mode="after")
    def _normalize_and_check(self) -> "TagsFilter":
        for name in ("any_", "all_", "none_"):
            value = getattr(self, name)
            if value is not None:
                # Stored tags are normalized, so filters have to be too.
                # No count limit: the 50-tag ceiling applies to the tags
                # stored on a single file, not to a filter's alternatives.
                object.__setattr__(
                    self, name, validate_tags(value, max_count=None)
                )

        if not any(getattr(self, name) for name in ("any_", "all_", "none_")):
            raise ValueError(
                "`tags` requires at least one non-empty list of tags"
            )

        return self


class FileSearchRequest(SearchRequestModel):
    """A file search request.

    At least one condition is required: ``query``, ``phrase``, ``exact``,
    ``datetime_uploaded``, ``size``, ``is_image`` or ``tags``. ``fuzziness``
    and ``sort`` are modifiers and do not count as conditions.
    """

    query: Optional[str] = Field(None, min_length=MIN_TERM_LENGTH)
    phrase: Optional[SearchPhrase] = None
    exact: Optional[SearchExact] = None
    datetime_uploaded: Optional[DatetimeRange] = None
    size: Optional[SizeRange] = None
    # Strict, so `1` or `"true"` is rejected rather than silently coerced.
    is_image: Optional[StrictBool] = None
    tags: Optional[TagsFilter] = None
    fuzziness: Optional[StrictBool] = None
    sort: Optional[List[SearchSort]] = Field(
        None, min_length=MIN_SORT_KEYS, max_length=MAX_SORT_KEYS
    )

    CONDITION_FIELDS: ClassVar[Tuple[str, ...]] = (
        "query",
        "phrase",
        "exact",
        "datetime_uploaded",
        "size",
        "is_image",
        "tags",
    )

    # Fields `phrase` and `exact` have in common. `metadata` is excluded on
    # purpose: `phrase.metadata` and `exact.metadata[<key>]` are different
    # field names on the wire, so they do not collide.
    OVERLAPPING_FIELDS: ClassVar[Tuple[str, ...]] = (
        "original_filename",
        "detected_mime_type",
    )

    @model_validator(mode="after")
    def _at_least_one_condition(self) -> "FileSearchRequest":
        if all(getattr(self, name) is None for name in self.CONDITION_FIELDS):
            raise ValueError(
                "at least one of "
                + ", ".join(f"`{name}`" for name in self.CONDITION_FIELDS)
                + " is required"
            )
        return self

    @model_validator(mode="after")
    def _no_phrase_and_exact_overlap(self) -> "FileSearchRequest":
        if self.phrase is None or self.exact is None:
            return self

        for name in self.OVERLAPPING_FIELDS:
            if (
                getattr(self.phrase, name) is not None
                and getattr(self.exact, name) is not None
            ):
                raise ValueError(
                    f"`{name}` cannot appear in both `phrase` and `exact`"
                )

        return self

    @model_validator(mode="after")
    def _unique_sort_keys(self) -> "FileSearchRequest":
        if self.sort is None:
            return self

        seen = set()

        for key in self.sort:
            # Both directions of one key count as the same key.
            field = key.value.lstrip("-")

            if field in seen:
                raise ValueError(
                    f"`sort` must not contain `{field}` more than once, "
                    "in either direction"
                )

            seen.add(field)

        return self

    def has_undefined_order(self) -> bool:
        """Whether the result order of this request is undefined.

        Without ``sort``, results come back ranked by relevance. A filter-only
        request has no ``query`` or ``phrase`` to rank by, so its order is
        undefined and an explicit ``sort`` is required to page reliably.
        """
        return self.sort is None and self.query is None and self.phrase is None

    def to_payload(self) -> Dict[str, Any]:
        """Render the request as the JSON body the API expects."""
        payload = self.model_dump(
            mode="json", by_alias=True, exclude_none=True
        )

        exact = payload.get("exact")
        if exact and "metadata" in exact:
            for key, values in exact.pop("metadata").items():
                exact[f"metadata[{key}]"] = values

        tags = payload.get("tags")
        if tags:
            payload["tags"] = {
                key: value for key, value in tags.items() if value
            }

        return payload
