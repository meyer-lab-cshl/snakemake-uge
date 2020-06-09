class CookieCutter:
    """
    Cookie Cutter wrapper
    """

    @staticmethod
    def get_default_threads() -> int:
        return int("{{cookiecutter.default_threads}}")

    @staticmethod
    def get_default_mem_mb() -> int:
        return int("{{cookiecutter.default_mem_mb}}")

    @staticmethod
    def get_log_dir() -> str:
        return "{{cookiecutter.default_cluster_logdir}}"

    @staticmethod
    def get_default_queue() -> str:
        return "{{cookiecutter.default_queue}}"

    @staticmethod
    def get_log_status_checks() -> bool:
        return "{{cookiecutter.log_status_checks}}" == "True"

    @staticmethod
    def get_latency_wait() -> int:
        return int("{{cookiecutter.latency_wait}}")

    @staticmethod
    def get_max_qstat_checks() -> int:
        return int("{{cookiecutter.max_qstat_checks}}")

    @staticmethod
    def get_time_between_qstat_checks() -> float:
        return float("{{cookiecutter.time_between_qstat_checks}}")


