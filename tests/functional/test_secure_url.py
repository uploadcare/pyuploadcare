import pytest

from pyuploadcare.secure_url import SecureUrlBuilder


@pytest.mark.freeze_time("2021-10-12")
def test_generate_secure_url():
    secure_url_bulder = SecureUrlBuilder("cdn.yourdomain.com", "secret")
    secure_url = secure_url_bulder.generate_secure_url(
        "52da3bfc-7cd8-4861-8b05-126fef7a6994"
    )
    assert secure_url == (
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/?token="
        "exp=1633997100~"
        "acl=/52da3bfc-7cd8-4861-8b05-126fef7a6994/~"
        "hmac=a33cfc66c3e3592e712cdd1f82bd79d51df93b06"
    )


@pytest.mark.freeze_time("2021-10-12")
def test_generate_secure_url_with_transformation():
    secure_url_bulder = SecureUrlBuilder("cdn.yourdomain.com", "secret")
    secure_url = secure_url_bulder.generate_secure_url(
        "52da3bfc-7cd8-4861-8b05-126fef7a6994/-/resize/640x/other/transformations/"
    )
    assert secure_url == (
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/"
        "-/resize/640x/other/transformations/?token="
        "exp=1633997100~"
        "acl=/52da3bfc-7cd8-4861-8b05-126fef7a6994/-/resize/640x/other/transformations/~"
        "hmac=24d11299339bdf9dcba26c7a5603c7ca63503fda"
    )


@pytest.mark.freeze_time("2021-10-12")
def test_generate_secure_url_custom_acl():
    secure_url_bulder = SecureUrlBuilder("cdn.yourdomain.com", "secret")
    secure_url = secure_url_bulder.generate_secure_url(
        "52da3bfc-7cd8-4861-8b05-126fef7a6994", acl="/*/"
    )
    assert secure_url == (
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/?token="
        "exp=1633997100~"
        "acl=/*/~"
        "hmac=722f6beb935d35b62427329dd591049afb498f77"
    )
