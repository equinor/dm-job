import json

import pytest

from services.dmss import dmss_api
from services.job_service import get_job_store


def pytest_addoption(parser):
    parser.addoption("--integration", action="store_true", help="run integration tests")


def pytest_runtest_setup(item):
    if "integration" in item.keywords and not item.config.getvalue("integration"):
        pytest.skip("need --integration option to run")


@pytest.fixture(scope="class", autouse=True)
def nuke_job_store():
    redis = get_job_store()
    redis.flushdb()


@pytest.fixture(scope="session", autouse=True)
def create_test_root_package():
    test_package = {"type": "dmss://system/SIMOS/Package", "name": "TestEntities", "isRoot": True, "content": []}
    try:
        dmss_api.document_remove("WorkflowDS/TestEntities")
    except Exception:  # nosec
        pass
    yield dmss_api.document_add("WorkflowDS", json.dumps(test_package))
