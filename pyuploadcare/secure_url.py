import binascii
import hashlib
import hmac
import re
import time
import warnings
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import quote_plus, urlparse


class BaseSecureUrlBuilder(ABC):
    @abstractmethod
    def build(self, handle: str, wildcard: bool = False) -> str:
        """
        :param handle: Can be one of the following: UUID, UUID with transformations, full URL.
        """
        raise NotImplementedError

    def get_token(self, handle: str, wildcard: bool = False) -> str:
        """
        :param handle: Can be one of the following: UUID, UUID with transformations, full URL.
        """
        raise NotImplementedError(
            f"{self.__class__} doesn't provide get_token()"
        )


class BaseAkamaiSecureUrlBuilder(BaseSecureUrlBuilder):
    """Akamai secure url builder.

    See https://uploadcare.com/docs/security/secure_delivery/
    for more details.
    """

    base_template = "https://{cdn}/{path}/"
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

    def build(self, handle: str, wildcard: bool = False) -> str:
        token = self.get_token(handle, wildcard=wildcard)
        secure_url = self._build_url(handle, token)
        return secure_url

    def get_token(self, handle: str, wildcard: bool = False) -> str:
        path = self._get_path(handle)
        expire = self._build_expire_time()
        acl = self._format_acl(path, wildcard=wildcard)
        signature = self._build_signature(handle, expire, acl)
        token = self._build_token(expire, acl, signature)
        return token

    def _prepare_path_for_url(self, path: str) -> str:
        path = re.sub(
            r"(%..)",
            lambda match: match.group(1).lower(),
            quote_plus(path, safe=","),
        )
        path = self._prepare_path_for_acl(path)
        return path

    def _prepare_path_for_acl(self, path: str) -> str:
        for escape_char in "~":
            path = path.replace(
                escape_char, "%" + hex(ord(escape_char)).lower()[2:]
            )
        return path

    def _build_expire_time(self) -> int:
        return int(time.time()) + self.window

    def _build_signature(
        self, handle: str, expire: int, acl: Optional[str]
    ) -> str:
        path = self._get_path(handle)
        path = self._prepare_path_for_url(path)
        hash_source = [
            f"exp={expire}",
            f"acl={acl}" if acl else f"url={path}",
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

    def _build_url(
        self,
        handle: str,
        token: str,
    ) -> str:
        base_url = self._build_base_url(handle)
        return self.template.format(
            base=base_url,
            token=token,
        )

    def _get_path(self, handle: str) -> str:
        """
        >>> builder._get_path("fake-uuid")
        /fake-uuid/
        >>> builder._get_path("https://sectest.ucarecdn.com/fake-uuid/-/resize/20x20/")
        /fake-uuid/-/resize/20x20/
        """
        path = handle
        parsed = urlparse(path)
        if parsed.netloc:
            # extract uuid with transformations from url
            path = parsed.path
        if not path.startswith("/"):
            path = f"/{path}"
        return path

    def _build_base_url(self, handle: str):
        """
        >>> builder._build_base_url("fake-uuid")
        https://sectest.ucarecdn.com/fake-uuid/
        >>> builder._get_path("https://sectest.ucarecdn.com/fake-uuid/-/resize/20x20/")
        https://sectest.ucarecdn.com/fake-uuid/-/resize/20x20/
        """
        path = self._get_path(handle)
        path = path.lstrip("/").rstrip("/")
        base_url = self.base_template.format(cdn=self.cdn_url, path=path)
        return base_url

    @abstractmethod
    def _format_acl(self, handle: str, wildcard: bool) -> Optional[str]:
        raise NotImplementedError


class AkamaiSecureUrlBuilderWithAclToken(BaseAkamaiSecureUrlBuilder):
    def _format_acl(self, handle: str, wildcard: bool) -> str:
        path = self._get_path(handle)
        path = path.lstrip("/").rstrip("/")
        path = self._prepare_path_for_acl(path)
        if wildcard:
            return f"/{path}/*"
        return f"/{path}/"


class AkamaiSecureUrlBuilderWithUrlToken(BaseAkamaiSecureUrlBuilder):
    def _format_acl(self, handle: str, wildcard: bool) -> None:
        if wildcard:
            raise ValueError(
                "Wildcards are not supported in AkamaiSecureUrlBuilderWithUrlToken."
            )
        return None


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
