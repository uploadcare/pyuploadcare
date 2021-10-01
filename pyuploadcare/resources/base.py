from datetime import date, datetime

from pyuploadcare.api.api import (
    DocumentConvertAPI,
    FilesAPI,
    GroupsAPI,
    UploadAPI,
    VideoConvertAPI,
)
from pyuploadcare.api.base import ListCountMixin
from pyuploadcare.resources.helpers import classproperty


class BaseApiList:
    # abstract
    constructor = None
    # ordering fields names which must be handled as datetime
    datetime_ordering_fields = ()

    resource_api: ListCountMixin

    def __init__(
        self,
        starting_point=None,
        ordering=None,
        limit=None,
        request_limit=None,
    ):
        self.ordering = ordering
        self.starting_point = starting_point
        self.limit = limit
        self.request_limit = request_limit
        self._count = None

    @property
    def starting_point(self):
        return self._starting_point

    @starting_point.setter
    def starting_point(self, value):
        ordering_field = (self.ordering or "").lstrip("-")
        datetime_fields = self.datetime_ordering_fields

        if value and ordering_field in datetime_fields:
            if not isinstance(value, (datetime, date)):
                raise ValueError("The starting_point must be a datetime")
            value = value.isoformat()

        self._starting_point = value

    def query_parameters(self, **parameters):
        if self.starting_point is not None:
            parameters.setdefault("from", self.starting_point)

        if self.ordering is not None:
            parameters.setdefault("ordering", self.ordering)

        if self.limit is not None:
            parameters.setdefault("limit", self.limit)

        if self.request_limit is not None:
            parameters.setdefault("request_limit", self.request_limit)

        return parameters

    def __iter__(self):
        qs = self.query_parameters()
        for entity in self.resource_api.list(**qs):
            yield self.constructor(entity.dict())

    def count(self):
        if self.starting_point:
            raise ValueError(
                "Can't count objects if the `starting_point` present"
            )
        if self._count is None:
            qs = self.query_parameters(limit=None)
            self._count = self.resource_api.count(**qs)
        return self._count


class ApiMixin:
    @classproperty
    def files_api(cls) -> FilesAPI:
        return FilesAPI()

    @classproperty
    def upload_api(cls) -> UploadAPI:
        return UploadAPI()

    @classproperty
    def groups_api(cls) -> GroupsAPI:
        return GroupsAPI()

    @classproperty
    def video_convert_api(cls) -> VideoConvertAPI:
        return VideoConvertAPI()

    @classproperty
    def document_convert_api(cls) -> DocumentConvertAPI:
        return DocumentConvertAPI()
