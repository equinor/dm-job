# type: ignore
import json

import pytest
from starlette.testclient import TestClient

from app import create_app
from services.dmss import dmss_api

pytestmark = pytest.mark.integration


test_job = {
    "label": "Example local container job",
    "type": "dmss://WorkflowDS/Blueprints/Job",
    "status": "not started",
    "triggeredBy": "me",
    "applicationInput": {
        "name": "whatever",
        "description": "raksO gitS",
        "_id": "f5282220-4a90-4d02-8f34-b82255fc91d5",
        "type": "dmss://system/SIMOS/NamedEntity",
    },
    "runner": {"type": "dmss://WorkflowDS/Blueprints/ReverseDescription"},
    "started": "Not started",
}
test_client = TestClient(create_app())


class TestReverseDescription:
    def test_starting_and_get_result(self):
        job_document_dmss_id = dmss_api.document_add(
            "dmss://WorkflowDS/TestEntities", json.dumps(test_job), update_uncontained=True
        )
        start_job_response = test_client.post(f"WorkflowDS/${job_document_dmss_id['uid']}")
        start_job_response.raise_for_status()
        get_results_response = test_client.get(f"/{start_job_response.json()['uid']}/result")
        get_results_response.raise_for_status()
        assert get_results_response.json()["result"] == "Stig Oskar"
