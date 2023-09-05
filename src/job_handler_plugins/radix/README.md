# Radix job

See [official documentation](https://www.radix.equinor.com/guides/jobs/job-manager-and-job-api.html).

The Radix job handler communicated with the job manager (also named job scheduler) to create, delete and monitor the state of jobs. 

Radix creates one job-scheduler per job defined in radixconfig.yaml.

> **Job manager not exposed to the internet:**: The job-scheduler API can only be accessed by components running in the same environment, and it is not exposed to the Internet. No authentication is required.