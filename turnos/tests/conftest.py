import pytest

@pytest.fixture
def driver():
    return None

@pytest.fixture
def base_url(live_server):
    return live_server.url