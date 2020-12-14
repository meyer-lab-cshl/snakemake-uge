#!/bin/sh
# properties = {"type": "single", "rule": "search_fasta_on_index", "local": false, "input": ["/hps/nobackup/research/zi/leandro/fasta.txt", "/hps/nobackup/research/zi/config.txt"], "output": ["output/result"], "wildcards": {"i": "0"}, "params": {"threshold": 1.0, "cache_mem_gb": 2}, "log": ["logs/search_fasta.0.log"], "threads": 4, "resources": {"mem_mb": 5000}, "jobid": 2, "cluster": {"queue": "q1"}}

echo "whatever_command"
