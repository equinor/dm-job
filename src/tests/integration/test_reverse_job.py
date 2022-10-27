# type: ignore
import pytest
from starlette.testclient import TestClient

from app import create_app
from services.dmss import add_document_to_path

pytestmark = pytest.mark.integration

test_package = {"type": "system/SIMOS/Package", "name": "JobApiIntegrationTestEntities", "isRoot": True}
test_job = {
    "label": "Example local container job",
    "type": "WorkflowDS/Blueprints/Job",
    "status": "not started",
    "triggeredBy": "me",
    "applicationInput": {
        "name": "whatever",
        "description": "raksO gitS",
        "_id": "f5282220-4a90-4d02-8f34-b82255fc91d5",
        "type": "system/SIMOS/NamedEntity",
    },
    "runner": {"type": "WorkflowDS/Blueprints/ReverseDescription"},
    "started": "Not started",
}
test_client = TestClient(create_app())


class TestReverseDescription:
    def test_starting_and_get_result(self):
        job_document_dmss_id = add_document_to_path("WorkflowDS", test_job, "/JobApiIntegrationTestEntities")
        start_job_response = test_client.post(f"/WorkflowDS/{job_document_dmss_id}").json()
        get_results_response = test_client.get(f"/{start_job_response['uid']}/result")

        assert get_results_response.json()["result"] == ""
