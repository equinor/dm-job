from uuid import UUID

from pydantic import BaseModel

from services.job_handler_interface import JobStatus
from services.job_service import status_job


class StatusJobResponse(BaseModel):
    status: JobStatus
    log: str | None
    message: str

    class Config:
        use_enum_values = True


def status_job_use_case(job_id: str) -> StatusJobResponse:
    status, log, message = status_job(UUID(job_id))
    return StatusJobResponse(**{"status": status.value, "log": log, "message": message})
