===========
Project API
===========

The Project API manages the projects of an account: their settings, usage
statistics and content moderation thresholds. It is authorized with an OAuth
access token issued for a user rather than with a project key pair, so it has
its own client. The token gives access to every project the user owns or is a
team member of.

Initialize the client. The token can also be set with the
``UPLOADCARE_OAUTH_TOKEN`` environment variable, the same one ``Uploadcare``
reads::

    from pyuploadcare import ProjectAPIClient

    projects = ProjectAPIClient(token="<access-token>")

Refreshing the token is up to you; pass the new one to the client and the
following requests use it::

    projects.set_access_token("<new-access-token>")

List, count and get projects::

    for project in projects.list_projects(limit=50):
        print(project.pub_key, project.name)

    total: int = projects.count_projects()
    project: Project = projects.get_project("a1dddc498fb8a82c6276")

As with the other list APIs, ``limit`` is the total number of projects to
yield and ``request_limit`` is the page size (1 to 100).

Create a project::

    from pyuploadcare import ProjectFeatures, UploadsFeature

    project = projects.create_project(
        "Production",
        features=ProjectFeatures(uploads=UploadsFeature(autostore=False)),
    )

Update project settings. Updates are partial: only the passed arguments are
changed, and within ``features`` only the fields that were set.
Limits are set in millions: ``filesize_limit_mb`` in megabytes (10^6 bytes)
and ``image_resolution_limit_mp`` in megapixels. Both accept whole integers
(for example, ``filesize_limit_mb=10`` sends 10,000,000 bytes). Responses use
the same MB/MP units. The API's own names, ``filesize_limit`` and
``image_resolution_limit``, are accepted too, in bytes and pixels. An explicit
``None`` for either limit resets it to the plan's value::

    from pyuploadcare import ProjectFeature

    projects.update_project(
        project,
        is_search_index_allowed=True,
        features=ProjectFeatures(
            uploads=UploadsFeature(filesize_limit_mb=None),
            svg_validation=ProjectFeature(is_enabled=True),
        ),
    )

``features`` can be a plain dict of the same shape too. Unknown keys and
invalid values are rejected before a request is made.

The server rejects changes to the features the owner's plan does not include,
so build ``features`` with just the fields to change rather than passing the
one returned by ``get_project()`` back as is.

Configure Adaptive Bitrate Streaming profiles. Sending profiles replaces all
existing ones; omit ``h265`` to remove the H.265 profile::

    from pyuploadcare import (
        AdaptiveBitrateStreamingFeature,
        AdaptiveBitrateStreamingProfile,
        AdaptiveBitrateStreamingProfiles,
    )

    projects.update_project(
        project,
        features=ProjectFeatures(
            adaptive_bitrate_streaming=AdaptiveBitrateStreamingFeature(
                is_enabled=True,
                profiles=AdaptiveBitrateStreamingProfiles(
                    h264=AdaptiveBitrateStreamingProfile(
                        resolutions=["360p", "720p", "1080p"]
                    ),
                ),
            ),
        ),
    )

Delete a project. Only its owner can do this::

    projects.delete_project(project)

Get daily usage. Only complete days of the last 90 days in UTC are available,
so ``date_to`` must be before today. Dates are timezone-aware datetimes, and
only their UTC date is sent. Naive datetimes and plain ``date`` objects are
rejected::

    from datetime import datetime, timezone

    oct_1 = datetime(2026, 10, 1, tzinfo=timezone.utc)
    oct_31 = datetime(2026, 10, 31, tzinfo=timezone.utc)

    usage = projects.get_usage(project, oct_1, oct_31)
    for day in usage.data:
        print(day.date, day.traffic, day.storage, day.operations)

    traffic = projects.get_usage_metric(project, "traffic", oct_1, oct_31)
    print(traffic.unit, [point.value for point in traffic.data])

Manage content moderation thresholds. This requires unsafe content detection
on the owner's plan. Setting thresholds replaces all of them, so an empty list
clears them. Category ids come from ``list_moderation_categories()``::

    from pyuploadcare import ModerationThreshold

    for category in projects.list_moderation_categories():
        print(category.id, category.parent_id, category.level, category.name)

    projects.set_moderation_thresholds(project, [
        ModerationThreshold(category_id=4, threshold_percentage="30.5"),
        {"category_id": 5, "threshold_percentage": "45"},
    ])
    thresholds = projects.get_moderation_thresholds(project)

List MIME types allowed in ``mime_type_filtering``::

    mime_types: List[str] = projects.list_mime_types()
