from pydantic.main import BaseModel

from services.job_handler_interface import JobStatus


class Progress(BaseModel):
    percentage: float | None
    logs: list[str] | str | None
    status: JobStatus | None
