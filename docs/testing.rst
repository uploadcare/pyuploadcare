.. _testing:

=======
Testing
=======

To run tests using `Github Actions`_ workflows, but locally, install the `act`_ utility, and then run it:

.. code-block:: console

    make test-with-github-actions

This runs the full suite of tests across Python and Django versions.

.. _Github Actions: https://github.com/uploadcare/pyuploadcare/actions
.. _act: https://github.com/nektos/act
