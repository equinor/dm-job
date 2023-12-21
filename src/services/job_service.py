from __future__ import annotations

import importlib
import json
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Tuple
from uuid import UUID, uuid4

import redis
from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler
from redis import AuthenticationError

from config import config
from domain_classes.progress import Progress
from restful.exceptions import (
    BadRequestException,
    NotFoundException,
    NotImplementedException,
)
from services.dmss import get_document, get_personal_access_token, update_document

# TODO: Authorization. The only level of authorization at this point is to allow all that
#  can view the job entity to also run and delete the job.
from services.job_handler_interface import (
    Job,
    JobHandlerInterface,
    JobStatus,
    dmss_sync,
)
from services.job_scheduler import scheduler
from utils.logging import logger


def get_job_store():
    return redis.Redis(
        host=config.SCHEDULER_REDIS_HOST,
        port=config.SCHEDULER_REDIS_PORT,
        db=0,
        password=config.SCHEDULER_REDIS_PASSWORD,
        ssl=config.SCHEDULER_REDIS_SSL,
        socket_timeout=5,
        socket_connect_timeout=5,
    )


def schedule_cron_job(job_scheduler: BackgroundScheduler, function: Callable, job: Job) -> str:
    """Schedule a cron job.

    A cron job is a job that is run on a schedule. For example at 16:00 every Thursday.
    The cron syntax from unix is used to define when the job should run.
    For example: "30 12 * * 3" means that the job should run at 12:30 on Wednesday.

    It is assumed that the 'job' parameter contains an entity with a 'cron' string attribute that follows the cron syntax.
    """
    if not job.schedule:
        raise ValueError("CronJob entity is missing required attribute 'schedule'")
    try:
        minute, hour, day, month, day_of_week = job.schedule["cron"].replace("  ", " ").split(" ")
        scheduled_job = job_scheduler.add_job(
            trigger="cron",
            func=function,
            args=[str(job.job_uid)],
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=str(job.job_uid),
            replace_existing=True,
            jobstore="redis_job_store",
        )
        return (
            "Cron job successfully registered. Next scheduled run "
            + f"at {scheduled_job.next_run_time - datetime.now(timezone.utc) + datetime.fromisoformat(job.schedule['startDate'])} {scheduled_job.next_run_time.tzinfo}"
        )
    except ValueError as e:
        raise BadRequestException(message=f"Failed to schedule cron job '{job.job_uid}'.", debug=str(e))


def _get_job(job_uid: UUID) -> Job:
    """Get a job from the job storage."""
    try:
        if raw_job := get_job_store().get(str(job_uid)):
            return Job(**json.loads(raw_job.decode()))
        else:
            raise NotFoundException(f"No job with id '{job_uid}' is registered")
    except AuthenticationError:
        raise ValueError(
            "Tried to fetch a job from Redis but no password"
            + " was supplied. Make sure SCHEDULER_REDIS_PASSWORD is set."
        )


def _set_job(job: Job):
    # If we don't include an empty exclude dict, 'token' will be removed from the json string...
    return get_job_store().set(str(job.job_uid), job.json(exclude={}))


def load_cron_jobs():
    for key in get_job_store().scan_iter():
        job = _get_job(UUID(key.decode()))
        if job.schedule:
            schedule_cron_job(scheduler, _run_job, job)
            logger.info(f"Loaded and registered job '{job.job_uid}' from {config.SCHEDULER_REDIS_HOST}")


