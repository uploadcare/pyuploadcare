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

    def get_token(self, uuid: str, wildcard: bool = False) -> str:
        raise NotImplementedError(
            f"{self.__class__} doesn't provide get_token()"
        )


class BaseAkamaiSecureUrlBuilder(BaseSecureUrlBuilder):
    """Akamai secure url builder.

    See https://uploadcare.com/docs/security/secure_delivery/
    for more details.
    """

    template = "{base}?token={token}"
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

    def build(self, uuid: str, wildcard: bool = False) -> str:
        uuid_or_url = self._format_uuid_or_url(uuid)
        token = self.get_token(uuid_or_url, wildcard=wildcard)
        secure_url = self._build_url(uuid_or_url, token)
        return secure_url

    def get_token(self, uuid: str, wildcard: bool = False) -> str:
        uuid_or_url = self._format_uuid_or_url(uuid)
        expire = self._build_expire_time()
        acl = self._format_acl(uuid_or_url, wildcard=wildcard)
        signature = self._build_signature(uuid_or_url, expire, acl)
        token = self._build_token(expire, acl, signature)
        return token

    def _build_expire_time(self) -> int:
        return int(time.time()) + self.window

    def _build_signature(
        self, uuid_or_url: str, expire: int, acl: Optional[str]
    ) -> str:
        hash_source = [
            f"exp={expire}",
            f"acl={acl}" if acl else f"url={uuid_or_url}",
        ]

        signature = hmac.new(
            binascii.a2b_hex(self.secret_key.encode()),
            self.field_delimeter.join(hash_source).encode(),
            self.hash_algo,
        ).hexdigest()

        return signature

    def _build_token(self, expire: int, acl: Optional[str], signature: str):
        token_parts = [
            f"exp={expire}",
            f"acl={acl}" if acl else None,
            f"hmac={signature}",
        ]

        return self.field_delimeter.join(
            part for part in token_parts if part is not None
        )

    @abstractmethod
    def _build_base_url(self, uuid_or_url: str):
        raise NotImplementedError

    def _build_url(
        self,
        uuid_or_url: str,
        token: str,
    ) -> str:
        base_url = self._build_base_url(uuid_or_url)
        return self.template.format(
            base=base_url,
            token=token,
        )

    @abstractmethod
    def _format_acl(self, uuid_or_url: str, wildcard: bool) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def _format_uuid_or_url(self, uuid_or_url: str) -> str:
        raise NotImplementedError


class AkamaiSecureUrlBuilderWithAclToken(BaseAkamaiSecureUrlBuilder):
    base_template = "https://{cdn}/{uuid}/"

    def _build_base_url(self, uuid_or_url: str):
        return self.base_template.format(cdn=self.cdn_url, uuid=uuid_or_url)

    def _format_acl(self, uuid_or_url: str, wildcard: bool) -> str:
        if wildcard:
            return f"/{uuid_or_url}/*"
        return f"/{uuid_or_url}/"

    def _format_uuid_or_url(self, uuid_or_url: str) -> str:
        return uuid_or_url.lstrip("/").rstrip("/")


class AkamaiSecureUrlBuilderWithUrlToken(BaseAkamaiSecureUrlBuilder):
    def _build_base_url(self, uuid_or_url: str):
        return uuid_or_url

    def _format_acl(self, uuid_or_url: str, wildcard: bool) -> None:
        if wildcard:
            raise ValueError(
                "Wildcards are not supported in AkamaiSecureUrlBuilderWithUrlToken."
            )
        return None

    def _format_uuid_or_url(self, uuid_or_url: str) -> str:
        if "://" not in uuid_or_url:
            raise ValueError(f"{uuid_or_url} doesn't look like a URL")
        return uuid_or_url


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
