========
Core API
========

Initialization
--------------

You can use pyuploadcare in any Python project. You need to pass
your project keys to ``Uploadcare`` client::

    from pyuploadcare import Uploadcare
    uploadcare = Uploadcare(public_key='<your public key>', secret_key='<your private key>')

Uploading files
---------------

Upload single file. ``File.upload`` method can accept file object or URL. Depending of file object size
direct or multipart upload method will be chosen::

    with open('file.txt', 'rb') as file_object:
        ucare_file: File = uploadcare.upload(file_object)


Upload file from url::

    ucare_file: File = uploadcare.upload("https://github.githubassets.com/images/modules/logos_page/Octocat.png")

Upload multiple files. Direct upload method is used::

    file1 = open('file1.txt', 'rb')
    file2 = open('file2.txt', 'rb')
    ucare_files: List[File] = uploadcare.upload_files([file1, file2])

Send single file via multipart upload::

    with open('file.txt', 'rb') as file_object:
        ucare_file: File = uploadcare.upload(file_object)

``Uploadcare.upload`` method accepts optional callback function to track uploading progress.
Example of using callback function for printing progress::

    >>> def print_progress(info: UploadProgress):
    ...     print(f'{info.done}/{info.total} B')

    >>> # multipart upload is used
    >>> with open('big_file.jpg', 'rb') as fh:
    ...    uploadcare.upload(fh, callback=print_progress)
    0/11000000 B
    5242880/11000000 B
    10485760/11000000 B
    11000000/11000000 B

    >>> # upload from url is used
    >>> uploadcare.upload("https://github.githubassets.com/images/modules/logos_page/Octocat.png", callback=print_progress)
    32590/32590 B

    >>> # direct upload is used. Callback is called just once after successful upload
    >>> with open('small_file.jpg', 'rb') as fh:
    ...     uploadcare.upload(fh, callback=print_progress)
    56780/56780 B


List files
----------

Get list of files::

    files: FileList = uploadcare.list_files(stored=True, limit=10)
    for file in files:
        print(file.info)

Retrieve files
--------------

Get existing file::

    file: File = uploadcare.file("740e1b8c-1ad8-4324-b7ec-112c79d8eac2")
    print(file.info)

Store files
-----------

Store single file::

    file: File = uploadcare.file("740e1b8c-1ad8-4324-b7ec-112c79d8eac2")
    file.store()

Store multiple files::

    files = [
        '6c5e9526-b0fe-4739-8975-72e8d5ee6342',
        'a771f854-c2cb-408a-8c36-71af77811f3b'
    ]
    uploadcare.store_files(files)

Delete files
------------

Delete single file::

    file: File = uploadcare.file("740e1b8c-1ad8-4324-b7ec-112c79d8eac2")
    file.delete()

Delete multiple files::

    files = [
        '6c5e9526-b0fe-4739-8975-72e8d5ee6342',
        'a771f854-c2cb-408a-8c36-71af77811f3b'
    ]
    uploadcare.delete_files(files)

Video conversion
----------------

Uploadcare can encode video files from all popular formats, adjust their quality, format and dimensions, cut out a video fragment, and generate thumbnails via REST API.

After each video file upload you obtain a file identifier in UUID format. Then you can use this file identifier to convert your video in multiple ways::

    file = uploadcare.file('740e1b8c-1ad8-4324-b7ec-112c79d8eac2')
    transformation = (
        VideoTransformation()
            .format(Format.mp4)
            .size(width=640, height=480, resize_mode=ResizeMode.add_padding)
            .quality(Quality.lighter)
            .cut(start_time='2:30.535', length='2:20.0')
            .thumbs(10)
    )
    converted_file: File = file.convert(transformation)

or you can use API directly to convert single or multiple files::

    transformation = VideoTransformation().format(VideoFormat.webm).thumbs(2)
    paths: List[str] = [
        transformation.path("740e1b8c-1ad8-4324-b7ec-112c79d8eac2"),
    ]

    response = uploadcare.video_convert_api.convert(paths)
    video_convert_info = response.result[0]
    converted_file = uploadcare.file(video_convert_info.uuid)

    video_convert_status = uploadcare.video_convert_api.status(video_convert_info.token)

Document Conversion
-------------------

