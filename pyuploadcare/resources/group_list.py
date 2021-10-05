from pyuploadcare.resources.base import BaseApiList


class GroupList(BaseApiList):
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
        >>> for f in uploadcare.list_file_groups(starting_point=last_week):
        >>>     print(f.datetime_created)

    Count objects::

        >>> print('Number of groups is', uploadcare.list_file_groups().count())

    """

    constructor_name = "file_group"
    resource_id_field = "id"
    datetime_ordering_fields = ("", "datetime_created")

    @property
    def resource_api(self):
        return self._client.groups_api
