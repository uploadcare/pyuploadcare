from pyuploadcare.resources.base import BaseApiList


class FileList(BaseApiList):
    """List of File resources.

    This class provides iteration over all uploaded files.

    You can specify:

    - ``starting_point`` -- a starting point for filtering files.
      It is reflects a ``from`` parameter from REST API.
    - ``ordering`` -- a string with name of the field what must be used
      for sorting files. The actual list of supported fields you can find in
      documentation: http://uploadcare.com/documentation/rest/#file-files
    - ``limit`` -- a total number of objects to be iterated.
      If not specified, all available objects are iterated;
    - ``request_limit`` -- a number of objects retrieved per request (page).
      Usually, you don't need worry about this parameter.
    - ``stored`` -- ``True`` to include only stored files,
      ``False`` to exclude, ``None`` is default, will not exclude anything;
    - ``removed`` -- ``True`` to include only removed files,
      ``False`` to exclude, ``None`` will not exclude anything.
      The default is ``False``.

    Files can't be stored and removed at the same time, such query will
    always return an empty set.

    But files can be not stored and not removed (just uploaded files).

    Usage example::

        >>> for f in uploadcare.list_files(removed=None):
        >>>     print(f.datetime_uploaded)

    Count objects::

        >>> print('Number of stored files is', uploadcare.list_files(stored=True).count())

    """

    constructor_name = "file"
    resource_id_field = "uuid"
    datetime_ordering_fields = ("", "datetime_uploaded")

    def __init__(self, *args, **kwargs):
        self.stored = kwargs.pop("stored", None)
        self.removed = kwargs.pop("removed", None)
        super(FileList, self).__init__(*args, **kwargs)

    @property
    def resource_api(self):
        return self._client.files_api

    def query_parameters(self, **parameters):
        if self.stored is not None:
            parameters.setdefault("stored", str(bool(self.stored)).lower())

        if self.removed is not None:
            parameters.setdefault("removed", str(bool(self.removed)).lower())

        return super().query_parameters(**parameters)
