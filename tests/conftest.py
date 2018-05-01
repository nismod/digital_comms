import pytest
from pytest import fixture

import os

@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))