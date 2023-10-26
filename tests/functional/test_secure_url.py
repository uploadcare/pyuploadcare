import pytest

from pyuploadcare import Uploadcare
from pyuploadcare.secure_url import (
    AkamaiSecureUrlBuilderWithAclToken,
    AkamaiSecureUrlBuilderWithUrlToken,
)


known_secret = (
    "73636b61519adede42191efe1e73f02a67c7b692e3765f90c250c230be095211"
)


@pytest.mark.freeze_time("2021-10-12")
def test_generate_secure_url_acl_token():
    secure_url_bulder = AkamaiSecureUrlBuilderWithAclToken(
        "cdn.yourdomain.com", known_secret
    )
    secure_url = secure_url_bulder.build(
        "52da3bfc-7cd8-4861-8b05-126fef7a6994"
    )
    assert secure_url == (
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/?token="
        "exp=1633997100~"
        "acl=/52da3bfc-7cd8-4861-8b05-126fef7a6994/~"
        "hmac=81852547d9dbd9eefd24bee2cada6eab02244b9013533bc8511511923098df72"
    )


@pytest.mark.freeze_time("2021-10-12")
def test_generate_secure_url_with_transformation_acl_token():
    secure_url_bulder = AkamaiSecureUrlBuilderWithAclToken(
        "cdn.yourdomain.com", known_secret
    )
    secure_url = secure_url_bulder.build(
        "52da3bfc-7cd8-4861-8b05-126fef7a6994/-/resize/640x/other/transformations/"
    )
    assert secure_url == (
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/"
        "-/resize/640x/other/transformations/?token="
        "exp=1633997100~"
        "acl=/52da3bfc-7cd8-4861-8b05-126fef7a6994/-/resize/640x/other/transformations/~"
        "hmac=a3ae2b3e3adfcb5d41ca753598e19d17264ac87d2b0b828ccdac5136e63f2f1a"
    )


@pytest.mark.freeze_time("2021-10-12")
def test_generate_secure_url_with_wildcard_acl_token():
    secure_url_bulder = AkamaiSecureUrlBuilderWithAclToken(
        "cdn.yourdomain.com", known_secret
    )
    secure_url = secure_url_bulder.build(
        "52da3bfc-7cd8-4861-8b05-126fef7a6994", wildcard=True
    )
    assert secure_url == (
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/?token="
        "exp=1633997100~"
        "acl=/52da3bfc-7cd8-4861-8b05-126fef7a6994/*~"
        "hmac=b2c7526a29d0588b121aa78bc2b2c9399bfb6e1cad3d95397efed722fdbc5a78"
    )


@pytest.mark.freeze_time("2021-10-12")
def test_client_generate_secure_url_acl_token():
    secure_url_bulder = AkamaiSecureUrlBuilderWithAclToken(
        "cdn.yourdomain.com", known_secret
    )

    uploadcare = Uploadcare(
        public_key="public",
        secret_key="secret",
        secure_url_builder=secure_url_bulder,
    )
    secure_url = uploadcare.generate_secure_url(
        "52da3bfc-7cd8-4861-8b05-126fef7a6994"
    )
    assert secure_url == (
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/?token="
        "exp=1633997100~"
        "acl=/52da3bfc-7cd8-4861-8b05-126fef7a6994/~"
        "hmac=81852547d9dbd9eefd24bee2cada6eab02244b9013533bc8511511923098df72"
    )


@pytest.mark.freeze_time("2021-10-12")
def test_generate_secure_url_url_token():
    secure_url_bulder = AkamaiSecureUrlBuilderWithUrlToken(
        "cdn.yourdomain.com", known_secret
    )
    secure_url = secure_url_bulder.build(
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/"
    )
    assert secure_url == (
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/?token="
        "exp=1633997100~"
        "hmac=32b696b855ddc911b366f11dcecb75789adf6211a72c1dbdf234b83f22aaa368"
    )


@pytest.mark.freeze_time("2021-10-12")
def test_client_generate_secure_url_with_wildcard_acl_token():
    secure_url_bulder = AkamaiSecureUrlBuilderWithAclToken(
        "cdn.yourdomain.com", known_secret
    )

    uploadcare = Uploadcare(
        public_key="public",
        secret_key="secret",
        secure_url_builder=secure_url_bulder,
    )
    secure_url = uploadcare.generate_secure_url(
        "52da3bfc-7cd8-4861-8b05-126fef7a6994", wildcard=True
    )
    assert secure_url == (
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/?token="
        "exp=1633997100~"
        "acl=/52da3bfc-7cd8-4861-8b05-126fef7a6994/*~"
        "hmac=b2c7526a29d0588b121aa78bc2b2c9399bfb6e1cad3d95397efed722fdbc5a78"
    )
