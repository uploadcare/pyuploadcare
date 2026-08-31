import pytest

from pyuploadcare.api.tags import (
    MAX_TAGS_PER_FILE,
    TAG_MAX_LEN,
    normalize_tag,
    normalize_tags,
    validate_tag,
    validate_tags,
)
from pyuploadcare.exceptions import TagValidationError


def test_normalize_tag_lowercases_and_strips():
    assert normalize_tag("  Cat  ") == "cat"


def test_normalize_tags_lowercases():
    assert normalize_tags(["cat", "Cat", "CAT"]) == ["cat"]


def test_normalize_tags_strips_whitespace():
    assert normalize_tags([" cat ", "\tanimal\n"]) == ["cat", "animal"]


def test_normalize_tags_discards_empty_strings():
    assert normalize_tags(["cat", "", "   ", "animal"]) == ["cat", "animal"]


def test_normalize_tags_preserves_first_seen_order():
    assert normalize_tags(["dog", "cat", "Dog", "animal"]) == [
        "dog",
        "cat",
        "animal",
    ]


def test_normalize_tags_accepts_any_iterable():
    assert normalize_tags(("cat", "animal")) == ["cat", "animal"]
    assert normalize_tags(tag for tag in ["cat", "animal"]) == [
        "cat",
        "animal",
    ]


def test_normalize_tags_rejects_a_bare_string():
    with pytest.raises(TagValidationError):
        normalize_tags("cat,animal")


def test_normalize_tags_rejects_non_string_items():
    with pytest.raises(TagValidationError):
        normalize_tags(["cat", 42])  # type: ignore[list-item]


@pytest.mark.parametrize(
    "tag", ["cat", "animal-2", "under_score", "with.dot", "MiXeD", "0"]
)
def test_validate_tag_accepts_allowed_characters(tag):
    validate_tag(tag)


@pytest.mark.parametrize(
    "tag",
    [
        "with space",
        "with+plus",
        "with@at",
        "with/slash",
        "with,comma",
        "кот",
        "with:colon",
        "",
        "cat\n",
        "\ncat",
        "cat\t",
    ],
)
def test_validate_tag_rejects_disallowed_characters(tag):
    with pytest.raises(TagValidationError):
        validate_tag(tag)


def test_validate_tag_rejects_non_string():
    with pytest.raises(TagValidationError):
        validate_tag(42)  # type: ignore[arg-type]


def test_validate_tags_rejects_tags_that_normalize_to_nothing():
    """`set_tags(["  "])` must not silently clear every tag on the file."""
    with pytest.raises(TagValidationError, match="empty after normalization"):
        validate_tags(["  "])

    with pytest.raises(TagValidationError, match="empty after normalization"):
        validate_tags(["", "\t"])


def test_validate_tags_accepts_an_empty_collection():
    """An empty collection is the documented way to clear tags."""
    assert validate_tags([]) == []
    assert validate_tags(()) == []


def test_validate_tags_still_drops_empty_items_among_valid_ones():
    assert validate_tags(["cat", "  "]) == ["cat"]


def test_validate_tags_accepts_max_length_tag():
    tag = "a" * TAG_MAX_LEN
    assert validate_tags([tag]) == [tag]


def test_validate_tags_rejects_too_long_tag():
    with pytest.raises(TagValidationError):
        validate_tags(["a" * (TAG_MAX_LEN + 1)])


def test_validate_tags_returns_normalized_list():
    assert validate_tags([" Cat ", "CAT", "animal"]) == ["cat", "animal"]


def test_validate_tags_accepts_max_amount_of_tags():
    tags = [f"tag{index}" for index in range(MAX_TAGS_PER_FILE)]
    assert validate_tags(tags) == tags


def test_validate_tags_rejects_too_many_tags():
    tags = [f"tag{index}" for index in range(MAX_TAGS_PER_FILE + 1)]
    with pytest.raises(TagValidationError):
        validate_tags(tags)


def test_validate_tags_counts_tags_after_deduplication():
    """51 tags collapsing into 50 unique ones is within the limit."""
    tags = [f"tag{index}" for index in range(MAX_TAGS_PER_FILE)]
    assert validate_tags([*tags, "TAG0"]) == tags


def test_validate_tags_without_max_count_allows_more_tags():
    tags = [f"tag{index}" for index in range(MAX_TAGS_PER_FILE + 10)]
    assert validate_tags(tags, max_count=None) == tags


def test_validate_tags_accepts_empty_collection():
    assert validate_tags([]) == []
