from uuid import UUID

from pydantic.main import BaseModel

from domain_classes.progress import Progress
from services.job_service import update_progress_from_uid


class UpdateJobProgressResponse(BaseModel):
    response: str


def update_job_progress_use_case(job_uid: UUID, overwrite_log, progress: Progress) -> UpdateJobProgressResponse:
    update_progress_from_uid(job_uid, progress, overwrite_log, True)
    return UpdateJobProgressResponse(response="OK")
