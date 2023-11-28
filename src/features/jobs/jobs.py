from uuid import UUID

from fastapi import APIRouter
from starlette.responses import JSONResponse

from domain_classes.progress import Progress
from features.jobs.use_cases.delete_job import DeleteJobResponse, delete_job_use_case
from features.jobs.use_cases.get_result_job import (
    GetJobResultResponse,
    get_job_result_use_case,
)
from features.jobs.use_cases.start_job import StartJobResponse, start_job_use_case
from features.jobs.use_cases.status_job import StatusJobResponse, status_job_use_case
from features.jobs.use_cases.update_job_progress import (
    UpdateJobProgressResponse,
    update_job_progress_use_case,
)
from restful.responses import create_response

router = APIRouter()


@router.post("/{job_dmss_id:path}", operation_id="start_job", response_model=StartJobResponse)
@create_response(JSONResponse)
def start(job_dmss_id: str):
    """Start a job.

    To start the job, a job handler needs to be implemented for the job entity referenced with 'job_dmss_id'.
    After the job is started, the internal job uid is included in the response. This uid can be used to
    get status, remove the job or get the result.

    - **job_dmss_id**: an address to a job entity stored in DMSS:
       - By id: PROTOCOL://DATA SOURCE/$ID.Attribute
       - By path: PROTOCOL://DATA SOURCE/ROOT PACKAGE/SUB PACKAGE/ENTITY.Attribute

    The PROTOCOL is optional, and the default is dmss.
    """
    return start_job_use_case(job_dmss_id=job_dmss_id).dict()


@router.get("/{job_uid}", operation_id="job_status", response_model=StatusJobResponse)
@create_response(JSONResponse)
def status(job_uid: UUID):
    """Get the status for an existing job.

    - **job_uid**: the job API's internal uid for the job.
    """
    return status_job_use_case(job_id=job_uid).dict()


@router.delete("/{job_uid}", operation_id="remove_job", response_model=DeleteJobResponse)
@create_response(JSONResponse)
def remove(job_uid: UUID):
    """Remove an existing job by calling the remove() function in the job handler for a given job.
    The job will then be deleted from the redis database used for storing jobs.

    - **job_uid**: the job API's internal uid for the job.
    """
    return delete_job_use_case(job_id=job_uid).dict()


@router.get("/{job_uid}/result", operation_id="job_result", response_model=GetJobResultResponse)
@create_response(JSONResponse)
def result(job_uid: UUID):
    """Get the results from a completed job, by calling the result() function in the job handler for a given job.

    - **job_uid**: the job API's internal uid for the job.
    """
    return get_job_result_use_case(job_uid=job_uid).dict()


@router.put("/{job_uid}", operation_id="update_job_progress", response_model=UpdateJobProgressResponse)
@create_response(JSONResponse)
def progress(job_uid: UUID, overwrite_log: bool, job_progress: Progress):
    """Update the progress of the job.

    - **job_uid**: the job API's internal uid for the job.
    - **progress**: progress object with percentage and logs
    """
    return update_job_progress_use_case(job_uid=job_uid, overwrite_log=overwrite_log, progress=job_progress).dict()
