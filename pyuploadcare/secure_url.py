import binascii
import hashlib
import hmac
import time
import warnings
from abc import ABC, abstractmethod
from typing import Optional


class BaseSecureUrlBuilder(ABC):
    @abstractmethod
    def build(self, uuid: str, wildcard: bool = False) -> str:
        raise NotImplementedError


class BaseAkamaiSecureUrlBuilder(BaseSecureUrlBuilder):
    """Akamai secure url builder.

    See https://uploadcare.com/docs/security/secure_delivery/
    for more details.
    """

    field_delimeter = "~"

    def __init__(
        self,
        cdn_url: str,
        secret_key: str,
        window: int = 300,
        hash_algo=hashlib.sha256,
    ):
        self.secret_key = secret_key
        self.cdn_url = cdn_url
        self.window = window
        self.hash_algo = hash_algo

    def _build_expire_time(self) -> int:
        return int(time.time()) + self.window

    def _build_signature(
        self, expire: int, acl: Optional[str] = None, url: Optional[str] = None
    ) -> str:
        assert bool(acl) != bool(url)

        hash_source = [f"exp={expire}", f"acl={acl}" if acl else f"url={url}"]

        signature = hmac.new(
            binascii.a2b_hex(self.secret_key.encode()),
            self.field_delimeter.join(hash_source).encode(),
            self.hash_algo,
        ).hexdigest()

        return signature


class AkamaiSecureUrlBuilderWithAclToken(BaseAkamaiSecureUrlBuilder):
    template = "https://{cdn}/{uuid}/?token={token}"

    def build(self, uuid: str, wildcard: bool = False) -> str:
        uuid = uuid.lstrip("/").rstrip("/")

        expire = self._build_expire_time()

        acl = self._format_acl(uuid, wildcard=wildcard)

        signature = self._build_signature(expire, acl=acl)

        secure_url = self._build_url(uuid, expire, acl, signature)
        return secure_url

    def _build_url(
        self,
        uuid: str,
        expire: int,
        acl: str,
        signature: str,
    ) -> str:
        req_parameters = [
            f"exp={expire}",
            f"acl={acl}",
            f"hmac={signature}",
        ]

        token = self.field_delimeter.join(req_parameters)

        return self.template.format(
            cdn=self.cdn_url,
            uuid=uuid,
            token=token,
        )

    def _build_token(self, expire: int, acl: Optional[str], signature: str):
        token_parts = [
            f"exp={expire}",
            f"acl={acl}",
            f"hmac={signature}",
        ]
        return self.field_delimeter.join(token_parts)

    def _format_acl(self, uuid: str, wildcard: bool) -> str:
        if wildcard:
            return f"/{uuid}/*"
        return f"/{uuid}/"


class AkamaiSecureUrlBuilderWithUrlToken(BaseAkamaiSecureUrlBuilder):
    template = "{url}?token={token}"

    def build(self, uuid: str, wildcard: bool = False) -> str:
        if wildcard:
            raise ValueError(
                "Wildcards are not supported in AkamaiSecureUrlBuilderWithUrlToken."
            )

        url = uuid

        expire = self._build_expire_time()

        signature = self._build_signature(expire, url=url)

        secure_url = self._build_url(url, expire, signature)

        return secure_url

    def _build_url(
        self,
        url: str,
        expire: int,
        signature: str,
    ) -> str:
        req_parameters = [
            f"exp={expire}",
            f"hmac={signature}",
        ]

        token = self.field_delimeter.join(req_parameters)

        return self.template.format(
            url=url,
            token=token,
        )

    def _build_token(self, expire: int, url: str, signature: str):
        token_parts = [
            f"exp={expire}",
            f"url={url}",
            f"hmac={signature}",
        ]
        return self.field_delimeter.join(token_parts)


class AkamaiSecureUrlBuilder(AkamaiSecureUrlBuilderWithAclToken):
    def __init__(
        self,
        cdn_url: str,
        secret_key: str,
        window: int = 300,
        hash_algo=hashlib.sha256,
    ):
        warnings.warn(
            "AkamaiSecureUrlBuilder class was renamed to AkamaiSecureUrlBuilderWithAclToken",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(
            cdn_url=cdn_url,
            secret_key=secret_key,
            window=window,
            hash_algo=hash_algo,
        )
