import os
import pytest

# 👉 SI ESTÁS EN CI → skip total de E2E
if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
    pytest.skip("Skipping E2E tests in CI", allow_module_level=True)


from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@pytest.fixture
def driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


@pytest.fixture
def base_url(live_server):
    return live_server.url