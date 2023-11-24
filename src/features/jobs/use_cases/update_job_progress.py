from uuid import UUID

from pydantic.main import BaseModel

from domain_classes.progress import Progress
from services.job_service import update_progress


class UpdateJobProgressResponse(BaseModel):
    result: str


def update_job_progress_use_case(job_uid: str, overwrite_log, progress: Progress) -> UpdateJobProgressResponse:
    result = update_progress(UUID(job_uid), overwrite_log, progress)
    return UpdateJobProgressResponse(result=result)
