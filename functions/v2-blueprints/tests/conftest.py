from aioresponses import aioresponses
import pytest


@pytest.fixture
def aioresponse():
    with aioresponses() as m:
        yield m