Uploadcare allows converting documents to the following target formats: doc, docx, xls, xlsx, odt, ods, rtf, txt, pdf, jpg, png. Document Conversion works via our REST API.

After each document file upload you obtain a file identifier in UUID format. Then you can use this file identifier to convert your document to a new format::

    file = uploadcare.file('0e1cac48-1296-417f-9e7f-9bf13e330dcf')
    transformation = DocumentTransformation().format(DocumentFormat.pdf)
    converted_file: File = file.convert(transformation)

or create an image of a particular page (if using image format)::

    file = uploadcare.file('5dddafa0-a742-4a51-ac40-ae491201ff97')
    transformation = DocumentTransformation().format(DocumentFormat.png).page(1)
    converted_file: File = file.convert(transformation)

or you can use API directly to convert single or multiple files::

    transformation = DocumentTransformation().format(DocumentFormat.pdf)

    paths: List[str] = [
        transformation.path("0e1cac48-1296-417f-9e7f-9bf13e330dcf"),
    ]

    response = uploadcare.document_convert_api.convert([path])
    document_convert_info = response.result[0]
    converted_file = uploadcare.file(document_convert_info.uuid)

    document_convert_status = uploadcare.document_convert_api.status(document_convert_info.token)


Image transformations
---------------------

Uploadcare allows to apply image transformations to files. ``File.cdn_url`` attribute returns CDN url::

    >>> file_ = File('a771f854-c2cb-408a-8c36-71af77811f3b')
    >>> file_.cdn_url
    https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/

You can set default effects by string::

    >>> file_.set_effects('effect/flip/-/effect/mirror/')
    >>> file_.cdn_url
    https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/effect/flip/-/effect/mirror/

or by image transformation builder::

    >>> file_.set_effects(ImageTransformation().grayscale().flip())
    >>> file_.cdn_url
    https://ucarecdn.com/a771f854-c2cb-408a-8c36-71af77811f3b/-/grayscale/-/flip/

Using addons
---------------------

To perform operation provided by addon you need to select the file and to set parameters of execution.
Parameters are always specified by particular addon.
For example, AWS Rekognition addon has no params to setup::

    from pyuploadcare.api.addon_entities import AddonRemoveBGExecutionParams
    remove_bg_params = AddonRemoveBGExecutionParams(
        crop=True,
        crop_margin="20px",
        scale="15%"
    )

    from pyuploadcare.api.addon_entities import AddonClamAVExecutionParams
    clamav_params = AddonClamAVExecutionParams(purge_infected=True)


To execute addon call an API `execute` method with the file and parameters::

    target_file = uploadcare.file("59fccca5-3af7-462f-905b-ed7de83b9762")
    # params - from previous step
    remove_bg_result = uploadcare.addons_api.execute(
        target_file,
        AddonLabels.REMOVE_BG,
        remove_bg_params,
    )

    aws_recognition_result = uploadcare.addons_api.execute(
        target_file,
        AddonLabels.AWS_LABEL_RECOGNITION,
    )

    clamav_result = uploadcare.addons_api.execute(
        target_file,
        AddonLabels.CLAM_AV,
        clamav_params,
    )

Each of these `*_result` objects contains not the result of operation itself, but `request_id` of invoked task, so we can check the state of execution.
To check status of performed task use `status` method::

    addon_task_status = uploadcare.addons_api.status(request_id, addon)

If addon execution produces new data for file (like an AWS recognition does), this data will be placed at `appdata` complex attribute of `File.info` (see `addons documentation`_)


File metadata
-----------------

You can store some additional information for a file (`metadata documentation`_). Access is organized in key-value manner.
Metadata may be initially set while uploading::

    custom_metadata = {
        "specific_key_1": "some_value_1",
        "specific_key_2": "constant_for_this_planet",
    }
    with open('file.txt', 'rb') as file_object:
        ucare_file: File = uploadcare.upload(file_object, metadata=custom_metadata)

While uploading multiple files at once you can set common metadata that will be applied for every file in collection::

    file1 = open('file1.txt', 'rb')
    file2 = open('file2.txt', 'rb')
    ucare_files: List[File] = uploadcare.upload_files(
        [file1, file2],
        common_metadata=custom_metadata,
    )
    # don't forget to close the files, of course

Value may be set by key::

    md_key, md_value = "new_key_for_filemeta", "obvious_value"
    uploadcare.metadata_api.update_or_create_key(file_id, md_key, md_value)


