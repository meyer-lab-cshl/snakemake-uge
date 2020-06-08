#!/usr/bin/env python3

import sys
import time
import re
from pathlib import Path

if not __name__.startswith("tests.src."):
    sys.path.append(str(Path(__file__).parent.absolute()))
    from OSLayer import OSLayer
else:
    from .OSLayer import OSLayer


class QstatError(Exception):
    pass


class QacctError(Exception):
    pass


class UnknownStatusLine(Exception):
    pass


class StatusChecker:
    SUCCESS = "success"
    RUNNING = "running"
    FAILED = "failed"
    STATUS_TABLE = {
        "r": RUNNING,
        "x": RUNNING,
        "t": RUNNING,
        "s": RUNNING,
        "R": RUNNING,
        "qw": RUNNING,
        "d": FAILED,
        "E": FAILED,
        "FAIL": FAILED,
        "EXIT_STATUS: 1": FAILED,
        "SUCCESS": SUCCESS,
        "EXIT_STATUS: 0": SUCCESS,
    }

    """
    From man qstat:
        the  status  of  the  job  -  one  of  d(eletion),  E(rror), h(old),
        r(unning), R(estarted), s(uspended),  S(uspended),  e(N)hanced  sus-
        pended, (P)reempted, t(ransfering), T(hreshold) or w(aiting).

    """

    def __init__(
        self,
        jobid: int,
        outlog: str,
        wait_between_tries: float = 0.001,
        max_status_checks: int = 3,
    ):
        self._jobid = jobid
        self._outlog = outlog
        self.wait_between_tries = wait_between_tries
        self.max_status_checks = max_status_checks

    @property
    def jobid(self) -> int:
        return self._jobid

    @property
    def outlog(self) -> str:
        return self._outlog

    @property
    def qstat_query_cmd(self) -> str:
        return "qstat -j {jobid}".format(jobid=self.jobid)

    @property
    def qacct_query_cmd(self) -> str:
        return "qacct -j {jobid}".format(jobid=self.jobid)

    @property
    def qdel_cmd(self) -> str:
        return "qdel -j {jobid}".format(jobid=self.jobid)

    def _query_status_using_qstat(self) -> str:
        returncode, output_stream, error_stream = OSLayer.run_process(
            self.qstat_query_cmd
        )
        if str(returncode) != 0:
            raise QstatError(
                "qstat failed on job {jobid} with {returncode}".format(
                    jobid=self.jobid, returncode=returncode
                )
            )
        status = self._qstat_job_state(output_stream)
        if status not in self.STATUS_TABLE.keys():
            raise KeyError(
                "[Predicted exception] Unknown job status "
                "{status} for {jobid}".format(status=status, jobid=self.jobid)
            )
        return self.STATUS_TABLE[status]

        # hung_status = self._handle_hung_qstat(output_stream)
        # if hung_status or self._qstat_error(output_stream):
        #    status = "failed"
        # else:
        #    status = "running"

    def _query_status_using_qacct(self) -> str:
        returncode, output_stream, error_stream = OSLayer.run_process(
            self.qacct_query_cmd
        )

        if str(returncode) != 0:
            raise QacctError(
                "qacct failed on job {jobid} with {returncode}".format(
                    jobid=self.jobid, returncode=returncode
                )
            )

        status = self._qacct_job_state(output_stream)
        if status not in self.STATUS_TABLE.keys():
            raise KeyError(
                "[Predicted exception] Unknown job status "
                "{status} for {jobid}".format(status=status, jobid=self.jobid)
            )
        return self.STATUS_TABLE[status]

    def _query_status_using_cluster_log(self) -> str:
        try:
            lastline = OSLayer.tail(self.outlog, num_lines=1)
        except (FileNotFoundError, ValueError):
            return self.STATUS_TABLE["r"]

        status = lastline[0].strip().decode("utf-8")
        if status not in self.STATUS_TABLE.keys():
            raise UnknownStatusLine(
                "[Predicted exception] Unknown job status "
                "{status} for {jobid}".format(status=status, jobid=self.jobid)
            )
        return self.STATUS_TABLE[status]

    @staticmethod
    def _extract_time(line, time_name) -> float:
        """ Extracts time elapsed in seconds from usage line for given name
        """
        result = re.search(f"{time_name}=([^,]+)(,|$,\n)", line)
        if not result:
            return 0
        time_str = re.search(f"{time_name}=([^,]+)(,|$,\n)", line).group(1)
        elapsed_time = 0
        multiplier = 1
        multipliers = (1, 60, 60, 24)
        for t, m in zip(reversed(time_str.split(":")), multipliers):
            elapsed_time += multiplier * m * int(t)
            multiplier *= m
        return elapsed_time

    @staticmethod
    def _qstat_job_state(output_stream) -> str:
        state = ""
        for line in output_stream.split("\n"):
            if line.startswith("job_state"):
                state = line.strip()[-1]
                break  # exit for loop
        return state

    @staticmethod
    def _qacct_job_state(output_stream) -> str:
        exit_state = ""
        failed = ""
        for line in output_stream.split("\n"):
            if line.startswith("failed"):
                failed = line.strip()[-1]
            if line.startswith("exit_status"):
                exit_state = line.strip()[-1]
            if failed != "" and exit_state != "":
                break
        if failed == "0" and exit_state == "0":
            return "SUCCESS"
        else:
            return "FAIL"

    def _handle_hung_qstat(self, output_stream) -> str:
        for line in output_stream.split("\n"):
            if line.startswith("usage"):
                wallclock = self._extract_time(line, "wallclock")
                if wallclock < self.cpu_hung_min_time * 60:
                    return False
                cpu = self._extract_time(line, "cpu")
                if (cpu / wallclock) < self.cpu_hung_max_ratio:
                    (
                        returncode,
                        output_stream,
                        error_stream,
                    ) = OSLayer.run_process(self.qdel_cmd)
                    return True
                return False
            return False

    def get_status(self) -> str:
        status = None
        for _ in range(self.max_status_checks):
            try:
                status = self._query_status_using_qstat()
                break  # succeeded on getting the status
            except QstatError as error:
                print(
                    "[Predicted exception] QstatError: {error}".format(
                        error=error
                    ),
                    file=sys.stderr,
                )
                print("Resuming...", file=sys.stderr)
                time.sleep(self.wait_between_tries)

            except KeyError as error:
                print(
                    "[Predicted exception] Unknown job status: {error}".format(
                        error=error
                    ),
                    file=sys.stderr,
                )
                print("Resuming...", file=sys.stderr)
                time.sleep(self.wait_between_tries)

        if status is None:
            print(
                "qstat checks failed {try_times} times.".format(
                    try_times=self.max_status_checks
                ),
                file=sys.stderr,
            )
            print("Checking via qacct...", file=sys.stderr)
            try:
                status = self._query_status_using_qacct()
            except QacctError as error:
                print(
                    "[Predicted exception] QacctError: {error}".format(
                        error=error
                    ),
                    file=sys.stderr,
                )

            except KeyError as error:
                print(
                    "[Predicted exception] Unknown job status: {error}".format(
                        error=error
                    ),
                    file=sys.stderr,
                )

        if status is None:
            print(
                "qacct check failed. Checking via cluster log...",
                file=sys.stderr,
            )
            status = self._query_status_using_cluster_log()

        return status


if __name__ == "__main__":
    jobid = int(sys.argv[1])
    outlog = sys.argv[2]
    uge_status_checker = StatusChecker(jobid, outlog)
    try:
        print(uge_status_checker.get_status())
    except KeyboardInterrupt:
        sys.exit(0)
