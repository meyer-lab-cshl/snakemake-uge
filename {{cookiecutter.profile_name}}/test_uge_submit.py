import json
import tempfile
import unittest
import math
from io import StringIO
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import patch

from src.CookieCutter import CookieCutter
from src.OSLayer import OSLayer
from src.uge_config import Config
from src.memory_units import Unit, Memory
from src.uge_submit import (
    Submitter,
    QsubInvocationError,
    JobidNotFoundError,
)


class TestSubmitter(unittest.TestCase):
    @patch.object(CookieCutter, "get_log_dir", return_value="logdir")
    @patch.object(CookieCutter, "get_default_mem_mb", return_value=1000)
    @patch.object(CookieCutter, "get_default_threads", return_value=8)
    def test_getter_methods(self, *mocks):
        argv = [
            "script_name",
            "cluster_opt_1",
            "cluster_opt_2",
            "cluster_opt_3",
            "real_jobscript.sh",
        ]
        expected_cluster_cmd = "cluster_opt_1 cluster_opt_2 cluster_opt_3"
        expected_jobscript = "real_jobscript.sh"
        expected_mem = 5
        expected_threads = 4
        expected_per_thread_decimal = round(expected_mem / expected_threads, 2)
        expected_per_thread_final = math.ceil(expected_per_thread_decimal)
        expected_wildcards_str = "i=0"
        expected_rule_name = "search_fasta_on_index"
        expected_jobname = "smk.search_fasta_on_index.i=0"
        expected_logdir = Path("logdir") / expected_rule_name
        expected_resource_cmd = "-pe threads 4 -l h_vmem={mem}G -l m_mem_free={mem}G".format(
                mem=expected_per_thread_final)
        expected_outlog = expected_logdir / "{jobname}.out".format(
            jobname=expected_jobname
        )
        expected_errlog = expected_logdir / "{jobname}.err".format(
            jobname=expected_jobname
        )
        expected_jobinfo_cmd = '-o "{outlog}" -e "{errlog}" -N "{jobname}"'.format(
            outlog=expected_outlog,
            errlog=expected_errlog,
            jobname=expected_jobname,
        )

        uge_submit = Submitter(jobscript=argv[-1], cluster_cmds=argv[1:-1])
        self.assertEqual(uge_submit.jobscript, expected_jobscript)
        self.assertEqual(
            uge_submit.cluster_cmd, expected_cluster_cmd
        )
        self.assertEqual(uge_submit.threads, expected_threads)
        self.assertEqual(uge_submit.mem_mb, Memory(5000, Unit.MEGA))
        self.assertEqual(uge_submit.jobid, "2")
        self.assertEqual(uge_submit.wildcards_str, expected_wildcards_str)
        self.assertEqual(uge_submit.rule_name, expected_rule_name)
        self.assertEqual(uge_submit.is_group_jobtype, False)
        self.assertEqual(uge_submit.resources_cmd, expected_resource_cmd)
        self.assertEqual(uge_submit.jobname, expected_jobname)
        self.assertEqual(uge_submit.logdir, expected_logdir)
        self.assertEqual(uge_submit.outlog, expected_outlog)
        self.assertEqual(uge_submit.errlog, expected_errlog)
        self.assertEqual(
            uge_submit.jobinfo_cmd, expected_jobinfo_cmd,
        )
        self.assertEqual(uge_submit.queue_cmd, "-q q1")
        self.assertEqual(
            uge_submit.submit_cmd,
            "qsub -cwd -pe threads 4 -l h_vmem={mem}G -l m_mem_free={mem}G "
            "{jobinfo} -q q1 cluster_opt_1 cluster_opt_2 cluster_opt_3 "
            "real_jobscript.sh".format(
                mem=expected_per_thread_final, jobinfo=expected_jobinfo_cmd
            ),
        )

    @patch.object(
        OSLayer,
        "run_process",
        return_value=(
            "0",
            (
                "Your job 8697223 is submitted to default queue q1."
                "logs/cluster/2_z137TAmCoQGdWHohm5m2zHH5EruIEJBcQoi.out"
            ),
            "",
        ),
    )
    @patch.object(CookieCutter, "get_log_dir", return_value="logdir")
    @patch.object(CookieCutter, "get_default_mem_mb", return_value=1000)
    @patch.object(CookieCutter, "get_default_threads", return_value=8)
    def test__submit_cmd_and_get_external_job_id_output_stream_from_submit(
        self, *mocks
    ):
        argv = [
            "script_name",
            "cluster_opt_1",
            "cluster_opt_2",
            "cluster_opt_3",
            "real_jobscript.sh",
        ]
        expected = 8697223
        uge_submit = Submitter(jobscript=argv[-1], cluster_cmds=argv[1:-1])
        actual = uge_submit._submit_cmd_and_get_external_job_id()
        self.assertEqual(actual, expected)

    @patch.object(OSLayer, "run_process", return_value=("", "", ""))
    @patch.object(CookieCutter, "get_log_dir", return_value="logdir")
    @patch.object(CookieCutter, "get_default_mem_mb", return_value=1000)
    @patch.object(CookieCutter, "get_default_threads", return_value=8)
    def test_submit_cmd_and_get_external_job_id_output_stream_no_jobid(
        self, *mocks
    ):
        argv = [
            "script_name",
            "cluster_opt_1",
            "cluster_opt_2",
            "cluster_opt_3",
            "real_jobscript.sh",
        ]
        uge_submit = Submitter(jobscript=argv[-1], cluster_cmds=argv[1:-1])
        self.assertRaises(JobidNotFoundError, uge_submit.submit)

    @patch.object(CookieCutter, "get_log_dir", return_value="logdir")
    @patch.object(CookieCutter, "get_default_mem_mb", return_value=1000)
    @patch.object(CookieCutter, "get_default_threads", return_value=8)
    @patch.object(OSLayer, "mkdir")
    @patch.object(OSLayer, "remove_file")
    @patch.object(
            OSLayer,
            "run_process",
            return_value=("0", "Your job 123456 was submitted.", "",),
    )
    @patch.object(OSLayer, "print")
    def test_submit_successfull_submit(
        self,
        print_mock,
        run_process_mock,
        remove_file_mock,
        mkdir_mock,
        *uninteresting_mocks
    ):
        argv = [
            "script_name",
            "cluster_opt_1",
            "cluster_opt_2",
            "cluster_opt_3",
            "real_jobscript.sh",
        ]

        expected_mem = 5
        
        expected_mem = 5
        expected_threads = 4
        expected_per_thread_decimal = round(expected_mem / expected_threads, 2)
        expected_per_thread_final = math.ceil(expected_per_thread_decimal)
        expected_wildcards_str = "i=0"
        expected_rule_name = "search_fasta_on_index"
        expected_jobname = "smk.{rule}.{wc}".format(
            rule=expected_rule_name, wc=expected_wildcards_str
        )
        expected_logdir = Path("logdir") / expected_rule_name
        expected_outlog = expected_logdir / "{jobname}.out".format(
            jobname=expected_jobname
        )
        expected_errlog = expected_logdir / "{jobname}.err".format(
            jobname=expected_jobname
        )
        expected_jobinfo_cmd = (
            '-o "{outlog}" -e "{errlog}" -N "{jobname}"'
        ).format(
            outlog=expected_outlog,
            errlog=expected_errlog,
            jobname=expected_jobname,
        )
        uge_submit = Submitter(jobscript=argv[-1], cluster_cmds=argv[1:-1])
        uge_submit.submit()

        self.assertEqual(remove_file_mock.call_count, 2)
        mkdir_mock.assert_called_once_with(expected_logdir)
        remove_file_mock.assert_any_call(expected_outlog)
        remove_file_mock.assert_any_call(expected_errlog)
        run_process_mock.assert_called_once_with(
            "qsub -cwd -pe threads 4 -l h_vmem={mem}G -l m_mem_free={mem}G "
            "{jobinfo} -q q1 cluster_opt_1 cluster_opt_2 cluster_opt_3 "
            "real_jobscript.sh".format(
                mem=expected_per_thread_final, jobinfo=expected_jobinfo_cmd
            )
        )
        print_mock.assert_called_once_with(
            "123456 {outlog}".format(outlog=expected_outlog)
        )

    @patch.object(CookieCutter, "get_log_dir", return_value="logdir")
    @patch.object(CookieCutter, "get_default_mem_mb", return_value=1000)
    @patch.object(CookieCutter, "get_default_threads", return_value=8)
    @patch.object(OSLayer, "mkdir")
    @patch.object(OSLayer, "remove_file")
    @patch.object(
            OSLayer,
            "run_process",
            side_effect=CalledProcessError(1, "qsub"),
    )
    @patch.object(OSLayer, "print")
    def test_submit_failed_submit_qsub_invocation_error(
        self,
        print_mock,
        run_process_mock,
        remove_file_mock,
        mkdir_mock,
        *uninteresting_mocks
    ):
        argv = [
            "script_name",
            "cluster_opt_1",
            "cluster_opt_2",
            "cluster_opt_3",
            "real_jobscript.sh",
        ]
        uge_submit = Submitter(jobscript=argv[-1], cluster_cmds=argv[1:-1])
        self.assertRaises(QsubInvocationError, uge_submit.submit)

        expected_wildcards_str = "i=0"
        expected_rule_name = "search_fasta_on_index"
        expected_jobname = "smk.{rule}.{wc}".format(
            rule=expected_rule_name, wc=expected_wildcards_str
        )
        expected_logdir = Path("logdir") / uge_submit.rule_name
        mkdir_mock.assert_called_once_with(expected_logdir)
        self.assertEqual(remove_file_mock.call_count, 2)
        expected_outlog = expected_logdir / "{jobname}.out".format(
            jobname=expected_jobname
        )
        expected_errlog = expected_logdir / "{jobname}.err".format(
            jobname=expected_jobname
        )
        remove_file_mock.assert_any_call(expected_outlog)
        remove_file_mock.assert_any_call(expected_errlog)

    @patch.object(CookieCutter, "get_default_queue", return_value="queue")
    def test_get_queue_cmd_returns_cookiecutter_default_if_no_cluster_config(
        self, *mock
    ):
        argv = [
            "script_name",
            "cluster_opt_1",
            "cluster_opt_2",
            "cluster_opt_3",
            "real_jobscript.sh",
        ]
        expected = "-q queue"
        uge_submit = Submitter(jobscript=argv[-1], cluster_cmds=argv[1:-1])
        # sorry, hacky but couldn't figure out how to mock read_job_properties
        del uge_submit._job_properties["cluster"]
        actual = uge_submit.queue_cmd

        self.assertEqual(actual, expected)

    @patch.object(CookieCutter, "get_log_dir", return_value="logdir")
    @patch.object(CookieCutter, "get_default_mem_mb", return_value=1000)
    @patch.object(CookieCutter, "get_default_threads", return_value=8)
    def test_rule_specific_params_are_submitted(self, *mocks):
        argv = [
            "script_name",
            "cluster_opt_1",
            "cluster_opt_2",
            "cluster_opt_3",
            "real_jobscript.sh",
        ]
        content = (
            "__default__:\n  - '-q queue'\n  - '-gpu -'\n"
            "search_fasta_on_index: '-P project'"
        )
        stream = StringIO(content)
        uge_config = Config.from_stream(stream)
        uge_submit = Submitter(
            jobscript=argv[-1],
            cluster_cmds=argv[1:-1],
            uge_config=uge_config,
        )

        expected_wildcards_str = "i=0"
        expected_rule_name = "search_fasta_on_index"
        expected_jobname = "smk.{rule}.{wc}".format(
            rule=expected_rule_name, wc=expected_wildcards_str
        )
        expected_logdir = Path("logdir") / uge_submit.rule_name
        expected_outlog = expected_logdir / "{jobname}.out".format(
            jobname=expected_jobname
        )
        expected_errlog = expected_logdir / "{jobname}.err".format(
            jobname=expected_jobname
        )
        expected_jobinfo_cmd = (
            '-o "{outlog}" -e "{errlog}" -N "{jobname}"'
        ).format(
            outlog=expected_outlog,
            errlog=expected_errlog,
            jobname=expected_jobname,
        )
        expected_mem = 5
        expected_threads = 4
        expected_per_thread_decimal = round(expected_mem / expected_threads, 2)
        expected_per_thread_final = math.ceil(expected_per_thread_decimal)
        expected = (
            "qsub -cwd -pe threads 4 -l h_vmem={mem}G -l m_mem_free={mem}G "

            "{jobinfo} -q q1 cluster_opt_1 cluster_opt_2 cluster_opt_3 "
            "-q queue -gpu - -P project "
            "real_jobscript.sh".format(
                mem=expected_per_thread_final, jobinfo=expected_jobinfo_cmd
            )
        )
        actual = uge_submit.submit_cmd
        assert actual == expected

    def test_rule_name_for_group_returns_groupid_instead(self):
        jobscript = Path(
            tempfile.NamedTemporaryFile(delete=False, suffix=".sh").name
        )
        properties = json.dumps(
            {
                "type": "group",
                "groupid": "mygroup",
                "jobid": "a9722c33-51ba-5ac4-9f17-bab04c68bc3d",
            }
        )
        script_content = "#!/bin/sh\n# properties = {}\necho something".format(
            properties
        )
        jobscript.write_text(script_content)
        uge_submit = Submitter(jobscript=str(jobscript))

        actual = uge_submit.rule_name
        expected = "mygroup"

        assert actual == expected

    def test_is_group_jobtype_when_group_is_present(self):
        jobscript = Path(
            tempfile.NamedTemporaryFile(delete=False, suffix=".sh").name
        )
        properties = json.dumps(
            {
                "type": "group",
                "groupid": "mygroup",
                "jobid": "a9722c33-51ba-5ac4-9f17-bab04c68bc3d",
            }
        )
        script_content = "#!/bin/sh\n# properties = {}\necho something".format(
            properties
        )
        jobscript.write_text(script_content)
        uge_submit = Submitter(jobscript=str(jobscript))

        assert uge_submit.is_group_jobtype

    def test_is_group_jobtype_when_group_is_not_present(self):
        jobscript = Path(
            tempfile.NamedTemporaryFile(delete=False, suffix=".sh").name
        )
        properties = json.dumps(
            {"jobid": "a9722c33-51ba-5ac4-9f17-bab04c68bc3d"}
        )
        script_content = "#!/bin/sh\n# properties = {}\necho something".format(
            properties
        )
        jobscript.write_text(script_content)
        uge_submit = Submitter(jobscript=str(jobscript))

        assert not uge_submit.is_group_jobtype

    def test_jobid_for_group_returns_first_segment_of_uuid(self):
        jobscript = Path(
            tempfile.NamedTemporaryFile(delete=False, suffix=".sh").name
        )
        properties = json.dumps(
            {
                "type": "group",
                "groupid": "mygroup",
                "jobid": "a9722c33-51ba-5ac4-9f17-bab04c68bc3d",
            }
        )
        script_content = "#!/bin/sh\n# properties = {}\necho something".format(
            properties
        )
        jobscript.write_text(script_content)
        uge_submit = Submitter(jobscript=str(jobscript))

        actual = uge_submit.jobid
        expected = "a9722c33"

        assert actual == expected

    def test_jobid_for_non_group_returns_job_number(self):
        jobscript = Path(
            tempfile.NamedTemporaryFile(delete=False, suffix=".sh").name
        )
        properties = json.dumps(
            {
                "type": "single",
                "rule": "search_fasta_on_index",
                "wildcards": {"i": "0"},
                "jobid": 2,
            }
        )
        script_content = "#!/bin/sh\n# properties = {}\necho something".format(
            properties
        )
        jobscript.write_text(script_content)
        uge_submit = Submitter(jobscript=str(jobscript))

        actual = uge_submit.jobid
        expected = "2"

        assert actual == expected

    def test_jobname_for_non_group(self):
        jobscript = Path(
            tempfile.NamedTemporaryFile(delete=False, suffix=".sh").name
        )
        properties = json.dumps(
            {
                "type": "single",
                "rule": "search",
                "wildcards": {"i": "0"},
                "jobid": 2,
            }
        )
        script_content = "#!/bin/sh\n# properties = {}\necho something".format(
            properties
        )
        jobscript.write_text(script_content)
        uge_submit = Submitter(jobscript=str(jobscript))

        actual = uge_submit.jobname
        expected = "smk.search.i=0"

        assert actual == expected

    def test_jobname_for_group(self):
        jobscript = Path(
            tempfile.NamedTemporaryFile(delete=False, suffix=".sh").name
        )
        properties = json.dumps(
            {
                "type": "group",
                "groupid": "mygroup",
                "jobid": "a9722c33-51ba-5ac4-9f17-bab04c68bc3d",
            }
        )
        script_content = "#!/bin/sh\n# properties = {}\necho something".format(
            properties
        )
        jobscript.write_text(script_content)
        uge_submit = Submitter(jobscript=str(jobscript))

        actual = uge_submit.jobname
        expected = "mygroup_a9722c33"

        assert actual == expected


if __name__ == "__main__":
    unittest.main()
