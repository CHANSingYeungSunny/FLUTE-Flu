#!/bin/bash
# READ-ONLY inspection of the D15 fail-stop row. Lightweight only.
B=/scratch/sychan552/_v318d
R=/scratch/sychan552/innovation_deploy_root_v3_clean12
K=baseline__last_value_naive__L24__seedna__w1
DUR=/home/sychan552/innovation_durable/screening

echo "=== clean6 CSV ledger (first controller, prior deployment) ==="
CSV=/scratch/sychan552/innovation_deploy_root_v3_clean6/results/v3_clean/runs/wave1_ledger.csv
head -2 "$CSV" 2>/dev/null
echo "csv_lines=$(( $(wc -l < "$CSV" 2>/dev/null) - 1 ))"
echo "csv_completed_0_0=$(grep -c ',COMPLETED,0:0' "$CSV" 2>/dev/null)"
echo "csv_nonzero=$(grep -vc ',COMPLETED,0:0' "$CSV" 2>/dev/null)"

echo
echo "=== D15 row: durable destination state ==="
echo "dest_exists=$(test -d "$DUR/$K" && echo yes || echo no)"
echo "dest_bytes=$(du -sb "$DUR/$K" 2>/dev/null | cut -f1)"
echo "dest_entries=$(find "$DUR/$K" -mindepth 1 2>/dev/null | wc -l)"
echo "dest_files=$(find "$DUR/$K" -type f 2>/dev/null | wc -l)"
echo "dest_tree:"; find "$DUR/$K" -maxdepth 2 2>/dev/null | sort | head -20
echo "staging_siblings:"
ls -1d "$DUR"/*.staging* "$DUR"/.[!.]* 2>/dev/null | head -10

echo
echo "=== D15 row: scratch source (must be fully preserved) ==="
echo "src_files=$(find "$R/results/v3_clean/runs/$K" -type f 2>/dev/null | wc -l)"
echo "src_bytes=$(du -sb "$R/results/v3_clean/runs/$K" 2>/dev/null | cut -f1)"

echo
echo "=== does the failing root's finalize output exist? ==="
echo "verif_report=$(test -f "$B/finalize/$K.storage_verification.json" && echo yes || echo no)"
ls -1 "$B/finalize" 2>/dev/null | tail -5

echo
echo "=== finalize driver: baseline handling (source lines) ==="
grep -n 'baseline\|checkpoint\|export_compact\|no_checkpoint\|applicable' \
     "$B/finalize_row.py" 2>/dev/null | head -30

echo
echo "=== v3.18 deployment identity ==="
grep -m1 'version' "$R/results/v3_clean/implementation/source_manifest.json" 2>/dev/null
echo "gate_reports_in_root:"
ls -1 $R/results/v3_clean/implementation/ 2>/dev/null | grep -i gate | head