Value may be deleted by key::

    uploadcare.metadata_api.delete_key(file_id, mkey=md_key)

Value may be retrieved by key::

    meta_value = uploadcare.metadata_api.get_key(file_id, mkey=md_key)

Or the whole metadata may be got at once::

    file_metadata = uploadcare.metadata_api.get_all_metadata(file_id, mkey=md_key)

But you should better use a special attribute of `File.info`::

    file_metadata = file.info.metadata


Create file group
-----------------

Create file group::

    file_1: File = uploadcare.file('6c5e9526-b0fe-4739-8975-72e8d5ee6342')
    file_2: File = uploadcare.file('a771f854-c2cb-408a-8c36-71af77811f3b')
    file_group: FileGroup = uploadcare.create_file_group([file_1, file_2])


Retrieve file group
-------------------

Get file group::

    file_group: FileGroup = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')
    print(file_group.info())

Store file group
----------------

Stores all group's files::

    file_group: FileGroup = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')
    file_group.store()

List file groups
----------------

List file groups::

    file_groups: List[FileGroup] = uploadcare.list_file_groups(limit=10)
    for file_group in file_groups:
        print(file_group.info)

Delete file groups
----------------

Delete file groups::

    file_group: FileGroup = uploadcare.file_group('0513dda0-582f-447d-846f-096e5df9e2bb~2')
    file_group.delete()


Create webhook
--------------

Create a webhook::

    webhook: Webhook = uploadcare.create_webhook("https://path/to/webhook")

Create a webhook with a signing secret::

    webhook = uploadcare.create_webhook(
        target_url="https://path/to/webhook",
        signing_secret="7kMVZivndx0ErgvhRKAr",
    )

List webhooks
-------------

List webhooks::

    webhooks: List[Webhook] = list(uploadcare.list_webhooks(limit=10))

Update webhook
--------------

Update a webhook::

    webhook: Webhook = uploadcare.update_webhook(webhook_id, is_active=False)

Update a webhook's signing secret::

    webhook: Webhook = uploadcare.update_webhook(webhook_id, signing_secret="7kMVZivndx0ErgvhRKAr")

Delete webhook
--------------

Delete a webhook::

    uploadcare.delete_webhook(webhook_id)


Get project info
----------------

Get project info::

    project_info: ProjectInfo = uploadcare.get_project_info()


Secure delivery
---------------

You can use your own custom domain and CDN provider for deliver files with authenticated URLs (see `original documentation`_).

Generate secure for file::

    from pyuploadcare import Uploadcare
    from pyuploadcare.secure_url import AkamaiSecureUrlBuilder

    secure_url_bulder = AkamaiSecureUrlBuilder("your cdn>", "<your secret for token generation>")

    uploadcare = Uploadcare(
        public_key='<your public key>',
        secret_key='<your private key>',
        secure_url_builder=secure_url_bulder,
    )

    secure_url = uploadcare.generate_secure_url('52da3bfc-7cd8-4861-8b05-126fef7a6994')

Generate secure for file with transformations::

    secure_url = uploadcare.generate_secure_url(
        '52da3bfc-7cd8-4861-8b05-126fef7a6994/-/resize/640x/other/transformations/'
    )

Useful links
------------

- `Uploadcare documentation`_
- `Upload`_ API reference
- `REST`_ API reference
- `Django app example`_

.. _Uploadcare documentation: https://uploadcare.com/docs/?utm_source=github&utm_campaign=pyuploadcare
.. _Upload: https://uploadcare.com/api-refs/upload-api/?utm_source=github&utm_campaign=pyuploadcare
.. _REST: https://uploadcare.com/api-refs/rest-api/?utm_source=github&utm_campaign=pyuploadcare
.. _Django app example: https://github.com/uploadcare/pyuploadcare-example
.. _original documentation: https://uploadcare.com/docs/security/secure-delivery/?utm_source=github&utm_campaign=pyuploadcare
.. _addons documentation: https://uploadcare.com/api-refs/rest-api/v0.7.0/#tag/Add-Ons
.. _metadata documentation: https://uploadcare.com/api-refs/rest-api/v0.7.0/#tag/File-metadata
.. _file uploader: https://uploadcare.com/products/file-uploader/?utm_source=github&utm_campaign=pyuploadcare
