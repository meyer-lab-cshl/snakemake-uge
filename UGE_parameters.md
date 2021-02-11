#### Status check parameters
The status check parameters dsecribed below should not be changed unless discussed with IT.
The compute cluster is a shared resource and running workflow managers like snakemake submitting large amounts
of jobs and high frequency status checks can slow down the compute environment for everyone. Should issues
occur with this profile and job status checks by snakemake,
for instance `snakemake.exceptions.WorkflowError: Failed to obtain job status.` errors, it is
recommended to set `log_status_checks` to True to track the issues.

* `log_status_checks`

  **Default**: False  

  When set, status check tries and exceptions are printed to stderr. Recommended
  to set to True for issues with status checks by snakemake, e.g.
  `snakemake.exceptions.WorkflowError: Failed to obtain job status.` errors.
  * `max_qstat_checks`

  **Default**: 3  

  This sets the maximum number of times `qstat -j JOBID` is invoked to determine
  the current status of the job. If `qstat` fails because the job has
  finished or if qstat has been called unsuccessfully for `max_qstat_checks`
  times, then the job exit status will be determined via `qacct -j JOBID`.

 * `max_status_checks_per_second`

  **Default**: `0.017`

  This sets the default `--max-status-checks-per-second` parameter in
  `snakemake`; effectively, this default means a status check per minute.

  ```text
    --max-status-checks-per-second MAX_STATUS_CHECKS_PER_SECOND
                        Maximal number of job status checks per second,
                        default is 10, fractions allowed.
  ```

* `time_between_qstat_checks`

  **Default**: 60  

  This sets the times in seconds to wait between job status checks via
  `qstat -j jobid`; see `max_qstat_checks` above; 

* `max_jobs_per_second`

  **Default**: `1`

  This sets the default `--max-jobs-per-second` parameter in `snakemake`.

  ```text
    --max-jobs-per-second MAX_JOBS_PER_SECOND
                        Maximal number of cluster/drmaa jobs per second,
                        default is 10, fractions allowed.
  ```
