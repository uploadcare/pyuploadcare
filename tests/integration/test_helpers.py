import math
import uuid
from collections.abc import Iterable
from itertools import chain

import pytest

from pyuploadcare.helpers import iterate_over_batches


TEST_COLLECTION_LENGTH = 10


@pytest.fixture()
def uuid_collection() -> Iterable[list[uuid.UUID]]:
    yield [uuid.uuid4() for _ in range(TEST_COLLECTION_LENGTH)]


@pytest.fixture()
def str_collection(
    uuid_collection: Iterable[list[uuid.UUID]],
) -> Iterable[list[str]]:
    yield list(map(str, uuid_collection))


@pytest.mark.parametrize("batch_size", (3, 4, TEST_COLLECTION_LENGTH, 20))
def test_batcher(str_collection, batch_size):
    pieces = list(iterate_over_batches(str_collection, batch_size))

    assert len(pieces) == math.ceil(len(str_collection) / batch_size)
    assert list(chain(*pieces)) == str_collection