def _get_job_handler(job: Job) -> JobHandlerInterface:
    """Get the job handler for a job.

    Job handlers must be placed in the "default_job_handlers" or the "job_handler_plugins" folder in the
    repository src folder.
    Each job handler have a folder with at least one file: __init__.py
    This __init__ file must implement a class called "JobHandler" that inherits from the JobHandlerInterface class.

    The runner type in the job entity (job.runner["type"]) decides what job handler to fetch.
    Also, the runner type must be equal to the '_SUPPORTED_TYPE' inside the job handler's __init__ file.
    """
    data_source_id = job.dmss_id.split("/", 1)[0]  # TODO use split_absolute_ref() to do this splitting.

    job_handler_directories = []
    for handler_location in ("default_job_handlers", "job_handler_plugins"):
        for file in Path(handler_location).iterdir():
            if file.is_dir() and file.name[0] != "_":  # Python modules can not start with "_"
                job_handler_directories.append(str(file).replace("/", "."))

    try:
        modules = [importlib.import_module(module) for module in job_handler_directories]
        for job_handler_module in modules:
            if job.runner["type"] == job_handler_module._SUPPORTED_TYPE:
                return job_handler_module.JobHandler(job, data_source_id)
    except ImportError as error:
        traceback.print_exc()
        raise ImportError(
            f"Failed to import a job handler module: '{error}'"
            + "Make sure the module has a '_init_.py' file, a 'JobHandler' class implementing "
            + "the JobHandlerInterface, and a global variable named '_SUPPORTED_TYPE' "
            + "with the string, tuple, or list value of the job type(s)."
        )

    raise NotImplementedError(f"No handler for a job of type '{job.runner['type']}' is configured")


def _run_job(job_uid: UUID) -> str:
    """Start a job, by calling the start() function for the job's job handler."""
    job: Job = _get_job(job_uid)
    message: list[str] | str = ""
    try:
        job_handler = _get_job_handler(job)
        job.started = datetime.now().replace(microsecond=0)
        try:
            message = job_handler.start()

        except Exception as error:
            print(traceback.format_exc())
            logger.warning(f"Failed to run job; {job_uid}")
            job.set_job_status(JobStatus.FAILED)
            raise error
    except NotImplementedError as error:
        message = f"The jobHandler '{type(job_handler).__name__}' is missing some implementations: {error}"
    except KeyError as error:
        message = f"The jobHandler '{type(job_handler).__name__}' " f"tried to access a missing attribute: {error}"
    except Exception as error:
        message = str(error)
    finally:
        if job.type == config.RECURRING_JOB:
            # The recurring job has been updated within the JobHandler
            # Fetch the updated entity before merging data
            job = dmss_sync(job)
        job.append_log(message)
        update_document(
            job.dmss_id, job.json(by_alias=True, exclude_none=True, exclude=job.exclude_keys), job.token
        )  # Update in DMSS with status etc.

        _set_job(job)
        return message  # type: ignore


def register_job(dmss_id: str, token: str | None = None) -> Tuple[str, str, JobStatus]:
    """Register and start a job.

    Create an instance of the Job class from a job entity stored in DMSS, and start running the job.

    - **dmss_id**: address to the job entity to register. Can be on the formats:
      - By id: PROTOCOL://DATA SOURCE/$ID.Attribute
      - By path: PROTOCOL://DATA SOURCE/ROOT PACKAGE/SUB PACKAGE/ENTITY.Attribute
    - **token**: optional access token for dmss. Must be passed if there is no HTTP
        request context to get a token from (e.g. when the job api itself is creating a scheduled job
    """

    # A token must be created when there still is a request object.
    token = token if token else get_personal_access_token()
    job_entity = get_document(dmss_id, 0, token)
    kwargs = {
        **job_entity,
        "dmss_id": dmss_id,
        "started": datetime.now().replace(microsecond=0),
        "token": token,
        "uid": uuid4(),
    }
    job = Job(**kwargs)
    _get_job_handler(job)  # Test for available handler before registering
    if job_entity.get("schedule"):
        job.set_job_status(JobStatus.REGISTERED)
        schedule_response = schedule_cron_job(
            scheduler,
            _run_job,
            job,
        )
    else:
        # Add a 5second delay on every job we run.
        # This is so that the JobService can update job state in
        # DMSS, before we get a race with the job itself trying to update it's state.
        in_5_seconds = datetime.now() + timedelta(seconds=5)
        job.set_job_status(JobStatus.STARTING)
        scheduled_job = scheduler.add_job(
            func=_run_job,
            next_run_time=in_5_seconds,
            args=[job.job_uid],
            jobstore="redis_job_store",
            id=str(job.job_uid),
        )
        schedule_response = (
            f"Job starting in 5 seconds: {scheduled_job.next_run_time} {scheduled_job.next_run_time.tzinfo}"
        )

    job.append_log(schedule_response)
    result = str(job.job_uid), schedule_response, job.status

    _set_job(job)
    update_document(job.dmss_id, job.json(by_alias=True, exclude_none=True, exclude=job.exclude_keys), token=job.token)
    return result


