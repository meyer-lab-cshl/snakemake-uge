# Snakemake UGE profile

[Snakemake profile][profile] for running jobs on an [UGE][uge] cluster.

[TOC]: #


# Table of Contents
- [Install](#install)
  - [Dependencies](#dependencies)
  - [Profile](#profile)
- [Usage](#usage)
  - [Standard rule-specific cluster resource settings](#standard-rule-specific-cluster-resource-settings)
  - [Non-standard rule-specific cluster resource settings](#non-standard-rule-specific-cluster-resource-settings)
- [Known Issues](#known-issues)
- [Contributing](#contributing)


## Install

### Dependencies

This profile is deployed using [Cookiecutter][cookiecutter-repo]. `cookiecutter`
can be easily installed using `conda` or `pip`:

```bash
pip install --user cookiecutter
# or
conda install -c conda-forge cookiecutter
```

### Profile

Download and set up the profile on your cluster

```bash
# create profiles directory for snakemake
dir_profiles="${HOME}/.config/snakemake"
mkdir -p "$dir_profiles"
# use cookiecutter to create the profile in the config directory
template="gh:Snakemake-Profiles/snakemake-uge"
cookiecutter --output-dir "$dir_profiles" "$template"
```

The latter command will then prompt you to set default parameters (parameter
explanations from `snakemake --help`) :

#### `latency_wait`

**Default:** `5`

This sets the default `--latency-wait/--output-wait/-w` parameter in
`snakemake`.

```text
  --latency-wait SECONDS, --output-wait SECONDS, -w SECONDS
                        Wait given seconds if an output file of a job is not
                        present after the job finished. This helps if your
                        filesystem suffers from latency (default 5).
```

#### `use_conda`

**Default**: `False`  
**Valid options:** `False`, `True`

This sets the default `--use-conda` parameter in `snakemake`.

```text
  --use-conda           If defined in the rule, run job in a conda
                        environment. If this flag is not set, the conda
                        directive is ignored.
```


#### `use_singularity`
**Default**: `False`
**Valid options:** `False`, `True`

This sets the default `--use-singularity` parameter in `snakemake`.

```text
  --use-singularity     If defined in the rule, run job within a singularity
                        container. If this flag is not set, the singularity
                        directive is ignored.
```

#### `keep_going`

**Default**: `False`
**Valid options:** `False`, `True`

This sets the default `--keep-going` parameter in `snakemake`.

```text
--keep-going        Go on with independent jobs if a job fails.
```

#### `restart_times`

**Default**: `0`

This sets the default `--restart-times` parameter in `snakemake`.

```text
  --restart-times RESTART_TIMES
                        Number of times to restart failing jobs (defaults to
                        0).
```

#### `jobs`

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

#### `default_mem_mb`

**Default**: `1024`

This sets the default memory, in megabytes, for a `rule` being submitted to the
cluster without `mem_mb` set under `resources`.

See [below](#standard-rule-specific-cluster-resource-settings) for how to
overwrite this in a `rule`.

#### `default_threads`

**Default**: `1`

This sets the default number of threads for a `rule` being submitted to the
cluster without the `threads` variable set.

See [below](#standard-rule-specific-cluster-resource-settings) for how to
overwrite this in a `rule`.

#### `missing_job_wait`
#### `default_cluster_logdir`

**Default**: `"logs/cluster"`

This sets the directory under which cluster log files are written. The path is
relative to the working directory of the pipeline. If it does not exist, it will
be created.


#### `default_queue`

**Default**: None

The default queue on the cluster to submit jobs to. If left unset, then the
default on your cluster will be used.
The `bsub` parameter that this controls is [`-q`][bsub-q].


#### `max_status_checks_per_second`

**Default**: `10`

This sets the default `--max-status-checks-per-second` parameter in `snakemake`.

```text
  --max-status-checks-per-second MAX_STATUS_CHECKS_PER_SECOND
                        Maximal number of job status checks per second,
                        default is 10, fractions allowed.
```

#### `max_jobs_per_second`

**Default**: `10`

This sets the default `--max-jobs-per-second` parameter in `snakemake`.

```text
  --max-jobs-per-second MAX_JOBS_PER_SECOND
                        Maximal number of cluster/drmaa jobs per second,
                        default is 10, fractions allowed.
```

#### `profile_name`

**Default**: `uge`

The name to use for this profile. The directory for the profile is created as
this name i.e. `$HOME/.config/snakemake/<profile_name>`.
This is also the value you pass to `snakemake --profile <profile_name>`.



#### `print_shell_commands`

**Default**: `False`
**Valid options:** `False`, `True`

This sets the default ` --printshellcmds/-p` parameter in `snakemake`.

```text
  --printshellcmds, -p  Print out the shell commands that will be executed.
```

## Usage

Once set up is complete, this will allow you to run snakemake with the cluster
profile using the `--profile` flag. For profile name was `uge`, you can run:

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

A cluster configuration can be provided to specify additional information:
+ `mem_mb`: the memory that will be requested for the rule in megabytes.
  Overriden by `resources.mem_mb`. If neither provided, use a default value (in
  cookiecutter configuration).
+ `runtime`: the maximum amount of time the job will be allowed to run for in
  minutes
+ `queue`: override the default queue for this job.
+ `logdir`: override the default cluster log directory for this job.
+ `output`: override the default name of stdout logfile
+ `error`: override the default name of stderr logfile
+ `jobname`: override the default name of the job


***NOTE:*** these settings are only valid for this profile and are not guaranteed
to be valid on non-UGE cluster systems.

All settings are given with the `rule` name as the key, and the additional
cluster settings as a string ([scalar][yaml-collections]) or list
([sequence][yaml-collections]).

#### Examples

`Snakefile`

```python
rule foo:
    input: "foo.txt"
    output: "bar.txt"
    shell:
        "grep 'bar' {input} > {output}"
        
rule bar:
    input: "bar.txt"
    output: "file.out"
    shell:
        "echo blah > {output}"
```

`lsf.yaml`

```yaml
__default__:
  - "-P project2"
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

```yaml
__default__: "-P project2 -W 1:05"

foo: "-P gpu -gpu 'gpu resources'"
```

The above is also a valid form of the previous example but **not recommended**.


## Contributing

Please refer to [`CONTRIBUTING.md`](CONTRIBUTING.md).

<!--Link References-->

[leandro]: https://github.com/leoisl
[snakemake_params]: https://snakemake.readthedocs.io/en/stable/executing/cli.html#all-options
[profile]: https://snakemake.readthedocs.io/en/stable/executable.html#profiles
[1]: https://snakemake.readthedocs.io/en/stable/executing/cluster-cloud.html#cluster-execution
[uuid]: https://docs.python.org/3.6/library/uuid.html
[config-deprecate]: https://snakemake.readthedocs.io/en/stable/snakefiles/configuration.html#cluster-configuration-deprecated
[yaml-collections]: https://yaml.org/spec/1.2/spec.html#id2759963
[18]: https://github.com/Snakemake-Profiles/snakemake-lsf/issues/18

