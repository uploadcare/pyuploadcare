import httpx2 as httpx
import pytest

import pyuploadcare.api.client


@pytest.fixture
def test_client():
    yield pyuploadcare.api.client.Client()


def test_deprecated_argument_if_allow_is_set(test_client, caplog):
    """
    Test that `allow_redirects` is converted into `follow_redirects`
    and causes a warning about argument deprecation.
    """
    with pytest.raises(httpx.UnsupportedProtocol):
        test_client.request(
            method="any",
            url="yandex.ru",
            allow_redirects=True,
        )

    # `allow_redirects` is valid argument for a while but we aware about deprecation
    assert caplog.records[0].message.startswith(
        "Argument `allow_redirects` is deprecated"
    )


def test_deprecated_both_arguments_ar_not_allowed(test_client):
    with pytest.raises(ValueError):
        # both arguments are not allowed to be set together
        test_client.request(
            method="any",
            url="yandex.ru",
            allow_redirects=True,
            follow_redirects=True,
        )
