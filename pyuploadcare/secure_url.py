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
        use_acl=True,
    ):
        self.secret_key = secret_key
        self.cdn_url = cdn_url
        self.window = window
        self.hash_algo = hash_algo
        self.use_acl = use_acl

    def build(self, uuid: str) -> str:
        uuid = uuid.lstrip("/").rstrip("/")

        expire = self._build_expire_time()

        acl = None
        if self.use_acl:
            acl = self._format_acl(uuid)

        hmac_signature = self._build_hmac(expire, acl)

        secure_url = self._build_url(uuid, hmac_signature, expire, acl)
        return secure_url

    def _build_url(
        self,
        uuid: str,
        hmac_signature: str,
        expire: int,
        acl: Optional[str] = None,
    ) -> str:
        req_parameters = [f"exp={expire}"]

        if acl:
            req_parameters.append(f"acl={acl}")

        req_parameters.append(f"hmac={hmac_signature}")

        token = self.field_delimeter.join(req_parameters)

        return self.template.format(
            cdn=self.cdn_url,
            uuid=uuid,
            token=token,
        )

    def _build_token(
        self, expire: int, hmac_signature: str, acl: Optional[str] = None
    ):
        token_parts = [f"exp={expire}"]

        if acl:
            token_parts.append(f"acl={acl}")

        token_parts.append(f"hmac={hmac_signature}")

        return self.field_delimeter.join(token_parts)

    def _format_acl(self, uuid: str) -> str:
        return f"/{uuid}/"

    def _build_expire_time(self) -> int:
        return int(time.time()) + self.window

    def _build_hmac(self, expire: int, acl: Optional[str] = None) -> str:
        hash_source = [
            f"exp={expire}",
        ]
        if acl:
            hash_source.append(f"acl={acl}")

        hmac_signature = hmac.new(
            self.secret_key.encode(),
            self.field_delimeter.join(hash_source).encode(),
            self.hash_algo,
        ).hexdigest()

        return hmac_signature
