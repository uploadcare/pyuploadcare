import os
import socket
from itertools import islice
from typing import (
    IO,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Type,
    Union,
)
from uuid import UUID

from pyuploadcare import File, FileGroup, FileList, GroupList, conf
from pyuploadcare.api import (
    DocumentConvertAPI,
    FilesAPI,
    GroupsAPI,
    ProjectAPI,
    UploadAPI,
    VideoConvertAPI,
    WebhooksAPI,
)
from pyuploadcare.api.auth import UploadcareAuth
from pyuploadcare.api.client import Client
from pyuploadcare.api.entities import ProjectInfo, Webhook
from pyuploadcare.exceptions import InvalidParamError
from pyuploadcare.helpers import extracts_uuids, get_file_size, guess_mime_type
from pyuploadcare.resources.file import FileFromUrl, UploadProgress
from pyuploadcare.secure_url import BaseSecureUrlBuilder


class Uploadcare:
    """Uploadcare client.

    Initialize client::

        >>> uploadcare = Uploadcare(public_key='<public-key>', secret_key='<secret-key>')

    Args:
        - public_key: Public key to access Uploadcare API.
        - secret_key: Secret ket to access Uploadcare API.
        - api_base: Rest API base url.
        - upload_base: Upload API base url.
        - cdn_base: CDN base url.
        - api_version: API version.
        - signed_uploads: Enable signed uploads.
        - signed_uploads_ttl: Signed uploads signature timeout in seconds.
        - verify_api_ssl: Verify Rest API SSL certificate.
        - verify_upload_ssl: Verify Upload API SSL certificate.
        - retry_throttled: Amount of retries after throttling header received.
        - user_agent_extension: Extra suffix to user agent to identify client.
        - timeout: HTTP requests timeout. If not set, default socket timeout is used.
        - batch_chunk_size: Amount of files to process at once
          in batch store and delete requests.
        - multipart_min_file_size: Mininum file size to use multipart uploading.
        - multipart_chunk_size: Chunk size in bytes for multipart uploading.
        - auth_class: Authentication class to use for API.
        - secure_url_builder: URL builder for secure delivery.

    """

    def __init__(
        self,
        public_key: Optional[str] = conf.pub_key,
        secret_key: Optional[str] = conf.secret,
        api_base=conf.api_base,
        upload_base=conf.upload_base,
        cdn_base=conf.cdn_base,
        api_version=conf.api_version,
        signed_uploads=conf.signed_uploads,
        signed_uploads_ttl=conf.signed_uploads_ttl,
        verify_api_ssl=conf.verify_api_ssl,
        verify_upload_ssl=conf.verify_upload_ssl,
        retry_throttled=conf.retry_throttled,
        user_agent_extension=conf.user_agent_extension,
        timeout=conf.timeout,
        batch_chunk_size=conf.batch_chunk_size,
        multipart_min_file_size=conf.multipart_min_file_size,
        multipart_chunk_size=conf.multipart_chunk_size,
        auth_class: Type[UploadcareAuth] = UploadcareAuth,
        secure_url_builder: Optional[BaseSecureUrlBuilder] = None,
    ):
        if not public_key:
            raise ValueError("public_key is required")

        self.public_key = public_key
        self.secret_key = secret_key
        self.api_version = api_version
        self.api_base = api_base
        self.upload_base = upload_base
        self.cdn_base = cdn_base
        self.signed_uploads = signed_uploads
        self.signed_uploads_ttl = signed_uploads_ttl
        self.verify_api_ssl = verify_api_ssl
        self.verify_upload_ssl = verify_upload_ssl
        self.retry_throttled = retry_throttled
        self.user_agent_extension = user_agent_extension
        self.batch_chunk_size = batch_chunk_size
        self.multipart_min_file_size = multipart_min_file_size
        self.multipart_chunk_size = multipart_chunk_size
        self.secure_url_builder = secure_url_builder

        if timeout is conf.DEFAULT:
            timeout = socket.getdefaulttimeout()

        self.timeout = timeout

        auth = auth_class(public_key, secret_key, self.api_version)  # type: ignore

        self.rest_client = Client(
            base_url=api_base,
            auth=auth,
            verify=verify_api_ssl,
            timeout=timeout,
            user_agent_extension=user_agent_extension,
            retry_throttled=retry_throttled,
            public_key=public_key,
        )

        self.upload_client = Client(
            base_url=upload_base,
            verify=verify_upload_ssl,
            timeout=timeout,
            user_agent_extension=user_agent_extension,
            retry_throttled=retry_throttled,
            public_key=public_key,
        )

        api_config = {
            "public_key": public_key,
            "secret_key": secret_key,
            "signed_uploads_ttl": signed_uploads_ttl,
        }
        self.upload_api = UploadAPI(client=self.upload_client, **api_config)  # type: ignore
        self.files_api = FilesAPI(client=self.rest_client, **api_config)  # type: ignore
        self.groups_api = GroupsAPI(client=self.rest_client, **api_config)  # type: ignore
        self.video_convert_api = VideoConvertAPI(
            client=self.rest_client, **api_config  # type: ignore
        )
        self.document_convert_api = DocumentConvertAPI(
            client=self.rest_client, **api_config  # type: ignore
        )
        self.webhooks_api = WebhooksAPI(client=self.rest_client, **api_config)  # type: ignore
        self.project_api = ProjectAPI(client=self.rest_client, **api_config)  # type: ignore

    def file(
        self,
        cdn_url_or_file_id: Union[str, UUID],
        file_info: Optional[Dict[str, Any]] = None,
    ) -> File:
        """File resource for working with user-uploaded files.

        It can take file UUID or group CDN url::

            >>> file_ = uploadcare.file('a771f854-c2cb-408a-8c36-71af77811f3b')
            >>> file_.cdn_url
            https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/
            >>> print uploadcare.file(
            ...    'https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/')
            https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/

        """
        file_ = File(cdn_url_or_file_id, client=self)
        if file_info:
            file_.default_effects = file_info.get("default_effects")
            file_._info_cache = file_info
        return file_

    def file_from_url(self, token) -> FileFromUrl:
        return FileFromUrl(token, client=self)

    def file_group(
        self, group_id: str, group_info: Optional[Dict[str, Any]] = None
    ) -> FileGroup:
        """
        File Group resource for working with user-uploaded group of files.

        It can take group id or group CDN url::

            >>> file_group = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')

        You can iterate ``file_group`` or get ``File`` instance by key::

            >>> [file_ for file_ in file_group]
            [<uploadcare.File 6c5e9526-b0fe-4739-8975-72e8d5ee6342>, None]
            >>> file_group[0]
            <uploadcare.File 6c5e9526-b0fe-4739-8975-72e8d5ee6342>
            >>> len(file_group)
            2

        But slicing is not supported because ``FileGroup`` is immutable::

            >>> file_group[:]
            TypeError: slicing is not supported

        If file was deleted then you will get ``None``::

            >>> file_group[1]
            None

        """
        file_group_ = FileGroup(group_id, client=self)
        file_group_._info_cache = group_info
        return file_group_

    def upload(  # noqa: C901
        self,
        file_handle: Union[IO, str],
        store=None,
        size: Optional[int] = None,
        callback: Optional[Callable[[UploadProgress], Any]] = None,
    ) -> "File":
        """Uploads a file and returns ``File`` instance.

        Method can accept file object or URL. Depending of file object size
        direct or multipart upload method will be chosen.

        Upload from url::

            >>> uploadcare = Uploadcare(public_key='<public-key>', secret_key='<secret-key>')
            >>> file: File = uploadcare.upload("https://shorturl.at/fAX28")

        Upload small file, direct upload is used::

            >>> fh = open('small_file.jpg', 'rb')
            >>> file: File = uploadcare.upload(fh)

        Upload big file, multipart upload is used::

            >>> with open('big_file.mp4', 'rb') as fh:
            >>>     file: File = uploadcare.upload(fh)

        To track uploading progress you can pass optional callback function::

            >>> def print_progress(info: UploadProgress):
            ...     print(f'{info.done}/{info.total} B')
            >>>
            >>> with open('big_file.mp4', 'rb') as fh:
            ...    file: File = uploadcare.upload(fh, callback=print_progress)
            0/11000000 B
            5242880/11000000 B
            10485760/11000000 B
            11000000/11000000 B

        Args:
            - file_handle: file object or url to upload to. If file object
                is passed, ``File.upload_files`` (direct upload) or
                ``File.multipart_upload`` (multipart upload) will be used.
                If file URL is passed, ``File.upload_from_url_sync`` will be
                used for uploading.
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings
            - size (Optional[int]): file size in bytes.
                If not set, it is calculated by ``os.fstat``.
                Used for multipart uploading.
            - callback (Optional[Callable[[UploadProgress], Any]]): Optional callback
                accepting ``UploadProgress`` to track uploading progress.

        Returns:
            ``File`` instance

        """

        # assume url is passed if str
        if isinstance(file_handle, str):
            file_url: str = file_handle
            return self.upload_from_url_sync(
                file_url,
                store=store,
                callback=callback,
            )

        file_obj: IO = file_handle

        if size is None:
            size = os.fstat(file_obj.fileno()).st_size

        # use direct upload for files less then multipart_min_file_size
        if size < self.multipart_min_file_size:
            files = self.upload_files([file_obj], store=store)
            if not files:
                raise ValueError("Failed to get uploaded file from response")
            file: "File" = files[0]

            if callback:
                callback(UploadProgress(total=size, done=size))

            return file

        file = self.multipart_upload(
            file_obj, store=store, size=size, callback=callback
        )
        return file

    @staticmethod
    def _format_store(store: Optional[bool]) -> str:
        values_map: Dict[Any, str] = {
            None: "auto",
            True: "1",
            False: "0",
        }

        if store not in values_map:
            store = None

        return values_map[store]

    def upload_files(
        self, file_objects: List[IO], store: Optional[bool] = None
    ) -> List["File"]:
        """Upload multiple files using direct upload.

        It support files smaller than 100MB only. If you want to upload larger files,
        use Multipart Uploads.

        Args:
            - file_objects: list of file objects to upload to
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings

        Returns:
            ``File`` instance

        """

        def _file_name(file_object, index):
            return os.path.basename(file_object.name or "") or f"file{index}"

        files = {
            _file_name(file_object, index): (
                _file_name(file_object, index),
                file_object,
                guess_mime_type(file_object),
            )
            for index, file_object in enumerate(file_objects)
        }

        response = self.upload_api.upload(
            files=files,
            store=self._format_store(store),
            secure_upload=self.signed_uploads,
            expire=self.signed_uploads_ttl,
        )
        ucare_files = [self.file(response[file_name]) for file_name in files]
        return ucare_files

    def multipart_upload(  # noqa: C901
        self,
        file_obj: IO,
        store: Optional[bool] = None,
        size: Optional[int] = None,
        mime_type: Optional[str] = None,
        callback: Optional[Callable[[UploadProgress], Any]] = None,
    ) -> "File":
        """Upload file straight to s3 by chunks.

        Multipart Uploads are useful when you are dealing with files larger than 100MB
        or explicitly want to use accelerated uploads.

        Args:
            - file_obj: file object to upload to
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings
            - size (Optional[int]): file size in bytes.
                If not set, it is calculated by ``os.fstat``
            - mime_type (Optional[str]): file mime type.
                If not set, it is guessed from filename extension.
            - callback (Optional[Callable[[UploadProgress], Any]]): Optional callback
                accepting ``UploadProgress`` to track uploading progress.

        Returns:
            ``File`` instance

        """
        if size is None:
            size = get_file_size(file_obj)

        if not mime_type:
            mime_type = guess_mime_type(file_obj)

        complete_response = self.upload_api.start_multipart_upload(
            file_name=file_obj.name,
            file_size=size,
            content_type=mime_type,
            store=self._format_store(store),
            secure_upload=self.signed_uploads,
            expire=self.signed_uploads_ttl,
        )

        multipart_uuid = complete_response["uuid"]

        parts: List[str] = complete_response["parts"]

        chunk = file_obj.read(self.multipart_chunk_size)

        uploaded_size = 0

        while chunk:
            chunk_url = parts.pop(0)
            self.upload_api.multipart_upload_chunk(chunk_url, chunk)
            uploaded_size += len(chunk)

            if callback:
                callback(UploadProgress(total=size, done=uploaded_size))

            chunk = file_obj.read(self.multipart_chunk_size)

        file_info: Dict = self.upload_api.multipart_complete(multipart_uuid)
        return self.file(file_info["uuid"], file_info)

    def upload_from_url(self, url, store=None, filename=None) -> FileFromUrl:
        """Uploads file from given url and returns ``FileFromUrl`` instance.

        Args:
            - url (str): URL of file to upload to
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings
            - filename (Optional[str]): Name of the uploaded file. If this not
                specified the filename will be obtained from response headers
                or source URL. Defaults to None.

        Returns:
            ``FileFromUrl`` instance

        """
        if store is None:
            store = "auto"
        elif store:
            store = "1"
        else:
            store = "0"

        token = self.upload_api.upload_from_url(
            source_url=url,
            store=store,
            filename=filename,
            secure_upload=self.signed_uploads,
            expire=self.signed_uploads_ttl,
        )
        file_from_url = FileFromUrl(token, self)
        return file_from_url

    def upload_from_url_sync(
        self,
        url,
        timeout=30,
        interval=0.3,
        until_ready=False,
        store=None,
        filename=None,
        callback: Optional[Callable[[UploadProgress], Any]] = None,
    ) -> File:
        """Uploads file from given url and returns ``File`` instance.

        Args:
            - url (str): URL of file to upload to
            - store (Optional[bool]): Should the file be automatically stored
                upon upload. Defaults to None.
                - False - do not store file
                - True - store file (can result in error if autostore
                               is disabled for project)
                - None - use project settings
            - filename (Optional[str]): Name of the uploaded file. If this not
                specified the filename will be obtained from response headers
                or source URL. Defaults to None.
            - timeout (Optional[int]): seconds to wait for successful upload.
                Defaults to 30.
            - interval (Optional[float]): interval between upload status checks.
                Defaults to 0.3.
            - until_ready (Optional[bool]): should we wait until file is
                available via CDN. Defaults to False.
            - callback (Optional[Callable[[UploadProgress], Any]]): Optional callback
                accepting ``UploadProgress`` to track uploading progress.

        Returns:
            ``File`` instance

        Raises:
            ``TimeoutError`` if file wasn't uploaded in time

        """
        ffu = self.upload_from_url(url, store, filename)
        return ffu.wait(
            timeout=timeout,
            interval=interval,
            until_ready=until_ready,
            callback=callback,
        )

    def store_files(self, files: Iterable[Union[str, "File"]]) -> None:
        """Stores multiple files by requesting Uploadcare API.

        Usage example::

            >>> uploadcare = Uploadcare(public_key='<public-key>', secret_key='<secret-key>')
            >>> files = [
            ... '6c5e9526-b0fe-4739-8975-72e8d5ee6342',
            ... 'a771f854-c2cb-408a-8c36-71af77811f3b'
            ... ]
            >>> uploadcare.store_files(files)

        Args:
            - files:
                List of file UUIDs, CND urls or ``File`` instances.
        """
        uuids = extracts_uuids(files)
        start = 0
        chunk = list(islice(uuids, start, self.batch_chunk_size))
        while chunk:
            self.files_api.batch_store(uuids)
            start += self.batch_chunk_size
            chunk = list(islice(uuids, start, self.batch_chunk_size))

    def delete_files(self, files: Iterable[Union[str, "File"]]) -> None:
        """Deletes multiple files by requesting Uploadcare API.

        Usage example::

            >>> uploadcare = Uploadcare(public_key='<public-key>', secret_key='<secret-key>')
            >>> files = [
            ... '6c5e9526-b0fe-4739-8975-72e8d5ee6342',
            ... 'a771f854-c2cb-408a-8c36-71af77811f3b'
            ... ]
            >>> uploadcare.delete_files(files)

        Args:
            - files:
                List of file UUIDs, CND urls or ``File`` instances.
        """
        uuids = extracts_uuids(files)
        start = 0
        chunk = list(islice(uuids, start, self.batch_chunk_size))
        while chunk:
            self.files_api.batch_delete(uuids)
            start += self.batch_chunk_size
            chunk = list(islice(uuids, start, self.batch_chunk_size))

    def create_file_group(self, files: List[File]) -> FileGroup:
        """Creates file group and returns ``FileGroup`` instance.

        It expects iterable object that contains ``File`` instances, e.g.::

            >>> uploadcare = Uploadcare(public_key='<public-key>', secret_key='<secret-key>')
            >>> file_1 = uploadcare.file('6c5e9526-b0fe-4739-8975-72e8d5ee6342')
            >>> file_2 = uploadcare.file('a771f854-c2cb-408a-8c36-71af77811f3b')
            >>> uploadcare.create_file_group([file_1, file_2])
            <uploadcare.FileGroup 0513dda0-6666-447d-846f-096e5df9e2bb~2>

        """
        if not files:
            raise InvalidParamError("set of files is empty")

        for file_ in files:
            if not isinstance(file_, File):
                raise InvalidParamError(
                    "all items have to be ``File`` instance"
                )

        file_urls = [str(file_) for file_ in files]
        group_info = self.upload_api.create_group(
            files=file_urls,
            secure_upload=self.signed_uploads,
            expire=self.signed_uploads_ttl,
        )

        group = self.file_group(group_info["id"], group_info)
        return group

    def list_files(
        self,
        starting_point=None,
        ordering=None,
        limit: Optional[int] = None,
        request_limit: Optional[int] = None,
        stored: Optional[bool] = None,
        removed: Optional[bool] = None,
    ) -> FileList:
        """List files.

        Returns ``FileList`` instance providing iteration over all uploaded files.

        Args:m
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

        return FileList(
            client=self,
            starting_point=starting_point,
            ordering=ordering,
            limit=limit,
            request_limit=request_limit,
            stored=stored,
            removed=removed,
        )

    def list_file_groups(
        self,
        starting_point=None,
        ordering=None,
        limit: Optional[int] = None,
        request_limit: Optional[int] = None,
    ):
        """List file groups.

        Return ``GroupList`` instance providing iteration over all groups for project.

        Args:
            - ``starting_point`` -- a starting point for filtering groups.
              It is reflects a ``from`` parameter from the REST API.
            - ``ordering`` -- a string with name of the field what must be used
              for sorting files. The actual list of supported fields you can find in
              documentation.
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
        return GroupList(
            client=self,
            starting_point=starting_point,
            ordering=ordering,
            limit=limit,
            request_limit=request_limit,
        )

    def create_webhook(
        self,
        target_url: str,
        event="file.uploaded",
        is_active=True,
        signing_secret=None,
    ) -> Webhook:
        """Create and subscribe to a webhook."""

        data = {
            "target_url": target_url,
            "event": event,
            "is_active": is_active,
        }

        if signing_secret:
            data["signing_secret"] = signing_secret

        return self.webhooks_api.create(data)

    def list_webhooks(self, limit=None) -> Iterable[Webhook]:
        """List of project webhooks."""

        return self.webhooks_api.list(limit=limit)

    def update_webhook(  # noqa: C901
        self,
        webhook_id: Union[Webhook, int],
        target_url=None,
        event=None,
        is_active=None,
        signing_secret=None,
    ) -> Webhook:
        """Update webhook attributes."""

        if isinstance(webhook_id, Webhook):
            webhook_id = webhook_id.id

        data = {}
        if target_url is not None:
            data["target_url"] = target_url
        if event is not None:
            data["event"] = event
        if is_active is not None:
            data["is_active"] = is_active
        if signing_secret is not None:
            data["signing_secret"] = signing_secret

        return self.webhooks_api.update(webhook_id, data)  # type: ignore

    def delete_webhook(self, webhook_id: Union[Webhook, int]) -> None:
        """Unsubscribe and delete a webhook."""

        if isinstance(webhook_id, Webhook):
            webhook_id = webhook_id.id

        return self.webhooks_api.delete(webhook_id)  # type: ignore

    def get_project_info(self) -> ProjectInfo:
        """Get info about account project."""

        return self.project_api.retrieve()

    def generate_secure_url(self, uuid: Union[str, UUID]) -> str:
        """Generate authenticated URL."""
        if isinstance(uuid, UUID):
            uuid = str(uuid)

        if not self.secure_url_builder:
            raise ValueError("secure_url_builder must be set")

        return self.secure_url_builder.build(uuid)
