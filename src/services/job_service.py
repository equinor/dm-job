import importlib
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable, Tuple, Union
from uuid import UUID, uuid4

import redis
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from redis import AuthenticationError

from config import config
from restful.exceptions import (
    BadRequestException,
    NotFoundException,
    NotImplementedException,
)
from services.dmss import (
    get_document_by_uid,
    get_personal_access_token,
    update_document_by_uid,
)

# TODO: Authorization. The only level of authorization at this point is to allow all that
#  can view the job entity to also run and delete the job.
from services.job_handler_interface import Job, JobHandlerInterface, JobStatus
from services.job_scheduler import scheduler
from utils.logging import logger
from utils.string_helpers import split_address


def schedule_cron_job(scheduler: BackgroundScheduler, function: Callable, job: Job) -> str:
    """Schedule a cron job.

    A cron job is a job that is run on a schedule. For example at 16:00 every Thursday.
    The cron syntax from unix is used to define when the job should run.
    For example: "30 12 * * 3" means that the job should run at 12:30 on Wednesday.

    It is assumed that the 'job' parameter contains an entity with a 'cron' string attibute that follows the cron syntax.
    """
    if not job.entity.get("schedule"):
        raise ValueError("CronJob entity is missing required attribute 'schedule'")
    try:
        minute, hour, day, month, day_of_week = job.entity["cron"].split(" ")
        scheduled_job = scheduler.add_job(
            function,
            "cron",
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
            id=str(job.job_uid),
            replace_existing=True,
        )
        return (
            "Cron job successfully registered. Next scheduled run "
            + f"at {scheduled_job.next_run_time} {scheduled_job.next_run_time.tzinfo}"
        )
    except ValueError as e:
        raise ValueError(f"Failed to schedule cron job '{job.job_uid}'. {e}'")


