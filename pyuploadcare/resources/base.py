import itertools
from datetime import date, datetime
from typing import TYPE_CHECKING

from pyuploadcare.api.base import ListCountMixin


if TYPE_CHECKING:
    from pyuploadcare.client import Uploadcare


class BaseApiList:
    # ordering fields names which must be handled as datetime
    datetime_ordering_fields = ()

    resource_api: ListCountMixin
    constructor_name: str
    resource_id_field: str

    def __init__(
        self,
        client: "Uploadcare",
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
        self._client = client

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
            resource_info = entity.dict()
            resource_id = resource_info.get(self.resource_id_field)
            constructor = getattr(self._client, self.constructor_name)
            yield constructor(resource_id, resource_info)

    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(
                itertools.islice(self, item.start, item.stop, item.step)
            )
        try:
            return next(itertools.islice(self, item, None))
        except StopIteration:
            raise IndexError("index out of range")

    def count(self):
        if self.starting_point:
            raise ValueError(
                "Can't count objects if the `starting_point` present"
            )
        if self._count is None:
            qs = self.query_parameters(limit=None)
            self._count = self.resource_api.count(**qs)
        return self._count
