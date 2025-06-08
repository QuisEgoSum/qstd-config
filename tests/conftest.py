import os

import pytest


@pytest.fixture(autouse=True)
def clear_env():
    orig = os.environ.copy()

    yield

    os.environ.clear()
    os.environ.update(orig)