class JobService:
    """
    Service for working with jobs.
    The job service is responsible for job operations like registering jobs, starting jobs, removing jobs, etc.
    """

    def __init__(self):
        """Set up Redis database for storing jobs."""
        # TODO should move the job store out of the job service to separate responsibilities
        self.job_store = redis.Redis(
            host=config.SCHEDULER_REDIS_HOST,
            port=config.SCHEDULER_REDIS_PORT,
            db=0,
            password=config.SCHEDULER_REDIS_PASSWORD,
            ssl=config.SCHEDULER_REDIS_SSL,
            socket_timeout=5,
            socket_connect_timeout=5,
        )

    def load_cron_jobs(self):
        for key in self.job_store.scan_iter():
            job = self._get_job(UUID(key.decode()))
            if job.cron_job:
                schedule_cron_job(scheduler, lambda: self._run_job(job.job_uid), job)
                logger.info(f"Loaded and registered job '{job.job_uid}' from {config.SCHEDULER_REDIS_HOST}")

    def _set_job(self, job: Job):
        return self.job_store.set(str(job.job_uid), json.dumps(job.to_dict()))

    def _get_job(self, job_uid: UUID) -> Union[Job, None]:
        """Get a job from the job storage."""
        try:
            if raw_job := self.job_store.get(str(job_uid)):
                return Job.from_dict(json.loads(raw_job.decode()))
        except AuthenticationError:
            raise ValueError(
                "Tried to fetch a job from Redis but no password"
                + " was supplied. Make sure SCHEDULER_REDIS_PASSWORD is set."
            )
        return None

    @staticmethod
    def _get_job_entity(dmss_id: str, token: str | None = None):
        """Get a document from DMSS.

        The dmss_id can be on the formats:
          - By id: PROTOCOL://DATA SOURCE/$ID.Attribute
          - By path: PROTOCOL://DATA SOURCE/ROOT PACKAGE/SUB PACKAGE/ENTITY.Attribute
        """
        protocol, data_source_id, job_entity_id, attribute = split_address(dmss_id)
        return get_document_by_uid(
            reference=f"{data_source_id}/{job_entity_id}.{attribute}", token=token, depth=1, resolve_links=False
        )

    @staticmethod
    def _insert_reference(document_id: str, reference: dict, token: str = ""):  # nosec
        """Insert a reference into an existing entity stored in dmss.

        - **document_id**: the address to the entity we want to update. Can be on the formats:
          - By id: PROTOCOL://DATA SOURCE/$ID.Attribute
          - By path: PROTOCOL://DATA SOURCE/ROOT PACKAGE/SUB PACKAGE/ENTITY.Attribute

        - **reference**: an entity of type 'dmss://system/SIMOS/Reference' to be inserted.
        """
        headers = {"Access-Key": token}
        # TODO use document update instead, the reference insert endpoint has been removed from DMSS
        req = requests.put(
            f"{config.DMSS_API}/api/reference/{document_id}",
            json=reference,
            headers=headers,
            timeout=10,
        )
        req.raise_for_status()

        return req.json()

    @staticmethod
    def _update_job_entity(dmss_id: str, job_entity: dict, token: str | None):
        """Update a job entity in dmss.

        - **dmss_id**: the address to the job entity we want to update. Can be on the formats:
          - By id: PROTOCOL://DATA SOURCE/$ID.Attribute
          - By path: PROTOCOL://DATA SOURCE/ROOT PACKAGE/SUB PACKAGE/ENTITY.Attribute

        - **job_entity**: the new job entity.
        """
        return update_document_by_uid(dmss_id, {"data": job_entity}, token=token)

    def _get_job_handler(self, job: Job) -> JobHandlerInterface:
        """Get the job handler for a job.

        Job handlers must be placed in the "default_job_handlers" or the "job_handler_plugins" folder in the
        repository src folder.
        Each job handler have a folder with at least one file: __init__.py
        This __init__ file must implement a class called "JobHandler" that inherits from the JobHandlerInterface class.

        The runner type in the job entity (job.entity["runner"]["type"]) decides what job handler to fetch.
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
                if job.entity["runner"]["type"] == job_handler_module._SUPPORTED_TYPE:
                    return job_handler_module.JobHandler(job, data_source_id)
        except ImportError as error:
            traceback.print_exc()
            raise ImportError(
                f"Failed to import a job handler module: '{error}'"
                + "Make sure the module has a '_init_.py' file, a 'JobHandler' class implementing "
                + "the JobHandlerInterface, and a global variable named '_SUPPORTED_TYPE' "
                + "with the string, tuple, or list value of the job type(s)."
            )

        raise NotImplementedError(f"No handler for a job of type '{job.entity['runner']['type']}' is configured")

    def _run_job(self, job_uid: UUID) -> str:
        """Start a job, by calling the start() function for the job's job handler."""
        job: Job = self._get_job(job_uid)
        if not job:
            raise NotFoundException(
                message=f"The job with uid '{job_uid}' was not found",
                debug=f"The job with uid '{job_uid}' was not found",
            )
        try:
            job_handler = self._get_job_handler(job)
            job.started = datetime.now()
            job.status = JobStatus.STARTING
            try:
                job.log = job_handler.start()
            except Exception as error:
                print(traceback.format_exc())
                logger.warning(f"Failed to run job; {job_uid}")
                job.status = JobStatus.FAILED
                raise error
        except NotImplementedError as error:
            job.log = (
                f"{job.log}\n\nThe jobHandler '{type(job_handler).__name__}' is missing some implementations: {error}"
            )
        except KeyError as error:
            job.log = (
                f"{job.log}\n\nThe jobHandler '{type(job_handler).__name__}' "
                f"tried to access a missing attribute: {error}"
            )
        except Exception as error:
            job.log = f"{job.log}\n\n{error}"
        finally:
            job.update_entity_attributes()
            self._update_job_entity(job.dmss_id, job.entity, job.token)  # Update in DMSS with status etc.
            self._set_job(job)
            return job.log  # type: ignore

    def register_job(self, dmss_id: str) -> Tuple[str, str]:
        """Register and start a job.

        Create an instance of the Job class from a job entity stored in DMSS, and start running the job.

        - **dmss_id**: address to the job entity to register. Can be on the formats:
          - By id: PROTOCOL://DATA SOURCE/$ID.Attribute
          - By path: PROTOCOL://DATA SOURCE/ROOT PACKAGE/SUB PACKAGE/ENTITY.Attribute
        """
        # A token must be created when there still is a request object.
        token = get_personal_access_token()
        job_entity = self._get_job_entity(dmss_id, token)

        # if False:  # TODO: Reimplement cron-job support
        if job_entity.get("schedule"):
            job = Job(
                job_uid=uuid4(),
                dmss_id=dmss_id,
                started=datetime.now(),
                status=JobStatus.REGISTERED,
                entity=job_entity,
                cron_job=True,
                token=token,
            )
            self._get_job_handler(job)  # Test for available handler before registering
            result = str(job.job_uid), schedule_cron_job(scheduler, lambda: self._run_job(job.job_uid), job)
        else:
            job = Job(
                job_uid=uuid4(),
                dmss_id=dmss_id,
                started=datetime.now(),
                status=JobStatus.REGISTERED,
                entity=job_entity,
                token=token,
            )
            self._get_job_handler(job)
            scheduler.add_job(lambda: self._run_job(job.job_uid))
            result = str(job.job_uid), "Job successfully started"

        self._set_job(job)
        job.update_entity_attributes()
        self._update_job_entity(job.dmss_id, job.entity, job.token)
        return result

    def status_job(self, job_uid: UUID) -> Tuple[JobStatus, str, str]:
        """Get the status for an existing job.

        The result of the job is fetched by using the progress() function in the job handler for the given job.
        """
        job = self._get_job(job_uid)
        if not job:
            raise NotFoundException(f"No job with uid '{job_uid}' is registered")
        job_handler = self._get_job_handler(job)
        try:
            status, log = job_handler.progress()
        except NotImplementedError:
            raise NotImplementedException(
                message="The job handler does not support the operation",
                debug="The job handler does not implement the 'progress' method",
            )
        job_entity = self._get_job_entity(job.dmss_id, job.token)
        if status is JobStatus.COMPLETED and job_entity.get("results", None):
            result_reference = job_entity["result"]
            job.entity["result"] = result_reference
        job.status = status
        job.log = log
        self._set_job(job)
        job.update_entity_attributes()
        self._update_job_entity(job.dmss_id, job.entity, job.token)
        if job.cron_job:
            cron_job = scheduler.get_job(job_uid)
            return status, job.log, f"Next scheduled run @ {cron_job.next_run_time} {cron_job.next_run_time.tzinfo}"
        return status, job.log, f"Started: {job.started.isoformat()}"

    def remove_job(self, job_uid: UUID) -> str:
        """Remove an existing job.

        The remove() function in the job's job handler is used.
        Also, the job is removed from the job store.
        """
        job = self._get_job(job_uid)
        if not job:
            raise NotFoundException(f"No job with id '{job_uid}' is registered")
        job_handler = self._get_job_handler(job)
        try:
            remove_message = job_handler.remove()
        except NotImplementedError:
            raise NotImplementedException(
                message="The job handler does not support the operation",
                debug="The job handler does not implement the 'remove' method",
            )
        self.job_store.delete(str(job_uid))
        return remove_message  # type: ignore

    def get_job_result(self, job_uid: UUID) -> Tuple[str, bytes]:
        """Get result from an existing job.

        The result() function in the job's job handler is used.
        """
        job = self._get_job(job_uid)
        if not job:
            raise NotFoundException(f"No job with id '{job_uid}' is registered")
        if not job.status.COMPLETED:
            raise BadRequestException("The job has not yet completed")
        job_handler = self._get_job_handler(job)
        try:
            return job_handler.result()  # type: ignore
        except NotImplementedError:
            raise NotImplementedException(
                message="The job handler does not support the operation",
                debug="The job handler does not implement the 'result' method",
            )
