#!/bin/python

# installation:
# pip install pytz pyuploadcare~=3.0.0

import time
from datetime import datetime, timedelta

import pytz

from pyuploadcare.client import Uploadcare


MAX_LIFETIME = 10  # days

dt_cutoff = datetime.now(pytz.utc) - timedelta(days=MAX_LIFETIME)


if __name__ == "__main__":

    uploadcare = Uploadcare(
        public_key="demopublickey", secret_key="demosecretkey"
    )

    print("Selecting files to be deleted...")  # noqa: T001
    uuid_list = [
        f.uuid
        for f in uploadcare.list_files(
            starting_point=dt_cutoff,
            ordering="-datetime_uploaded",
            stored=True,
            limit=500,
        )
    ]
    print("Batch delete of selected files", len(uuid_list))  # noqa: T001
    ts1 = time.time()
    uploadcare.delete_files(uuid_list)
    ts2 = time.time()
    print("Operation completed in %f seconds" % (ts2 - ts1))  # noqa: T001
