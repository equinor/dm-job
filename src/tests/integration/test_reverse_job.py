# type: ignore
import json
import unittest

from starlette.testclient import TestClient

from app import create_app
from services.dmss import dmss_api

application_input = {
    "_id": "1",
    "name": "whatever",
    "description": "raksO gitS",
    "type": "dmss://system/SIMOS/NamedEntity",
}

test_job = {
    "label": "Example local container job",
    "type": "dmss://WorkflowDS/Blueprints/Job",
    "status": "not started",
    "triggeredBy": "me",
    "applicationInput": {
        "address": "dmss://WorkflowDS/$1",
        "type": "dmss://system/SIMOS/Reference",
        "referenceType": "link",
    },
    "runner": {"type": "dmss://WorkflowDS/Blueprints/ReverseDescription"},
    "started": "Not started",
}
test_client = TestClient(create_app())


class TestReverseDescription(unittest.TestCase):
    def test_starting_and_get_result(self):
        dmss_api.document_add(
            "dmss://WorkflowDS/TestEntities", json.dumps(application_input), update_uncontained=False
        )
        job_document_dmss_id = dmss_api.document_add(
            "dmss://WorkflowDS/TestEntities", json.dumps(test_job), update_uncontained=False
        )
        start_job_response = test_client.post(f"WorkflowDS/${job_document_dmss_id['uid']}")
        start_job_response.raise_for_status()
        get_results_response = test_client.get(f"/{start_job_response.json()['uid']}/result")
        get_results_response.raise_for_status()
        assert get_results_response.json()["result"] == "Stig Oskar"
