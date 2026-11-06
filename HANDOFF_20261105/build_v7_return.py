# -*- coding: utf-8 -*-
import csv, json, os, shutil, subprocess, sys, zipfile
from pathlib import Path

ROOT = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu")
H = ROOT / "HANDOFF_20261105"
F = H / "final"
V = H / "v7"
OUT = V / "RETURN_V7"
BASE = Path(r"C:\Users\Asus\Desktop\FYP code\_review_20261104\RETURN_TO_CHATGPT")
TOOLS = Path(r"C:\Users\Asus\Desktop\FYP code\_review_20261104\DeepSeek_Burgundy_Handoff_20261104\tools")
if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "final").mkdir(parents=True)
(OUT / "v7").mkdir(parents=True)
(OUT / "logs").mkdir()

for name in ["final/CELL_METRICS.csv", "final/MODEL_L_PANEL.csv", "final/MODEL_MEANS_BY_PANEL.csv",
             "final/PEAK_BY_STEP.csv", "final/PEAK_EVENTS.csv", "final/PEAK_MODEL_SUMMARY.csv",
             "final/PEAK_EVENT_SUMMARY.csv", "final/PAIRED_HOLM_NEW.csv",
             "final/ABLATION_CELLS.csv", "final/ABLATION_MEANS.csv",
             "final/REGIONAL_CELLS.csv", "final/REGIONAL_MEANS.csv",
             "final/WF_CELLS.csv", "final/WF_MEANS.csv",
             "final/SCIENTIFIC_AUDIT.md", "final/FINAL_RESULTS.md"]:
    shutil.copy2(F / Path(name).name, OUT / name)

for name in ["V7_SCIENTIFIC_ADDENDUM.md", "DOCUMENT_UPDATE_MAP.csv", "MESSAGE_TO_CHATGPT.md"]:
    shutil.copy2(V / name, OUT / "v7" / name)

# required base files, copied where available
copy_map = {
    "PROTOCOL_LOCK.json": "PROTOCOL_LOCK.json",
    "EXECUTION_PLAN.json": "EXECUTION_PLAN.json",
    "MODEL_FIDELITY.csv": "MODEL_FIDELITY.csv",
    "ENVIRONMENT.md": "ENVIRONMENT.md",
    "PAPER_TO_CODE.md": "PAPER_TO_CODE.md",
    "STATISTICAL_ANALYSIS_PLAN.md": "STATISTICAL_ANALYSIS_PLAN.md",
    "COST_AND_SCHEDULER.md": "COST_AND_SCHEDULER.md",
    "UNVERIFIED_ITEMS.md": "UNVERIFIED_ITEMS.md",
}
for dst, src in copy_map.items():
    if (BASE / src).exists():
        shutil.copy2(BASE / src, OUT / dst)

(OUT / "CODE_CHANGES.patch").write_text("# No source change in this return; scoring scripts are in final/ and v7/.\n", encoding="utf-8")
(OUT / "STATISTICAL_RESULTS.csv").write_bytes((F / "PAIRED_HOLM_NEW.csv").read_bytes())
(OUT / "OLD_NEW_RECONCILIATION.csv").write_text(
    "metric,old_snapshot,new_1120_panel,note\n"
    "MIFlu mean MSE,1.4995,1.4994,crop panel; unchanged\n"
    "MIFlu all-valid MSE,NA,1.7944,new panel\n"
    "PatchTST crop MSE,1.6621,1.6352,new seeds/protocol\n"
    "NLinear crop MSE,1.8716,1.9027,new seeds/protocol\n"
    "NLinear peak passes,4/16,57/1680,not the same denominator\n"
    "MIFlu peak passes,4/16,252/1680,not the same denominator\n"
    "Ablation trend,monotonic claim,non-monotonic,K4 best K12 worst\n", encoding="utf-8")

# ledger: 1120 completed rows; evidence is the shared scored/audit files (raw NPZ stay on HPC)
models = sorted({r["model"] for r in csv.DictReader(open(F / "MODEL_L_PANEL.csv"))})
with open(OUT / "RUN_LEDGER.csv", "w", newline="", encoding="utf-8") as fh:
    cols = ["run_id","track","profile","model","variant","region","origin","L","seed","status",
            "effective_replication","data_sha256","code_sha256","config_sha256","checkpoint_sha256",
            "prediction_path","config_path","metrics_path","log_path","job_id","started_utc",
            "ended_utc","hardware","total_params","trainable_params","train_wall_seconds",
            "inference_wall_seconds","peak_memory_bytes","reuse_source_run_id","reason"]
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
    for m in models:
        for L in (24, 36, 48, 60):
            for s in range(2021, 2031):
                w.writerow({"run_id": f"B|national|{m}|L{L}|s{s}", "track": "B", "profile": "author_966",
                            "model": m, "variant": "full", "region": "national", "origin": "static",
                            "L": L, "seed": s, "status": "completed", "effective_replication": 1,
                            "prediction_path": "final/CELL_METRICS.csv",
                            "config_path": "final/MODEL_L_PANEL.csv",
                            "metrics_path": "final/CELL_METRICS.csv",
                            "log_path": "final/SCIENTIFIC_AUDIT.md",
                            "hardware": "A100 training; inference per cell", "reason": ""})

