from abc import ABC, abstractmethod
from datetime import datetime, timezone
from enum import Enum
from typing import Tuple
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    model_config = ConfigDict(populate_by_name=True)

    type: str
    dmss_id: str
    job_uid: UUID = Field(alias="uid")
    name: str | None = None
    label: str | None = None
    triggeredBy: str | None = None
    status: JobStatus = JobStatus.NOT_STARTED
    application_input: dict | None = Field(default=None, alias="applicationInput")
    started: datetime | None = None
    ended: datetime | None = None
    outputTarget: str | None = None
    result: dict | None = None
    runner: dict | None = None
    referenceTarget: str | None = None
    schedule: dict | None = None

    log: list | None = []
    percentage: float | None = None
    token: str | None = None
    state: dict | None = None
    external_progress: bool = False

    # Fields that are not sendt to DMSS
    exclude_keys: dict = {
        "dmss_id": True,
        "log": True,
        "percentage": True,
        "token": True,  # nosec B105
        "state": True,
        "external_progress": True,
        "exclude_keys": True,
    }

    def append_log(self, log: list | str):
        if not isinstance(log, list):
            logs = log.split("\n")
            log = [line for line in logs if line]
        if self.log:
            self.log.extend(log)
            return

        self.log = log

    def set_job_status(self, status: JobStatus):
        if status == self.status:
            return
        self.status = status
        match status:
            case JobStatus.COMPLETED | JobStatus.FAILED:
                self.ended = datetime.now(timezone.utc).replace(microsecond=0)


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
    fetched: dict = get_document(job.dmss_id, 0, job.token)
    job_dict = job.model_dump(mode="json")
    merged_kwargs: dict = {
        **fetched,
        "status": job_dict["status"],
        "started": job_dict["started"],
        "dmss_id": job.dmss_id,
    }
    new_job = Job.model_validate(merged_kwargs)
    # For some reason, "token" does not survive the exporting and parsing...
    new_job.token = job.token
    return new_job
