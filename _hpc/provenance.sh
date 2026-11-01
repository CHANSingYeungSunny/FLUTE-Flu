#!/bin/bash
set -u
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
CD=/gpfs1/home/sychan552/stage5_a2_durable/code
echo "########## L24_s42 : the 18:30 run that made seed42/43 ckpts ##########"
cat "$AR"/L24_s42/training_miflu_log_20261031_183023.txt
echo
echo "########## L24_s42 : results 18:30 ##########"
cat "$AR"/L24_s42/results_miflu_paper_protocol_20261031_183023.csv
echo
echo "########## L24_s42 : head of the 03:18 run (source of the CSV) ##########"
grep -hE "Config:|Profile |Data:|batch=|containment|Text source|Author text|kept rep|FINAL|CSV\]" "$AR"/L24_s42/training_miflu_log_20261031_031814.txt | head -20
echo
echo "########## submit scripts on HPC ##########"
ls -la "$CD"/*.sh 2>/dev/null
echo
echo "########## grep export-dir usage in scripts ##########"
grep -rn "export-dir\|export_dir" "$CD"/*.sh 2>/dev/null | head -20
