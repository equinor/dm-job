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
    ended: datetime | None
    outputTarget: str | None
    result: dict | None
    runner: dict | None
    referenceTarget: str | None
    schedule: dict | None

    log: list | None = []
    percentage: float | None
    token: str | None
    state: dict | None
    external_progress: bool = False

    # Fields that are not sendt to DMSS
    exclude_keys: dict = {
        "dmss_id": True,
        "log": True,
        "percentage": True,
        "token": True,
        "state": True,
        "external_progress": True,
        "exclude_keys": True,
    }

    def append_log(self, log: list | str):
        if not isinstance(log, list):
            logs = log.split("\n")
            log = [f"JOBAPI: {log}" for log in logs]
        if self.log:
            self.log.extend(log)
        else:
            self.log = log

    def set_job_status(self, status: JobStatus):
        if status == self.status:
            return
        self.status = status
        match status:
            case JobStatus.COMPLETED | JobStatus.FAILED:
                self.ended = datetime.now().replace(microsecond=0)


class JobHandlerInterface(ABC):
    def __init__(self, job: Job, data_source: str):
        self.job = job
        self.data_source = data_source

    @abstractmethod
    def start(self) -> str:
        """Run or deploy a job or job service"""

    def remove(self) -> Tuple[JobStatus, str]:
        """Terminate and cleanup all job related resources"""
        raise NotImplementedError

    def progress(self) -> Tuple[JobStatus, None | list[str] | str, None | float]:
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


def dmss_sync(job: Job) -> Job:
    fetched: dict = get_document(job.dmss_id)
    job_dict = json.loads(job.json())
    merged_kwargs: dict = {
        **fetched,
        "status": job_dict["status"],
        "started": job_dict["started"],
        "dmss_id": job.dmss_id,
    }
    return Job.parse_obj(merged_kwargs)
