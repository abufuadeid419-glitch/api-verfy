import pytest
import requests


CONVEX_SITE = "https://fearless-ostrich-878.eu-west-1.convex.site"
API = f"{CONVEX_SITE}/api"


@pytest.fixture
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture
def base_url():
    return API
