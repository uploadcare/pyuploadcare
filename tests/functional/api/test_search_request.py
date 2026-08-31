"""Validation and serialization of file search request models."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from pyuploadcare.api.search_entities import (
    MAX_SORT_KEYS,
    DatetimeRange,
    FileSearchRequest,
    SearchExact,
    SearchPhrase,
    SearchSort,
    SizeRange,
    TagsFilter,
)


# --- at least one condition -------------------------------------------------


def test_request_requires_at_least_one_condition():
    with pytest.raises(ValidationError):
        FileSearchRequest()


def test_modifiers_alone_are_not_a_condition():
    """`fuzziness` and `sort` are modifiers, not conditions."""
    with pytest.raises(ValidationError):
        FileSearchRequest(fuzziness=True, sort=[SearchSort.SCORE])


@pytest.mark.parametrize(
    "condition",
    [
        {"query": "sunset"},
        {"phrase": SearchPhrase(original_filename="sunset")},
        {"exact": SearchExact(original_filename=["sunset.jpg"])},
        {"datetime_uploaded": DatetimeRange(gt=datetime(2024, 1, 1))},
        {"size": SizeRange(gt=1000)},
        {"is_image": True},
        {"is_image": False},
        {"tags": TagsFilter(any_=["cat"])},
    ],
)
def test_any_single_condition_is_enough(condition):
    FileSearchRequest(**condition)


# --- query and phrase -------------------------------------------------------


def test_query_requires_four_characters():
    with pytest.raises(ValidationError):
        FileSearchRequest(query="abc")


def test_query_accepts_four_characters():
    assert FileSearchRequest(query="abcd").query == "abcd"


def test_phrase_requires_at_least_one_field():
    with pytest.raises(ValidationError):
        SearchPhrase()


@pytest.mark.parametrize(
    "field", ["original_filename", "metadata", "detected_mime_type"]
)
def test_phrase_values_require_four_characters(field):
    with pytest.raises(ValidationError):
        SearchPhrase(**{field: "abc"})


# --- exact ------------------------------------------------------------------


def test_exact_requires_at_least_one_condition():
    with pytest.raises(ValidationError):
        SearchExact()


def test_exact_rejects_empty_metadata_mapping():
    """It would otherwise serialize to an empty `"exact": {}`."""
    with pytest.raises(ValidationError):
        SearchExact(metadata={})


@pytest.mark.parametrize(
    "field", ["uuid", "original_filename", "detected_mime_type"]
)
def test_exact_rejects_empty_arrays(field):
    with pytest.raises(ValidationError):
        SearchExact(**{field: []})


def test_exact_rejects_empty_metadata_value_array():
    with pytest.raises(ValidationError):
        SearchExact(metadata={"color": []})


@pytest.mark.parametrize("key", ["bad]key[", "album\n"])
def test_exact_rejects_invalid_metadata_key(key):
    """A `[`, `]` or newline in a key could forge a different wire key."""
    with pytest.raises(ValidationError) as excinfo:
        SearchExact(metadata={key: ["red"]})

    assert "is not valid" in str(excinfo.value)


# --- phrase / exact overlap -------------------------------------------------


@pytest.mark.parametrize("field", ["original_filename", "detected_mime_type"])
def test_field_cannot_be_in_both_phrase_and_exact(field):
    with pytest.raises(ValidationError):
        FileSearchRequest(
            phrase=SearchPhrase(**{field: "sunset"}),
            exact=SearchExact(**{field: ["sunset"]}),
        )


def test_different_fields_in_phrase_and_exact_are_allowed():
    FileSearchRequest(
        phrase=SearchPhrase(original_filename="sunset"),
        exact=SearchExact(uuid=["a55d6b25-d03c-4038-9838-6e06bb7df598"]),
    )


def test_metadata_in_both_phrase_and_exact_is_allowed():
    """`phrase.metadata` and `exact.metadata[key]` are distinct wire keys."""
    FileSearchRequest(
        phrase=SearchPhrase(metadata="sunset"),
        exact=SearchExact(metadata={"color": ["red"]}),
    )


# --- sort -------------------------------------------------------------------


def test_sort_rejects_empty_list():
    with pytest.raises(ValidationError):
        FileSearchRequest(query="sunset", sort=[])


def test_sort_rejects_too_many_keys():
    keys = [
        SearchSort.SCORE,
        SearchSort.SIZE,
        SearchSort.DATETIME_UPLOADED,
        SearchSort.ORIGINAL_FILENAME,
        SearchSort.SCORE_DESC,
    ]
    assert len(keys) == MAX_SORT_KEYS + 1

    with pytest.raises(ValidationError):
        FileSearchRequest(query="sunset", sort=keys)


def test_sort_rejects_duplicate_keys():
    with pytest.raises(ValidationError):
        FileSearchRequest(
            query="sunset", sort=[SearchSort.SIZE, SearchSort.SIZE]
        )


def test_sort_rejects_both_directions_of_the_same_key():
    with pytest.raises(ValidationError):
        FileSearchRequest(
            query="sunset", sort=[SearchSort.SCORE, SearchSort.SCORE_DESC]
        )


def test_sort_rejects_unknown_key():
    with pytest.raises(ValidationError):
        FileSearchRequest(query="sunset", sort=["relevance"])


def test_sort_accepts_plain_strings():
    request = FileSearchRequest(query="sunset", sort=["-score", "size"])
    assert request.sort == [SearchSort.SCORE_DESC, SearchSort.SIZE]


# --- tags -------------------------------------------------------------------


def test_tags_filter_requires_at_least_one_list():
    with pytest.raises(ValidationError):
        TagsFilter()


def test_tags_filter_rejects_only_empty_lists():
    with pytest.raises(ValidationError):
        TagsFilter(any_=[], all_=[])


def test_tags_filter_accepts_wire_names():
    tags = TagsFilter(**{"any": ["cat"], "none": ["dog"]})
    assert tags.any_ == ["cat"]
    assert tags.none_ == ["dog"]


def test_tags_filter_normalizes_tags():
    assert TagsFilter(any_=[" Cat ", "CAT", "dog"]).any_ == ["cat", "dog"]


def test_tags_filter_rejects_invalid_tags():
    with pytest.raises(ValidationError) as excinfo:
        TagsFilter(any_=["not valid"])

    assert "is not valid" in str(excinfo.value)


def test_tags_filter_has_no_count_limit():
    """The 50-tag limit is per stored file, not per filter."""
    tags = [f"tag{index}" for index in range(60)]
    assert TagsFilter(any_=tags).any_ == tags


# --- ranges -----------------------------------------------------------------


@pytest.mark.parametrize("model", [DatetimeRange, SizeRange])
def test_range_requires_at_least_one_bound(model):
    with pytest.raises(ValidationError):
        model()


def test_size_range_rejects_negative_values():
    with pytest.raises(ValidationError):
        SizeRange(gt=-1)


# --- strict scalars ---------------------------------------------------------


@pytest.mark.parametrize("value", [True, False, "1000", 1000.5])
def test_size_range_rejects_non_integers(value):
    """`gt=True` must not silently become `gt=1`."""
    with pytest.raises(ValidationError):
        SizeRange(gt=value)


def test_size_range_accepts_integers():
    size = SizeRange(gt=0, lte=1000)
    assert (size.gt, size.lte) == (0, 1000)


@pytest.mark.parametrize("field", ["is_image", "fuzziness"])
@pytest.mark.parametrize("value", [1, 0, "true", "false", "yes"])
def test_boolean_fields_reject_non_booleans(field, value):
    with pytest.raises(ValidationError):
        FileSearchRequest(query="sunset", **{field: value})


@pytest.mark.parametrize("field", ["is_image", "fuzziness"])
@pytest.mark.parametrize("value", [True, False])
def test_boolean_fields_accept_booleans(field, value):
    request = FileSearchRequest(query="sunset", **{field: value})
    assert getattr(request, field) is value


# --- extra fields -----------------------------------------------------------


def test_unknown_field_is_rejected():
    """A typo must be reported, not silently dropped."""
    with pytest.raises(ValidationError):
        FileSearchRequest.model_validate({"querry": "sunset"})


def test_unknown_nested_field_is_rejected():
    with pytest.raises(ValidationError):
        FileSearchRequest.model_validate(
            {"exact": {"filename": ["sunset.jpg"]}}
        )


def test_wire_shape_for_exact_metadata_is_rejected():
    """Dicts use the SDK shape, not the `metadata[key]` wire shape."""
    with pytest.raises(ValidationError):
        FileSearchRequest.model_validate(
            {"exact": {"metadata[color]": ["red"]}}
        )


# --- to_payload -------------------------------------------------------------


def test_payload_lifts_exact_metadata_into_bracketed_keys():
    request = FileSearchRequest(
        exact=SearchExact(metadata={"color": ["red"], "size": ["xl"]})
    )

    assert request.to_payload() == {
        "exact": {"metadata[color]": ["red"], "metadata[size]": ["xl"]}
    }


def test_payload_keeps_other_exact_fields_alongside_metadata():
    request = FileSearchRequest(
        exact=SearchExact(
            original_filename=["sunset.jpg"], metadata={"color": ["red"]}
        )
    )

    assert request.to_payload() == {
        "exact": {
            "original_filename": ["sunset.jpg"],
            "metadata[color]": ["red"],
        }
    }


def test_payload_renders_datetime_as_iso8601():
    request = FileSearchRequest(
        datetime_uploaded=DatetimeRange(
            gte=datetime(2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
        )
    )

    payload = request.to_payload()
    assert payload["datetime_uploaded"]["gte"].startswith(
        "2024-01-02T03:04:05"
    )


def test_payload_renders_sort_keys_as_values():
    request = FileSearchRequest(
        query="sunset", sort=[SearchSort.SCORE_DESC, SearchSort.SIZE]
    )

    assert request.to_payload()["sort"] == ["-score", "size"]


def test_payload_uses_tag_filter_wire_names():
    request = FileSearchRequest(
        tags=TagsFilter(any_=["cat"], all_=["pet"], none_=["dog"])
    )

    assert request.to_payload()["tags"] == {
        "any": ["cat"],
        "all": ["pet"],
        "none": ["dog"],
    }


def test_payload_drops_empty_tag_lists():
    request = FileSearchRequest(tags=TagsFilter(any_=["cat"], none_=[]))

    assert request.to_payload()["tags"] == {"any": ["cat"]}


def test_payload_omits_unset_fields():
    request = FileSearchRequest(query="sunset")

    assert request.to_payload() == {"query": "sunset"}


def test_payload_keeps_false_values():
    """`exclude_none` must not drop `is_image=False` or `fuzziness=False`."""
    request = FileSearchRequest(is_image=False, fuzziness=False)

    assert request.to_payload() == {"is_image": False, "fuzziness": False}
