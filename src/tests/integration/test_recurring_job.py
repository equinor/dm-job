# type: ignore
import unittest
from time import sleep

from starlette.testclient import TestClient

from app import create_app
from services.dmss import add_document, get_document

application_input = {
    "_id": "1",
    "name": "whatever",
    "description": "sdrawkcaBsIsihT",
    "type": "dmss://system/SIMOS/NamedEntity",
}

test_job = {
    "_id": "myTESTID",
    "label": "Example recurring job",
    "type": "dmss://WorkflowDS/Blueprints/RecurringJob",
    "status": "not started",
    "triggeredBy": "me",
    "applicationInput": {
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
    },
    "runner": {"type": "dmss://WorkflowDS/Blueprints/RecurringJobHandler"},
    "schedule": {
        "type": "dmss://WorkflowDS/Blueprints/CronJob",
        "startDate": "2023-12-21T12:10:00.000+01:00",
        "endDate": "2099-12-21T12:10:00.000+01:00",
        "cron": "1/1 * * * *",
        "runs": [],
    },
}
test_client = TestClient(create_app())


class TestRecurringJob(unittest.TestCase):
    def test_starting_and_get_result(self):
        add_document("dmss://WorkflowDS/TestEntities", application_input)
        job_document_dmss_id = add_document("dmss://WorkflowDS/TestEntities", test_job)
        recurring_job_address = f"dmss://WorkflowDS/${job_document_dmss_id['uid']}"
        start_job_response = test_client.post("/" + recurring_job_address)
        start_job_response.raise_for_status()
        sleep(100)
        first_run = get_document(f"{recurring_job_address}.schedule.runs[0]")
        self.assertEqual("completed", first_run["status"])
        result = test_client.get(f"/{first_run['uid']}/result").json()
        self.assertEqual(result["result"], "ThisIsBackwards")
        self.assertEqual(result["message"], "Done")
