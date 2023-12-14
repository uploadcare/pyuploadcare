from unittest import mock

import httpx
import pytest

import pyuploadcare.api.client


@pytest.fixture
def test_client():
    yield pyuploadcare.api.client.Client()


@mock.patch("pyuploadcare.api.client.PY37_PLUS", True)
def test_deprecated_argument_for_PY37_if_allow_is_set(test_client, caplog):
    """
    Test that for installed Python 3.7.* or newer
    using together `allow_redirects` and `follow_redirects`
    will cause warning about argument deprecation
    """
    real_PY36 = pyuploadcare.api.client.PY36

    with mock.patch("pyuploadcare.api.client.PY36", False):
        if real_PY36:
            # allow_redirects converted into follow_redirects
            # but there is an old version of httpx on real PY36 environment
            with pytest.raises(
                TypeError,
                match="got an unexpected keyword argument 'follow_redirects'",
            ):
                test_client.request(
                    method="any",
                    url="yandex.ru",
                    allow_redirects=True,
                )
        else:
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


@mock.patch("pyuploadcare.api.client.PY37_PLUS", False)
def test_deprecated_argument_is_OK_for_PY36_if_allow_is_set(test_client):
    real_PY36 = pyuploadcare.api.client.PY36

    with mock.patch("pyuploadcare.api.client.PY36", True):
        if real_PY36:
            """`allow_redirects` is valid argument"""
            with pytest.raises(httpx.UnsupportedProtocol):
                test_client.request(
                    method="any",
                    url="yandex.ru",
                    allow_redirects=True,
                )

        else:
            """
            `allow_redirects` is not valid argument for
            environment with bumped httpx version (Python 3.7 and newer)
            """
            with pytest.raises(TypeError, match="unexpected keyword argument"):
                test_client.request(
                    method="any",
                    url="yandex.ru",
                    allow_redirects=True,
                )
