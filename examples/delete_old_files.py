#!/bin/python

# installation:
# pip install pytz pyuploadcare==2.1.0

import pytz
from datetime import timedelta, datetime
import time
from pyuploadcare import conf
from pyuploadcare.api_resources import FileList, FilesStorage


MAX_LIFETIME = 30  # days
conf.pub_key = 'demopublickey'
conf.secret = 'demoprivatekey'


dt_cutoff = datetime.now(pytz.utc) - timedelta(days=MAX_LIFETIME)


if __name__ == '__main__':

    print 'Selecting files to be deleted...'
    uuid_list = [f.uuid for f in FileList(starting_point=dt_cutoff,
                                          stored=True,
                                          request_limit=500)]
    print 'Batch delete of selected files'
    ts1 = time.time()
    fs = FilesStorage(uuid_list)
    fs.delete()
    ts2 = time.time()
    print 'Operation completed in %f seconds' % (ts2 - ts1)
