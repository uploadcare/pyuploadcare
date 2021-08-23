from typing import Union
from typing import Iterable
from uuid import UUID
from pyuploadcare import entities
from pyuploadcare.base import (
    API,
    CreateMixin,
    ListMixin,
    RetrieveMixin,
    DeleteMixin,
)


class FilesAPI(API, ListMixin, RetrieveMixin, DeleteMixin):
    resource_type = "files"
    entity_class = entities.FileInfo

    def store(self, file_uuid: Union[UUID, str]):
        url = self._build_url(file_uuid, suffix="storage")
        document = self._client.put(url).json()
        return self._resource_to_entity(document)

    def batch_store(self, file_uuids: Iterable[Union[UUID, str]]):
        url = self._build_url(suffix="storage")
        document = self._client.put(url, json=file_uuids).json()
        for resource in document["results"]:
            yield self._resource_to_entity(resource)

    def batch_delete(self, file_uuids: Iterable):
        url = self._build_url(suffix="storage")
        document = self._client.delete_with_payload(
            url, json=file_uuids
        ).json()
        for resource in document["results"]:
            yield self._resource_to_entity(resource)

    def local_copy(self, source: Union[UUID, str], store: bool = False):
        url = self._build_url(suffix="local_copy")
        data = {"source": source, "store": store}
        document = self._client.post(url, json=data).json()
        return document["result"]

    def remote_copy(
        self,
        source: Union[UUID, str],
        target: str,
        make_public: bool = True,
        pattern: str = "${default}",
    ):
        url = self._build_url(suffix="remote_copy")
        data = {
            "source": source,
            "target": target,
            "make_public": make_public,
            "pattern": pattern,
        }
        document = self._client.post(url, json=data).json()
        return document["result"]


class GroupsAPI(API, ListMixin, RetrieveMixin):
    resource_type = "groups"
    entity_class = entities.GroupInfo

    def store(self, file_uuid: Union[UUID, str]):
        url = self._build_url(file_uuid, suffix="storage")
        document = self._client.put(url).json()
        return self._resource_to_entity(document)


class ProjectAPI(API, RetrieveMixin):
    resource_type = "project"
    entity_class = entities.ProjectInfo


class WebhooksAPI(API, CreateMixin, ListMixin, RetrieveMixin, DeleteMixin):
    resource_type = "webhooks"
    entity_class = entities.WebhookInfo
