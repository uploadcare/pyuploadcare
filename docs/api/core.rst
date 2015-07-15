.. _core_api:

========
Core API
========

You can use pyuploadcare in any Python project. At first you need assign
your project keys to conf object. After that you will be able
to do direct api calls or use api resources::

    >>> import pyuploadcare
    >>> pyuploadcare.conf.pub_key = '<your public key>'
    >>> pyuploadcare.conf.secret = '<your private key>'
    >>> f = pyuploadcare.File('6c5e9526-b0fe-4739-8975-72e8d5ee6342')
    >>> f.cdn_url
    http://www.ucarecdn.com/6c5e9526-b0fe-4739-8975-72e8d5ee6342/


.. _core_api-file-ref:

File API Resource
-----------------

.. autoclass:: pyuploadcare.api_resources.File
   :members:
   :undoc-members:

   .. attribute:: uuid

      File UUID [#uuid]_, e.g. ``a771f854-c2cb-408a-8c36-71af77811f3b``.

   .. attribute:: default_effects

      String of default effects that is used by ``File.cdn_url``, e.g.
      ``effect/flip/-/effect/mirror/``.

.. _core_api-filegroup-ref:

File Group API Resource
-----------------------

.. autoclass:: pyuploadcare.api_resources.FileGroup
   :members:
   :undoc-members:

   .. attribute:: id

      Group id, e.g. ``0513dda0-582f-447d-846f-096e5df9e2bb~2``.


.. _core_api-filelist-ref:

File List API Resource
----------------------

.. autoclass:: pyuploadcare.api_resources.FileList
   :members:
   :undoc-members:

   .. attribute:: since

   .. attribute:: until

   .. attribute:: count

   .. attribute:: stored

   .. attribute:: removed


.. _core_api-grouplist-ref:

Group List API Resource
-----------------------

.. autoclass:: pyuploadcare.api_resources.GroupList
   :members:
   :undoc-members:

   .. attribute:: since

   .. attribute:: until

   .. attribute:: count


.. _core_api-api-ref:

API Clients
-----------

.. automodule:: pyuploadcare.api
   :members:
   :undoc-members:

.. _core_api-exceptions-ref:

Exceptions
----------

.. automodule:: pyuploadcare.exceptions
   :members:
   :undoc-members:

.. [#] Universally unique identifier according to RFC 4122.
