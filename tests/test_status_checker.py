import unittest
from subprocess import CalledProcessError
from unittest.mock import patch

import pytest
from pathlib import Path
from tests.src.OSLayer import OSLayer
from tests.src.CookieCutter import CookieCutter
from tests.src.uge_status import StatusChecker, QstatError, QacctError, UnknownStatusLine


def assert_called_n_times_with_same_args(mock, n, args):
    assert mock.call_count == n
    mock_args = [a[0] for a,_ in mock.call_args_list]
    for actual, expected in zip(mock_args, args):
        assert actual == expected


class TestStatusChecker(unittest.TestCase):
    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=3)
    @patch.object(OSLayer,
            "run_process",
            return_value=(0, "job_state             1: r", ""))

    def test_get_status_qstat_says_process_is_r_job_status_is_running(
        self, run_process_mock, *othermocks
        ):
        uge_status_checker = StatusChecker(123, "test")
        actual = uge_status_checker.get_status()
        expected = "running"
        self.assertEqual(actual, expected)
        run_process_mock.assert_called_once_with("qstat -j 123")

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=3)
    @patch.object(OSLayer,
            "run_process",
            return_value=(0, "job_state             1: t", ""))
    def test_get_status_qstat_says_process_t_job_status_is_running(
        self, run_process_mock, *othermocks
    ):
        uge_status_checker = StatusChecker(123, "test")
        actual = uge_status_checker.get_status()
        expected = "running"
        self.assertEqual(actual, expected)
        run_process_mock.assert_called_once_with("qstat -j 123")

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=3)
    @patch.object(OSLayer,
            "run_process",
            return_value=(0, "job_state             1: s", ""))
    def test_get_status_qstat_says_process_is_s_job_status_is_running(
        self, run_process_mock, *othermocks
    ):
        uge_status_checker = StatusChecker(123, "test")
        actual = uge_status_checker.get_status()
        expected = "running"
        self.assertEqual(actual, expected)
        run_process_mock.assert_called_once_with("qstat -j 123")

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=3)
    @patch.object(OSLayer,
            "run_process",
            return_value=(0, "job_state             1: R", ""))
    def test_get_status_qstat_says_process_is_R_job_status_is_running(
        self, run_process_mock, *othermocks
    ):
        uge_status_checker = StatusChecker(123, "test")
        actual = uge_status_checker.get_status()
        expected = "running"
        self.assertEqual(actual, expected)
        run_process_mock.assert_called_once_with("qstat -j 123")

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=3)
    @patch.object(OSLayer,
            "run_process",
            return_value=(0, "job_state             1: qw", ""))
    def test_get_status_qstat_says_process_is_qw_job_status_is_running(
        self, run_process_mock, *othermocks
    ):
        uge_status_checker = StatusChecker(123, "test")
        actual = uge_status_checker.get_status()
        print(actual)
        expected = "running"
        self.assertEqual(actual, expected)
        run_process_mock.assert_called_once_with("qstat -j 123")

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=3)
    @patch.object(OSLayer,
            "run_process",
            return_value=(0, "job_state             1: d", ""))
    def test_get_status_qstat_says_process_is_d_job_status_is_failed(
        self, run_process_mock, *othermocks
    ):
        uge_status_checker = StatusChecker(123, "test")
        actual = uge_status_checker.get_status()
        expected = "failed"
        self.assertEqual(actual, expected)
        run_process_mock.assert_called_once_with("qstat -j 123")

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=3)
    @patch.object(OSLayer,
            "run_process",
            return_value=(0, "job_state             1: E", ""))
    def test_get_status_qstat_says_process_is_E_job_status_is_failed(
        self, run_process_mock, *othermocks
    ):
        uge_status_checker = StatusChecker(123, "test")
        actual = uge_status_checker.get_status()
        expected = "failed"
        self.assertEqual(actual, expected)
        run_process_mock.assert_called_once_with("qstat -j 123")

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=3)
    @patch.object(CookieCutter, "get_time_between_qstat_checks", return_value=1)
    @patch.object(OSLayer, "run_process")
    def test_get_status_qstat_fails_twice_succeeds_third_job_status_is_success(
        self, run_process_mock, *othermocks
    ):
        run_process_mock.side_effect = [
            QstatError,
            KeyError("test"),
            (0, "job_state    1: r", "")
        ]
        uge_status_checker = StatusChecker(123, "test")
        actual = uge_status_checker.get_status()
        expected = "running"
        self.assertEqual(actual, expected)
        assert_called_n_times_with_same_args(
            run_process_mock, 3, ["qstat -j 123"] * 3
        )

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=1)
    @patch.object(CookieCutter, "get_time_between_qstat_checks", return_value=1)
    @patch.object(CookieCutter, "get_latency_wait", return_value=45)
    @patch.object(OSLayer, "run_process")
    def test_get_status_qstat_fails_using_qacct_status_is_failure(
        self, run_process_mock, *othermocks
    ):

        run_process_mock.side_effect = [
            QstatError,
            (0, "exit_status 1\nfailed 0", "")
        ]
        uge_status_checker = StatusChecker(123, "dummy")
        actual = uge_status_checker.get_status()
        expected = "failed"
        self.assertEqual(actual, expected)
        assert_called_n_times_with_same_args(
            run_process_mock, 2, ["qstat -j 123", "qacct -j 123"])

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=1)
    @patch.object(CookieCutter, "get_time_between_qstat_checks", return_value=1)
    @patch.object(CookieCutter, "get_latency_wait", return_value=45)
    @patch.object(OSLayer, "run_process")
    def test_get_status_qstat_fails_using_qacct_status_is_success(
        self, run_process_mock, *othermocks
    ):
        run_process_mock.side_effect = [
            QstatError,
            (0, "exit_status 0\nfailed 0", "")
        ]
        uge_status_checker = StatusChecker(123, "dummy")
        actual = uge_status_checker.get_status()
        expected = "success"
        self.assertEqual(actual, expected)
        assert_called_n_times_with_same_args(
            run_process_mock, 2, ["qstat -j 123", "qacct -j 123"])

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=1)
    @patch.object(CookieCutter, "get_time_between_qstat_checks", return_value=1)
    @patch.object(CookieCutter, "get_latency_wait", return_value=45)
    @patch.object(OSLayer,
            "run_process",
            return_value = (1, "", ""))
    def test_get_status_qstat_and_qacct_fail_using_log_job_status_is_success(
        self, run_process_mock, *othermocks
    ):

        uge_status_checker = StatusChecker(123, "test.out")
        actual = uge_status_checker.get_status()
        expected = "success"
        self.assertEqual(actual, expected)
        assert_called_n_times_with_same_args(
            run_process_mock, 2, ["qstat -j 123", "qacct -j 123"])

    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=4)
    @patch.object(OSLayer,
            "run_process",
            return_value=(0, "", ""))
    def test_query_status_using_qstat_empty_stdout_raises_QstatError(
        self, run_process_mock, *othermocks
    ):
        uge_status_checker = StatusChecker(123, "test")
        self.assertRaises(QstatError,
                uge_status_checker._query_status_using_qstat)
        run_process_mock.assert_called_once_with("qstat -j 123")

    @patch.object(CookieCutter, "get_log_dir", return_value="logdir")
    @patch.object(CookieCutter, "get_max_qstat_checks", return_value=1)
    
    @patch.object(CookieCutter, "get_latency_wait", return_value=45)
    @patch.object(CookieCutter, "get_time_between_qstat_checks", return_value=1)
    @patch.object(OSLayer,
            "run_process",
            return_value=(1, "-----------------------------", ""))
    def test_get_status_dashed_status(
        self, run_process_mock, *othermocks
    ):
        expected_rule_name = "search_fasta_on_index"
        expected_jobname = "smk.search_fasta_on_index.0"
        expected_logdir = Path("logdir") / expected_rule_name
        outlog = expected_logdir / "{jobname}.out".format(jobname=expected_jobname)
        uge_status_checker = StatusChecker(123, "test")
        actual = uge_status_checker.get_status()
        expected = "running"
        self.assertEqual(actual, expected)
        run_process_mock.assert_called_with("qacct -j 123")

if __name__ == "__main__":
    unittest.main()
