#!/bin/python

# installation:
# pip install pytz pyuploadcare~=3.0.0

import time
from datetime import datetime, timedelta

import pytz

from pyuploadcare import File, FileList, conf


MAX_LIFETIME = 10  # days
conf.pub_key = "demopublickey"
conf.secret = "demoprivatekey"


dt_cutoff = datetime.now(pytz.utc) - timedelta(days=MAX_LIFETIME)


if __name__ == "__main__":

    print("Selecting files to be deleted...")  # noqa: T001
    uuid_list = [
        f.uuid
        for f in FileList(
            starting_point=dt_cutoff,
            ordering="-datetime_uploaded",
            stored=True,
            limit=500,
        )
    ]
    print("Batch delete of selected files", len(uuid_list))  # noqa: T001
    ts1 = time.time()
    File.batch_delete(uuid_list)
    ts2 = time.time()
    print("Operation completed in %f seconds" % (ts2 - ts1))  # noqa: T001
