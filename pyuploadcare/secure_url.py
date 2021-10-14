import hashlib
import hmac
import time
from abc import ABC, abstractmethod
from typing import Optional


class BaseSecureUrlBuilder(ABC):
    @abstractmethod
    def build(self, uuid: str) -> str:
        raise NotImplementedError


class AkamaiSecureUrlBuilder(BaseSecureUrlBuilder):
    """Akamai secure url builder.

    See https://uploadcare.com/docs/security/secure_delivery/
    for more details.
    """

    template = "https://{cdn}/{uuid}/?token={token}"
    field_delimeter = "~"

    def __init__(
        self,
        cdn_url: str,
        secret_key: str,
        window: int = 300,
        hash_algo=hashlib.sha1,
    ):
        self.secret_key = secret_key
        self.cdn_url = cdn_url
        self.window = window
        self.hash_algo = hash_algo

    def build(self, uuid: str) -> str:
        uuid = uuid.lstrip("/").rstrip("/")

        expire = self._build_expire_time()

        acl = self._format_acl(uuid)

        signature = self._build_signature(expire, acl)

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

    def _format_acl(self, uuid: str) -> str:
        return f"/{uuid}/"

    def _build_expire_time(self) -> int:
        return int(time.time()) + self.window

    def _build_signature(self, expire: int, acl: str) -> str:
        hash_source = [
            f"exp={expire}",
            f"acl={acl}",
        ]

        signature = hmac.new(
            self.secret_key.encode(),
            self.field_delimeter.join(hash_source).encode(),
            self.hash_algo,
        ).hexdigest()

        return signature
