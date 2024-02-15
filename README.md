# Snakemake UGE profile

The repository provides a [Snakemake profile][profile] for running jobs on a Univa Grid Engine (UGE).
It is heavily based on the excellent [snakemake-lsf profile][lsf-profile].

After installation and set-up of this profile (described in detail below), snakemake can be run on a UGE
with the simple command:

```bash
snakemake --profile uge [snakemake options]
```

The profile takes care of job submission and status checks. Rule specific parameters can be provided in a separate
.yaml file provided in the working directory (see [Examples](#examples)).

**Note**: For pipelines consisting of many jobs with short excution times (less than or a few minutes), we recommend running snakemake in single node mode i.e. a single multicore UGE interactive job on one node. In these pipelines, the overall run time could be dominated by UGE queueing/processing time. For pipelines with longer job runtimes and/or very different memory/cpu requirements per rule, using the profile described in this repository is recommended. 


[TOC]: #


# Table of Contents
- [Install](#install)
  - [Dependencies](#dependencies)
  - [Profile](#profile)
    - [Submission parameters](#submission-parameters)
    - [Status check parameters](#status-check-parameters)
- [Usage](#usage)
  - [Standard rule-specific cluster resource settings](#standard-rule-specific-cluster-resource-settings)
  - [Non-standard rule-specific cluster resource settings](#non-standard-rule-specific-cluster-resource-settings)
- [Examples](#examples)

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

The latter command will prompt you to set default parameters described in
the next two subsections. Each parameter has default settings and simply
pressing enter at the prompt will choose the default setting of that parameter
for the profile.

#### Submission parameters
Parameter explanations as retrieved from `snakemake --help`.

* `latency_wait`

  **Default:** `45`

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

  This sets the default memory, in megabytes, for a `rule` being submitted to
  the cluster without `mem_mb` set under `resources`.

  See [below](#standard-rule-specific-cluster-resource-settings) for how to
  overwrite this in a `rule`.

* `default_threads`

  **Default**: `1`

  This sets the default number of threads for a `rule` being submitted to the
  cluster without the `threads` variable set.

  See [below](#standard-rule-specific-cluster-resource-settings) for how to
  overwrite this in a `rule`.

  *NOTE: The submission script takes care of converting the threads and memory specified in MegaByte*
  *per rule into a memory request "per thread" in GigaByte.*
  
* `default_cluster_logdir`

  **Default**: `"cluster_logs"`

  This sets the directory under which cluster log files are written. The path is
  relative to the working directory of the pipeline. If it does not exist, it
  will be created.


* `default_queue`

  **Default**: None

  The default queue on the cluster to submit jobs to. If left unset, then the
  default on your cluster will be used.
  The `qsub` parameter that this controls is [`-q`][qsub-q].

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

#### Status check parameters
The status check parameters dsecribed [here](UGE_parameters.md) should not be changed unless discussed with IT.
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
    profile. As stated in the [snakemake manual][threads], it should be noted
    that the specified threads have to be seen as a maximum. When Snakemake is
    executed with fewer cores, the number of threads will be adjusted.

- `resources:`
  - `mem_mb = <INT>`: the memory required for the rule, in megabytes. If not
      specified, will
      [default to the amount you set when initialising](#default-mem-mb) the
      profile. For details on memory specification see the snakemake
      documentation on [resources][resources].

*NOTE: these settings within the snakemake rules will override the
profile defaults.*

### Non-standard rule-specific cluster resource settings

Since the [deprecation of cluster configuration files][config-deprecate] the
ability to specify per-rule cluster settings is snakemake-profile-specific.

Per-rule configuration must be placed in a file called `<profile_name>.yaml`
and **must** be located in the working directory for the pipeline. If you set
`workdir` manually within your workflow, the config file has to be in there.

Common parameters that can be provided to the cluster configuration (for
details check `man qsub`):

* `runtime`: the maximum amount of time the job will be allowed to run for
  
  ```text
    -l h_rt={runtime_hr}:{runtime_min}:00
  ```

* `queue`: override the default queue for this job.
  
  ```text
    -q QUEUENAME
  ```

* `output`: override the default name of stdout logfile
  
  ```text
    -o path/to/file/for/output_stream
  ```

* `error`: override the default name of stderr logfile
  
  ```text
    -o path/to/file/for/output_stream
  ```

* `jobname`: override the default name of the job

  ```text
    -N JOBNAME
  ```
* `project`:  Specifies the project to which this job is assigned to

  ```text
    -P PROJECTNAME
  ```
***NOTE:*** these settings are highly specific to the UGE cluster system and
this profile and are not guaranteed to be valid on non-UGE cluster systems.

All settings are given with the `rule` name as the key, and the additional
cluster settings as a list ([sequence][yaml-collections]), with the UGE-specific
flag followed by its argument (if applicable).

***NOTE:*** Directory paths should not be used as wildcards. If a directory is
used as a wildcard, any "/" will be replaced with "-". 

### Examples

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
  - "-P standard "
  - "-l h_rt=01:00:00"

grep:
  - "-P icecream "
  - "-N icecream.search"
```

In this example, we specify a default (`__default__`) project (`-P`)
and runtime limit (`-l h_rt=01:00:00 `) that will apply to all rules.
We then override the project and, additionally, specify a new job name for
the rule `grep`. This will lead to a submission command, for `grep`
that looks something like

```
$ qsub [options] -P standard -l h_rt=01:00:00 -P icecream -N icecream.search ...
```

Although `-P` is provided twice, UGE uses the last instance.


<!--Link References-->

[lsf-profile]: https://github.com/Snakemake-Profiles/snakemake-lsf
[snakemake_params]: https://snakemake.readthedocs.io/en/stable/executing/cli.html#all-options
[cookiecutter-repo]: https://github.com/cookiecutter/cookiecutter
[profile]: https://snakemake.readthedocs.io/en/stable/executing/cli.html#profiles
[threads]: https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#threads
[resources]: https://snakemake.readthedocs.io/en/stable/snakefiles/rules.html#resources
[1]: https://snakemake.readthedocs.io/en/stable/executing/cli.html#cluster-execution
[config-deprecate]: https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html#cluster-configuration-deprecated
[yaml-collections]: https://yaml.org/spec/1.2/spec.html#id2759963

