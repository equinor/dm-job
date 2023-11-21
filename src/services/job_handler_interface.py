import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Tuple
from uuid import UUID

from pydantic import BaseModel, Field

from services.dmss import get_document


class JobStatus(str, Enum):
    REGISTERED = "registered"
    NOT_STARTED = "not started"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"
    REMOVED = "removed"
    UNKNOWN = "unknown"


class Job(BaseModel):
    class Config:
        json_encoders = {UUID: lambda uuid: str(uuid)}
        allow_population_by_field_name = True

    type: str
    dmss_id: str
    job_uid: UUID = Field(alias="uid")
    name: str | None
    label: str | None
    triggeredBy: str | None
    status: JobStatus
    application_input: dict | None = Field(alias="applicationInput")
    started: datetime | None
    stopped: datetime | None
    ended: datetime | None
    outputTarget: str | None
    result: dict | None
    runner: dict | None
    referenceTarget: str | None
    schedule: dict | None

    log: str | None
    token: str | None
    state: dict | None

    # Fields that are not sendt to DMSS
    exclude_keys: dict = {"dmss_id": True, "log": True, "token": True, "state": True, "exclude_keys": True}

    def dmss_sync(self):
        fetched = get_document(self.dmss_id)
        job_dict = json.loads(self.json())
        merged_kwargs = {
            **fetched,
            "status": job_dict["status"],
            "started": job_dict["started"],
            "stopped": job_dict["stopped"],
        }
        for field, value in merged_kwargs.items():
            setattr(self, field, value)

    def append_log(self, log):
        self.log = f"{self.log}\n{log}"


class JobHandlerInterface(ABC):
    def __init__(self, job: Job, data_source: str):
        self.job = job
        self.data_source = data_source

    @abstractmethod
    def start(self) -> str:
        """Run or deploy a job or job service"""

    def remove(self) -> str:
        """Terminate and cleanup all job related resources"""
        raise NotImplementedError

    def progress(self) -> Tuple[JobStatus, str]:
        """Poll progress from the job instance"""
        raise NotImplementedError

    def result(self) -> Tuple[str, bytes]:
        """Returns a string for free text and the result of the job as a bytearray"""
        raise NotImplementedError

    def setup_service(self, service_id: str) -> str:
        """Start a persistent service"""
        raise NotImplementedError

    def teardown_service(self, service_id: str) -> str:
        """Teardown and cleanup a persistent service"""
        raise NotImplementedError
