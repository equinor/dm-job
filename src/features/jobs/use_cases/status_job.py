from uuid import UUID

from pydantic import BaseModel

from services.job_handler_interface import JobStatus
from services.job_service import status_job


class StatusJobResponse(BaseModel):
    status: JobStatus
    log: list[str] | None
    percentage: float | None

    class Config:
        use_enum_values = True


def status_job_use_case(job_id: UUID) -> StatusJobResponse:
    status, log, percentage = status_job(job_id)
    return StatusJobResponse(status=status, log=log, percentage=percentage)