def status_job(job_uid: UUID) -> Tuple[JobStatus, list[str], float]:
    """Get the status for an existing job.

    The result of the job is fetched by using the progress() function in the job handler for the given job.
    Return the logs and status which the job pushed (external progress tracking), if the job implements 'update_job_progress'.
    If the job does not implement progress tracking, the job handler tries to evaluate the status of the job.
    """
    job = _get_job(job_uid)
    job_handler = _get_job_handler(job)
    if job.external_progress:
        return job.status, job.log, job.percentage
    try:
        status, log, percentage = job_handler.progress()
    except NotImplementedError:
        raise NotImplementedException(
            message="The job handler does not support the operation",
            debug="The job handler does not implement the 'progress' method",
        )
    if job.schedule:
        job = dmss_sync(job)  # New runs might have been added and/or updated since last sync
    updated_job = Job(
        **update_progress(job, progress=Progress(status=status, logs=log, percentage=percentage), overwrite_log=True)
    )
    return updated_job.status, updated_job.log, updated_job.percentage


def remove_job(job_uid: UUID) -> Tuple[str, str]:
    """Remove an existing job.

    The remove() function in the job's job handler is used.
    Also, the job is removed from the job store.
    """
    job = _get_job(job_uid)
    job_handler = _get_job_handler(job)
    try:
        job_status, remove_message = job_handler.remove()
        job.set_job_status(job_status)
        update_document(job.dmss_id, job.json(by_alias=True, exclude_none=True, exclude=job.exclude_keys), job.token)
        get_job_store().delete(str(job_uid))
    except NotImplementedError:
        remove_message = "The job handler does not support the operation"
    try:
        scheduler.remove_job(str(job_uid))
    except JobLookupError:
        pass
    job.append_log(remove_message)
    return job.status, remove_message  # type: ignore


def get_job_result(job_uid: UUID) -> Tuple[str, bytes]:
    """Get result from an existing job.

    The result() function in the job's job handler is used.
    """
    job = _get_job(job_uid)
    if not job.status.COMPLETED:
        raise BadRequestException("The job has not yet completed")
    job_handler = _get_job_handler(job)
    try:
        result, result_bytes = job_handler.result()  # type: ignore
        job.append_log(result)
        return result, result_bytes
    except NotImplementedError:
        raise NotImplementedException(
            message="The job handler does not support the operation",
            debug="The job handler does not implement the 'result' method",
        )


def update_progress_from_uid(job_uid: UUID, progress: Progress, overwrite_log: bool, external: bool):
    job = _get_job(job_uid)
    if job.schedule:
        job = dmss_sync(job)
    return update_progress(job, progress, overwrite_log, external)


def update_progress(job: Job, progress: Progress, overwrite_log: bool, external: bool = False) -> dict:
    job.external_progress = external or job.external_progress
    if progress.percentage is not None:
        job.percentage = progress.percentage
    if progress.logs:
        if overwrite_log:
            job.log = progress.logs if isinstance(progress.logs, list) else [progress.logs]
        else:
            job.append_log(progress.logs)
    if progress.status:
        job.set_job_status(progress.status)
    _set_job(job)
    update_document(
        job.dmss_id,
        job.json(
            by_alias=True,
            exclude_none=True,
            exclude=job.exclude_keys,
        ),
        job.token,
    )
    return dict(json.loads(job.json()))
