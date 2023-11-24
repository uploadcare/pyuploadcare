from urllib.error import HTTPError
from urllib.request import urlopen

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
def test_get_acl_token():
    secure_url_bulder = AkamaiSecureUrlBuilderWithAclToken(
        "cdn.yourdomain.com", known_secret
    )
    token = secure_url_bulder.get_token("52da3bfc-7cd8-4861-8b05-126fef7a6994")
    assert token == (
        "exp=1633997100~"
        "acl=/52da3bfc-7cd8-4861-8b05-126fef7a6994/~"
        "hmac=81852547d9dbd9eefd24bee2cada6eab02244b9013533bc8511511923098df72"
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
def test_client_generate_secure_url_token_acl_token():
    secure_url_bulder = AkamaiSecureUrlBuilderWithAclToken(
        "cdn.yourdomain.com", known_secret
    )

    uploadcare = Uploadcare(
        public_key="public",
        secret_key="secret",
        secure_url_builder=secure_url_bulder,
    )
    secure_url = uploadcare.generate_secure_url_token(
        "52da3bfc-7cd8-4861-8b05-126fef7a6994"
    )
    assert secure_url == (
        "exp=1633997100~"
        "acl=/52da3bfc-7cd8-4861-8b05-126fef7a6994/~"
        "hmac=81852547d9dbd9eefd24bee2cada6eab02244b9013533bc8511511923098df72"
    )


@pytest.mark.freeze_time("2021-10-12")
def test_get_url_token():
    secure_url_bulder = AkamaiSecureUrlBuilderWithUrlToken(
        "cdn.yourdomain.com", known_secret
    )
    token = secure_url_bulder.get_token(
        "https://cdn.yourdomain.com/52da3bfc-7cd8-4861-8b05-126fef7a6994/"
    )
    assert token == (
        "exp=1633997100~"
        "hmac=25c485fd7f85c19704013673c80d2a86df1b4241fb44cdfa7b7762cb27ef3f57"
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
        "hmac=25c485fd7f85c19704013673c80d2a86df1b4241fb44cdfa7b7762cb27ef3f57"
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


@pytest.fixture
def uploadcare_with_acl_token():
    secure_url_builder = AkamaiSecureUrlBuilderWithAclToken(
        cdn_url="sectest.ucarecdn.com",
        secret_key=known_secret,
        window=60 * 60 * 24 * 365 * 10,
    )

    uploadcare = Uploadcare(
        public_key="public",
        secret_key="secret",
        secure_url_builder=secure_url_builder,
    )
    return uploadcare


@pytest.mark.freeze_time("2023-11-22")
@pytest.mark.vcr
def test_acl_token_bare_uuid(uploadcare_with_acl_token: Uploadcare):
    secure_url = uploadcare_with_acl_token.generate_secure_url(
        "1bd27101-6f40-460a-9358-d44c282e9d16"
    )
    assert urlopen(secure_url).status == 200


@pytest.mark.freeze_time("2023-11-22")
@pytest.mark.vcr
def test_acl_token_uuid_with_transformations(
    uploadcare_with_acl_token: Uploadcare,
):
    secure_url = uploadcare_with_acl_token.generate_secure_url(
        "1bd27101-6f40-460a-9358-d44c282e9d16/-/crop/10x10/20,20/"
    )
    with pytest.raises(HTTPError) as e:
        urlopen(secure_url)
    assert "are not images" in e.value.read().decode()


@pytest.mark.freeze_time("2023-11-22")
@pytest.mark.vcr
def test_acl_token_wildcard_uuid(uploadcare_with_acl_token: Uploadcare):
    secure_url = uploadcare_with_acl_token.generate_secure_url(
        "1bd27101-6f40-460a-9358-d44c282e9d16", wildcard=True
    )
    assert urlopen(secure_url).status == 200

    secure_url = uploadcare_with_acl_token.generate_secure_url(
        "1bd27101-6f40-460a-9358-d44c282e9d16", wildcard=True
    )
    secure_url = secure_url.replace("/?token=", "/hello.txt?token=")
    assert "hello.txt" in secure_url
    assert urlopen(secure_url).status == 200


@pytest.mark.freeze_time("2023-11-22")
@pytest.mark.vcr
def test_acl_token_wildcard_uuid_with_transformations(
    uploadcare_with_acl_token: Uploadcare,
):
    secure_url = uploadcare_with_acl_token.generate_secure_url(
        "1bd27101-6f40-460a-9358-d44c282e9d16/-/preview/400x400/",
        wildcard=True,
    )
    with pytest.raises(HTTPError) as e:
        urlopen(secure_url)
    assert "are not images" in e.value.read().decode()

    secure_url = uploadcare_with_acl_token.generate_secure_url(
        "1bd27101-6f40-460a-9358-d44c282e9d16/-/preview/400x400/",
        wildcard=True,
    )
    secure_url = secure_url.replace("/?token=", "/hello.txt?token=")
    assert "hello.txt" in secure_url
    with pytest.raises(HTTPError) as e:
        urlopen(secure_url)
    assert "are not images" in e.value.read().decode()


@pytest.mark.freeze_time("2023-11-22")
@pytest.mark.vcr
def test_acl_token_basic_url(uploadcare_with_acl_token: Uploadcare):
    secure_url = uploadcare_with_acl_token.generate_secure_url(
        "https://sectest.ucarecdn.com/1bd27101-6f40-460a-9358-d44c282e9d16/"
    )
    assert urlopen(secure_url).status == 200


@pytest.mark.freeze_time("2023-11-22")
@pytest.mark.vcr
def test_acl_token_group_url(uploadcare_with_acl_token: Uploadcare):
    secure_url = uploadcare_with_acl_token.generate_secure_url(
        "https://sectest.ucarecdn.com/3b278cee-47bd-4276-8d7d-9cde5902b18c~1/nth/0/"
    )
    assert urlopen(secure_url).status == 200


@pytest.fixture
def uploadcare_with_url_token():
    secure_url_builder = AkamaiSecureUrlBuilderWithUrlToken(
        cdn_url="sectest.ucarecdn.com",
        secret_key=known_secret,
        window=60 * 60 * 24 * 365 * 10,
    )

    uploadcare = Uploadcare(
        public_key="public",
        secret_key="secret",
        secure_url_builder=secure_url_builder,
    )
    return uploadcare


@pytest.mark.freeze_time("2023-11-22")
@pytest.mark.vcr
def test_url_token_basic_url(uploadcare_with_url_token: Uploadcare):
    secure_url = uploadcare_with_url_token.generate_secure_url(
        "https://sectest.ucarecdn.com/1bd27101-6f40-460a-9358-d44c282e9d16/"
    )
    assert urlopen(secure_url).status == 200


@pytest.mark.freeze_time("2023-11-22")
@pytest.mark.vcr
def test_url_token_uuid_with_transformations(
    uploadcare_with_url_token: Uploadcare,
):
    secure_url = uploadcare_with_url_token.generate_secure_url(
        "1bd27101-6f40-460a-9358-d44c282e9d16/-/crop/10x10/20,20/"
    )
    with pytest.raises(HTTPError) as e:
        urlopen(secure_url)
    assert "are not images" in e.value.read().decode()


@pytest.mark.freeze_time("2023-11-22")
@pytest.mark.vcr
def test_url_token_group_url(uploadcare_with_url_token: Uploadcare):
    secure_url = uploadcare_with_url_token.generate_secure_url(
        "https://sectest.ucarecdn.com/3b278cee-47bd-4276-8d7d-9cde5902b18c~1/nth/0/"
    )
    assert urlopen(secure_url).status == 200
