import pytest

from services.dmss import dmss_api


def pytest_addoption(parser):
    parser.addoption("--integration", action="store_true", help="run integration tests")


def pytest_runtest_setup(item):
    if "integration" in item.keywords and not item.config.getvalue("integration"):
        pytest.skip("need --integration option to run")


@pytest.fixture(scope="session", autouse=True)
def create_test_root_package():
    test_package = {"type": "dmss://system/SIMOS/Package", "name": "TestEntities", "isRoot": True}
    yield dmss_api.document_add("WorkflowDS", test_package)
    dmss_api.document_remove_by_path("WorkflowDS/TestEntities")
