#!/usr/bin/env python3
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Union, Optional

from snakemake.utils import read_job_properties

if not __name__.startswith("tests.src."):
    sys.path.append(str(Path(__file__).parent.absolute()))
    from CookieCutter import CookieCutter
    from OSLayer import OSLayer
    from uge_config import Config
else:
    from .CookieCutter import CookieCutter
    from .OSLayer import OSLayer
    from .uge_config import Config

PathLike = Union[str, Path]

class BsubInvocationError(Exception):
    pass

class JobidNotFoundError(Exception):
    pass

class Submitter:
    def __init__(
        self,
        jobscript: PathLike,
        cluster_cmds: List[str] = None,
        uge_config: Optional[Config] = None,
    ):
        if cluster_cmds is None:
            cluster_cmds = []
        if uge_config is None:
            uge_config = Config()

        self._jobscript = jobscript
        self._cluster_cmd = " ".join(cluster_cmds)
        self._job_properties = read_job_properties(self._jobscript)
        self.uge_config = uge_config

    @property
    def jobscript(self) -> str:
        return self._jobscript

    @property
    def job_properties(self) -> dict:
        return self._job_properties

    @property
    def cluster(self) -> dict:
        return self.job_properties.get("cluster", dict())

    @property
    def threads(self) -> int:
        return self.job_properties.get("threads",
                CookieCutter.get_default_threads())

    @property
    def resources(self) -> dict:
        return self.job_properties.get("resources", dict())

    @property
    def mem_mb(self) -> int:
        mem_value = self.resources.get(
            "mem_mb", self.cluster.get("mem_mb",
                CookieCutter.get_default_mem_mb())
        )
        return int(mem_value)

    @property
    def runtime(self) -> int:
        rt = self.cluster.get("runtime", None)
        if rt:
            rt = int(rt)
        return rt

    @property
    def resources_cmd(self) -> str:
        if self.threads > 1:
            res_cmd = "-pe smp {threads}".format(threads=self.threads)
            per_thread = round(self.mem_mb / self.threads, 2)
        else:
            res_cmd = ""
            per_thread = self.mem_mb
        res_cmd += " -l h_vmem={per_thread}M".format(per_thread=per_thread)
        res_cmd += " -l m_mem_free={per_thread}M".format(per_thread=per_thread)
        if self.runtime:
            hrs = self.runtime // 60
            mins = runtime % 60
            res_cmd += " -l h_rt={hours}:{min}:00".format(hours=hrs, mins=mins)
        return res_cmd

    @property
    def wildcards(self) -> dict:
        return self.job_properties.get("wildcards", dict())

    @property
    def wildcards_str(self) -> str:
        return (
            ".".join("{}={}".format(k, v) for k, v in self.wildcards.items())
            or "unique"
        )

    @property
    def rule_name(self) -> str:
        if not self.is_group_jobtype:
            return self.job_properties.get("rule", "rule_name")
        return self.groupid

    @property
    def groupid(self) -> str:
        return self.job_properties.get("groupid", "group")

    @property
    def is_group_jobtype(self) -> bool:
        return self.job_properties.get("type", "") == "group"

    @property
    def jobname(self) -> str:
        if self.is_group_jobtype:
            return "{groupid}_{jobid}".format(groupid=self.groupid,
                    jobid=self.jobid)
        return self.cluster.get(
            "jobname",
            "smk.{rule_name}.{wildcards_str}".format(
                rule_name=self.rule_name, wildcards_str=self.wildcards_str
            ),
        )

    @property
    def jobid(self) -> str:
        if self.is_group_jobtype:
            return self.job_properties.get("jobid", "").split("-")[0]
        return str(self.job_properties.get("jobid"))

    @property
    def logdir(self) -> Path:
        project_logdir = Path(self.cluster.get("logdir",
            CookieCutter.get_log_dir()))
        return project_logdir / self.rule_name

    @property
    def outlog(self) -> Path:
        if self.is_group_jobtype:
            return self.logdir / "groupid{groupid}_jobid{jobid}.out".format(
                groupid=self.groupid, jobid=self.jobid)
        return self.logdir / "{jobname}.out".format(jobname=self.jobname)

    @property
    def errlog(self) -> Path:
        if self.is_group_jobtype:
            return self.logdir / "groupid{groupid}_jobid{jobid}.err".format(
                groupid=self.groupid, jobid=self.jobid)
        return self.logdir / "{jobname}.err".format(jobname=self.jobname)

    @property
    def jobinfo_cmd(self) -> str:
        return '-o "{out_log}" -e "{err_log}" -N "{jobname}"'.format(
            out_log=self.outlog, err_log=self.errlog, jobname=self.jobname
        )

    @property
    def queue(self) -> str:
        return self.cluster.get("queue", CookieCutter.get_default_queue())

    @property
    def queue_cmd(self) -> str:
        return "-q {}".format(self.queue) if self.queue else ""

    @property
    def rule_specific_params(self) -> str:
        return self.uge_config.params_for_rule(self.rule_name)

    @property
    def cluster_cmd(self) -> str:
        return self._cluster_cmd

    @property
    def submit_cmd(self) -> str:
        params = [
            "qsub -cwd ",
            self.resources_cmd,
            self.jobinfo_cmd,
            self.queue_cmd,
            self.cluster_cmd,
            self.rule_specific_params,
            self.jobscript,
        ]
        return " ".join(p for p in params if p)

    def _create_logdir(self):
        OSLayer.mkdir(self.logdir)

    def _remove_previous_logs(self):
        OSLayer.remove_file(self.outlog)
        OSLayer.remove_file(self.errlog)

    def _submit_cmd_and_get_external_job_id(self) -> int:
        output_stream, error_stream = OSLayer.run_process(self.submit_cmd)
        match = re.search(r"Your job (\d+)", output_stream)
        jobid = match.group(1)
        return int(jobid)

    def _get_parameters_to_status_script(self, external_job_id: int) -> str:
        return "{external_job_id} {outlog}".format(
            external_job_id=external_job_id, outlog=self.outlog
        )

    def submit(self):
        self._create_logdir()
        self._remove_previous_logs()
        try:
            external_job_id = self._submit_cmd_and_get_external_job_id()
            parameters_to_status_script = self._get_parameters_to_status_script(
                external_job_id
            )
            OSLayer.print(parameters_to_status_script)
        except subprocess.CalledProcessError as error:
            raise BsubInvocationError(error)
        except AttributeError as error:
            raise JobidNotFoundError(error)


if __name__ == "__main__":
    workdir = Path().resolve()
    config_file = workdir / "uge.yaml"
    if config_file.exists():
        with config_file.open() as stream:
            uge_config = Config.from_stream(stream)
    else:
        uge_config = Config()

    jobscript = sys.argv[-1]
    cluster_cmds = sys.argv[1:-1]
    uge_submit = Submitter(
        jobscript=jobscript,
        uge_config=uge_config,
        cluster_cmds=cluster_cmds,
    )
    uge_submit.submit()
