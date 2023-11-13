# type: ignore
import unittest
from time import sleep

from starlette.testclient import TestClient

from app import create_app
from services.dmss import add_document

application_input = {
    "_id": "2",
    "name": "SomethingElseByTheKinks",
    "description": "sdrawkcaBsIsihT",
    "type": "dmss://system/SIMOS/NamedEntity",
}

test_job = {
    "label": "Example local container job",
    "type": "dmss://WorkflowDS/Blueprints/Job",
    "status": "not started",
    "triggeredBy": "me",
    "applicationInput": {
        "address": "dmss://WorkflowDS/$2",
        "type": "dmss://system/SIMOS/Reference",
        "referenceType": "link",
    },
    "runner": {"type": "dmss://WorkflowDS/Blueprints/ReverseDescription"},
}
test_client = TestClient(create_app())


class TestReverseDescription(unittest.TestCase):
    def test_starting_and_get_result(self):
        add_document("dmss://WorkflowDS/TestEntities", application_input)
        job_document_dmss_id = add_document("dmss://WorkflowDS/TestEntities", test_job)
        start_job_response = test_client.post(f"WorkflowDS/${job_document_dmss_id['uid']}")
        start_job_response.raise_for_status()
        sleep(8)  # Let the job run...
        get_results_response = test_client.get(f"/{start_job_response.json()['uid']}/result")
        get_results_response.raise_for_status()
        assert get_results_response.json()["result"] == "ThisIsBackwards"
