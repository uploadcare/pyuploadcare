from pyuploadcare.resources.base import ApiMixin, BaseApiList
from pyuploadcare.resources.file_group import FileGroup


class GroupList(BaseApiList, ApiMixin):
    """List of FileGroup resources.

    This class provides iteration over all groups for project. You can specify:

    - ``starting_point`` -- a starting point for filtering groups.
      It is reflects a ``from`` parameter from the REST API.
    - ``ordering`` -- a string with name of the field what must be used
      for sorting files. The actual list of supported fields you can find in
      documentation: https://uploadcare.com/docs/api_reference/rest/accessing_groups/#properties
    - ``limit`` -- a total number of objects to be iterated.
      If not specified, all available objects are iterated;
    - ``request_limit`` -- a number of objects retrieved per request (page).
      Usually, you don't need worry about this parameter.

    Usage example::

        >>> from datetime import datetime, timedelta
        >>> last_week = datetime.now() - timedelta(weeks=1)
        >>> for f in GroupList(starting_point=last_week):
        >>>     print(f.datetime_created())

    Count objects::

        >>> print('Number of groups is', GroupList().count())

    """

    constructor = FileGroup.construct_from
    datetime_ordering_fields = ("", "datetime_created")

    @property
    def resource_api(self):
        return self.groups_api