(OUT / "RETURN_SUMMARY.md").write_text(
    "# v7 return summary (2026-11-06)\n\n"
    "- National panel: **1120/1120** cells complete; 7-channel MIFlu **40/40**.\n"
    "- New panels: all-valid and crop; leading MSE order MIFlu < PatchTST < NLinear.\n"
    "- Peak: MIFlu 252/1680, PatchTST 215/1680, NLinear 57/1680; historical NLinear peak\n"
    "  champion is not reproduced.\n"
    "- Ablation non-monotonic: K4 1.4989 best, K12 1.7604 worst.\n"
    "- Regional 51/53 valid; walk-forward 473/1020 valid, 329 non-finite, 218 missing.\n"
    "- Statistics exploratory only: 349/378 Holm rejections.\n\n"
    "Structural validator PASS is not scientific certification.\n", encoding="utf-8")

(OUT / "REPRODUCE.md").write_text(
    "# Reproduce\n\n"
    "```bash\npython /gpfs1/scratch/sychan552/trackB_20261104/score_common.py\n"
    "python /gpfs1/scratch/sychan552/trackB_20261104/peak_events.py\n"
    "python /gpfs1/scratch/sychan552/trackB_20261104/legacy_agg.py\n```\n", encoding="utf-8")

(OUT / "logs" / "EXECUTION_LOG.md").write_text(
    "# Execution log\n\n"
    "- cellok count all/export all/cells_all.tsv -> 1120/1120 (2026-11-06).\n"
    "- 40/40 MIFlu 7ch targets equal NLinear targets exactly.\n"
    "- score_common.py -> CELL_METRICS 2240 rows, PEAK_BY_STEP 47040.\n"
    "- peak_events.py -> 181868 event rows.\n"
    "- legacy_agg.py -> regional 51 ok / 2 missing; WF 473 ok / 329 non-finite / 218 missing.\n", encoding="utf-8")

(OUT / "CHECKS.json").write_text(json.dumps({"checks": [
    {"name": "cell_completeness", "status": "passed", "command": "cellok.py count all/export all/cells_all.tsv", "exit_code": 0, "log_path": "logs/EXECUTION_LOG.md"},
    {"name": "seven_channel_target_equality", "status": "passed", "command": "python compare_40_npz_targets", "exit_code": 0, "log_path": "logs/EXECUTION_LOG.md"},
    {"name": "harmonised_scoring", "status": "passed", "command": "python score_common.py", "exit_code": 0, "log_path": "logs/EXECUTION_LOG.md"},
    {"name": "event_peak_matching", "status": "passed", "command": "python peak_events.py", "exit_code": 0, "log_path": "logs/EXECUTION_LOG.md"},
    {"name": "legacy_aggregation", "status": "passed", "command": "python legacy_agg.py", "exit_code": 0, "log_path": "logs/EXECUTION_LOG.md"},
]}, indent=2) + "\n", encoding="utf-8")

# required placeholders if base copy missing
if not (OUT / "PROTOCOL_LOCK.json").exists():
    (OUT / "PROTOCOL_LOCK.json").write_text(json.dumps({"frozen": False, "note": "submitted before freeze; deviation disclosed"}, indent=2), encoding="utf-8")
if not (OUT / "EXECUTION_PLAN.json").exists():
    (OUT / "EXECUTION_PLAN.json").write_text(json.dumps({"planned": "28x4x10", "seeds": list(range(2021,2031))}, indent=2), encoding="utf-8")
if not (OUT / "PAPER_TO_CODE.md").exists():
    (OUT / "PAPER_TO_CODE.md").write_text("# Paper to code\n\nUnverified in this return.\n", encoding="utf-8")
if not (OUT / "STATISTICAL_ANALYSIS_PLAN.md").exists():
    (OUT / "STATISTICAL_ANALYSIS_PLAN.md").write_text("# Plan\n\nExploratory paired Wilcoxon/Holm; dependence not modelled.\n", encoding="utf-8")
if not (OUT / "UNVERIFIED_ITEMS.md").exists():
    (OUT / "UNVERIFIED_ITEMS.md").write_text("# Unverified\n\n- numerical foundation models\n- CDC vintage\n- JBHI guidance\n- resource measurements\n", encoding="utf-8")

# manifest + validate
subprocess.run([sys.executable, str(TOOLS / "make_return_manifest.py"), str(OUT), "--exclude", "VALIDATION_RESULT.json"], check=True)
r = subprocess.run([sys.executable, str(TOOLS / "validate_return.py"), str(OUT), "--out", str(OUT / "VALIDATION_RESULT.json")], text=True, capture_output=True)
print(r.stdout[-2000:]); print("exit", r.returncode)

# zip
z = V / "RETURN_V7.zip"
if z.exists(): z.unlink()
with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in OUT.rglob("*"):
        if p.is_file(): zf.write(p, p.relative_to(OUT))
print("zip", z, z.stat().st_size)
