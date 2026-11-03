from datetime import datetime, timedelta, timezone

import pytest

from pyuploadcare.ucare_cli.commands.helpers import parse_datetime


def test_parse_datetime_assumes_utc_without_offset():
    assert parse_datetime("2024-01-02T03:04:05") == datetime(
        2024, 1, 2, 3, 4, 5, tzinfo=timezone.utc
    )


def test_parse_datetime_date_only_is_midnight_utc():
    assert parse_datetime("2024-01-02") == datetime(
        2024, 1, 2, tzinfo=timezone.utc
    )


def test_parse_datetime_keeps_explicit_offset():
    assert parse_datetime("2024-01-02T03:04:05+02:00") == datetime(
        2024, 1, 2, 3, 4, 5, tzinfo=timezone(timedelta(hours=2))
    )


def test_parse_datetime_rejects_garbage():
    with pytest.raises(ValueError):
        parse_datetime("not-a-date")
