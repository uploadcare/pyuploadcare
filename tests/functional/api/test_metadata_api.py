import pytest


@pytest.mark.vcr
def test_get_all_metadata(uploadcare):
    stored_metadata = uploadcare.metadata_api.get_all_metadata(
        "a55d6b25-d03c-4038-9838-6e06bb7df598"
    )

    assert stored_metadata == {
        "first_key": "first_value",
        "second_key": "any_others",
    }


@pytest.mark.vcr
def test_create_key_and_delete(uploadcare, vcr):
    base_expected_metadata = {
        "first_key": "first_value",
        "second_key": "any_others",
    }
    new_key, new_value = "-:45az_", "any string up to 512"

    created_value = uploadcare.metadata_api.update_or_create_key(
        "a55d6b25-d03c-4038-9838-6e06bb7df598", new_key, new_value
    )

    assert created_value == new_value

    uploadcare.metadata_api.delete_key(
        "a55d6b25-d03c-4038-9838-6e06bb7df598", new_key
    )

    with vcr.use_cassette("test_get_all_metadata"):
        stored_metadata = uploadcare.metadata_api.get_all_metadata(
            "a55d6b25-d03c-4038-9838-6e06bb7df598"
        )
        assert stored_metadata == base_expected_metadata


@pytest.mark.vcr
def test_get_metadata_value_for_specific_key(uploadcare):
    value_for_second_key = uploadcare.metadata_api.get_key(
        "a55d6b25-d03c-4038-9838-6e06bb7df598", "second_key"
    )
    assert value_for_second_key == "any_others"
