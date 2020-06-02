# Snakemake UGE profile

[Snakemake profile][profile] for running jobs on a Univa Grid Engine (UGE).
Documentation, Submitter class and helpers heavily based on excellent work by
@mbhall88 for [snakemake-lsf profile][lsf-profile]. Status checker based on 
[Broad-UGER][broad-uger] checker.

[TOC]: #


# Table of Contents
- [Install](#install)
  - [Dependencies](#dependencies)
  - [Profile](#profile)
- [Usage](#usage)
  - [Standard rule-specific cluster resource settings](#standard-rule-specific-cluster-resource-settings)
  - [Non-standard rule-specific cluster resource settings](#non-standard-rule-specific-cluster-resource-settings)

## Install

### Dependencies

This profile is deployed using [Cookiecutter][cookiecutter-repo]. `cookiecutter`
can be installed using `conda` or `pip`:

```bash
pip install --user cookiecutter
# or
conda install -c conda-forge cookiecutter
```

### Profile

To download and set up this profile on your cluster, create a profiles' directory
for snakemake:

```bash
mkdir -p "${HOME}/.config/snakemake"
```

Then use cookiecutter to create the profile in the config directory:
```bash
cookiecutter --output-dir "${HOME}/.config/snakemake"  "gh:meyer-lab-cshl/snakemake-uge"
```

The latter command will then prompt you to set default parameters described in the next two subsections.

### Submission parameters
Parameter explanations as retrieved from `snakemake --help`.

* `latency_wait`

  **Default:** `120`

  This sets the default `--latency-wait/--output-wait/-w` parameter in
  `snakemake`.

  ```text
    --latency-wait SECONDS, --output-wait SECONDS, -w SECONDS
                        Wait given seconds if an output file of a job is not
                        present after the job finished. This helps if your
                        filesystem suffers from latency (default 120).
  ```

* `use_conda`

  **Default**: `True`  
  **Valid options**: `False`, `True`

  This sets the default `--use-conda` parameter in `snakemake`.

  ```text
   --use-conda           If defined in the rule, run job in a conda
                        environment. If this flag is not set, the conda
                        directive is ignored.
  ```


* `use_singularity`

  **Default**: `False`  
  **Valid options**: `False`, `True`

  This sets the default `--use-singularity` parameter in `snakemake`.

  ```text
    --use-singularity     If defined in the rule, run job within a singularity
                        container. If this flag is not set, the singularity
                         directive is ignored.
  ```

* `keep_going`

  **Default**: `True`  
  **Valid options**: `False`, `True`

  This sets the default `--keep-going` parameter in `snakemake`.

  ```text
  --keep-going        Go on with independent jobs if a job fails.
  ```

* `restart_times`

  **Default**: `0`
  
  This sets the default `--restart-times` parameter in `snakemake`.

  ```text
    --restart-times RESTART_TIMES
                        Number of times to restart failing jobs (defaults to
                        0).
  ```

* `jobs`

  **Default**: `500`

  This sets the default `--cores/--jobs/-j` parameter in `snakemake`.

  ```text
    --cores [N], --jobs [N], -j [N]
                        Use at most N cores in parallel. If N is omitted or
                        'all', the limit is set to the number of available
                        cores.
  ```

  In the context of a cluster, `-j` denotes the number of jobs submitted to the
  cluster at the same time<sup>[1][1]</sup>.

* `default_mem_mb`

  **Default**: `1024`

  This sets the default memory, in megabytes, for a `rule` being submitted to the
  cluster without `mem_mb` set under `resources`.

  See [below](#standard-rule-specific-cluster-resource-settings) for how to
  overwrite this in a `rule`.

* `default_threads`

  **Default**: `1`

  This sets the default number of threads for a `rule` being submitted to the
  cluster without the `threads` variable set.

  See [below](#standard-rule-specific-cluster-resource-settings) for how to
  overwrite this in a `rule`.

* `default_cluster_logdir`

  **Default**: `"cluster_logs"`

  This sets the directory under which cluster log files are written. The path is
  relative to the working directory of the pipeline. If it does not exist, it will
  be created.


* `default_queue`

  **Default**: None

  The default queue on the cluster to submit jobs to. If left unset, then the
  default on your cluster will be used.
  The `qsub` parameter that this controls is [`-q`][qsub-q].


* `max_status_checks_per_second`

  **Default**: `10`

  This sets the default `--max-status-checks-per-second` parameter in `snakemake`.

  ```text
    --max-status-checks-per-second MAX_STATUS_CHECKS_PER_SECOND
                        Maximal number of job status checks per second,
                        default is 10, fractions allowed.
  ```

* `max_jobs_per_second`

  **Default**: `10`

  This sets the default `--max-jobs-per-second` parameter in `snakemake`.

  ```text
    --max-jobs-per-second MAX_JOBS_PER_SECOND
                        Maximal number of cluster/drmaa jobs per second,
                        default is 10, fractions allowed.
  ```

* `profile_name`

  **Default**: `uge`

  The name to use for this profile. The directory for the profile is created as
  this name i.e. `$HOME/.config/snakemake/<profile_name>`.
  This is also the value you pass to `snakemake --profile <profile_name>`.

* `print_shell_commands`

  **Default**: `False`
  **Valid options:** `False`, `True`

  This sets the default ` --printshellcmds/-p` parameter in `snakemake`.

  ```text
    --printshellcmds, -p  Print out the shell commands that will be executed.
  ```

### Status check parameters

* `missing_job_wait`

  **Default**: 1

  This set the time elapsed in minutes before a missing job id will be evaluated
  by qacct. If qacct has a status exception, job is considered failed.

* `cpu_hung_min_time`

  **Default**: 1

  This sets the time limit for checking if a job is hung. This is only evaluated if the walltime
  has passed`cpu_hung_min_time` minutes.
  
* `cpu_hung_max_ratio`

  **Default**: 0.01
  
  This sets the parameter determining if a job should be killed. Ff the walltime
  has passed`cpu_hung_min_time` minutes and the ratio of cpu/walltime is below `cpu_hung_max_ratio`,
  the job will be killed.
  
## Usage

Once set up is complete, this will allow you to run snakemake with the cluster
profile using the `--profile` flag. For profile name `uge`, you can run:

```bash
snakemake --profile uge [snakemake options]
```

and pass any other valid snakemake options.

### Standard rule-specific cluster resource settings
The following resources can be specified within a `rule` in the Snakemake file:

- `threads: <INT>` the number of threads needed for the job. If not specified,
    will [default to the amount you set when initialising](#default-threads) the
    profile.
- `resources:`
  - `mem_mb = <INT>`: the memory required for the rule, in megabytes. If not
      specified, will [default to the amount you set when initialising](#default-mem-mb)
      the profile.

*NOTE: these settings will override the profile defaults.*

### Non-standard rule-specific cluster resource settings

Since the [deprecation of cluster configuration files][config-deprecate] the
ability to specify per-rule cluster settings is snakemake-profile-specific.

Per-rule configuration must be placed in a file called `<profile_name>.yaml`
and **must** be located in the working directory for the pipeline. If you set
`workdir` manually within your workflow, the config file has to be in there.

The cluster configuration can provide the following parameters:
* `runtime`: the maximum amount of time the job will be allowed to run for in
minutes
* `queue`: override the default queue for this job.
* `logdir`: override the default cluster log directory for this job.
* `output`: override the default name of stdout logfile
* `error`: override the default name of stderr logfile
* `jobname`: override the default name of the job

***NOTE:*** these settings are highly specific to the UGE cluster system and this profile and
are not guaranteed to be valid on non-UGE cluster systems.

All settings are given with the `rule` name as the key, and the additional
cluster settings as a list ([sequence][yaml-collections]), with the UGe-specific flag followed by
its argument (if applicable).

#### Examples

`Snakefile`

```python
rule grep:
    input: "input.txt"
    output: "output.txt"
    shell:
        "grep 'icecream' {input} > {output}"
        
rule count:
    input: "output.txt"
    output: "output_count.txt"
    shell:
        "wc -l {input} > {output}"
```

`uge.yaml`

```yaml
__default__:
  - "-P "
  - "-W 1:05"

foo:
  - "-P gpu"
  - "-gpu 'gpu resources'"
```

In this example, we specify a default (`__default__`) [project][bsub-P] (`-P`) and
[runtime limit][bsub-W] (`-W`) that will apply to all rules.  
We then override the project and, additionally, specify [GPU resources][bsub-gpu] for
the rule `foo`.

For those interested in the details, this will lead to a submission command, for `foo`
that looks something like

```
$ bsub [options] -P project2 -W 1:05 -P gpu -gpu 'gpu resources' ...
```

Although `-P` is provided twice, LSF uses the last instance.


<!--Link References-->

[lsf-profile]: https://github.com/Snakemake-Profiles/snakemake-lsf
[broad-uger]: https://github.com/broadinstitute/snakemake-broad-uger
[snakemake_params]: https://snakemake.readthedocs.io/en/stable/executing/cli.html#all-options
[cookiecutter-repo]: https://github.com/cookiecutter/cookiecutter
[profile]: https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles
[1]: https://snakemake.readthedocs.io/en/stable/executing/cluster-cloud.html#cluster-execution
[uuid]: https://docs.python.org/3.6/library/uuid.html
[config-deprecate]: https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html#cluster-configuration-deprecated
[yaml-collections]: https://yaml.org/spec/1.2/spec.html#id2759963
[18]: https://github.com/Snakemake-Profiles/snakemake-lsf/issues/18

