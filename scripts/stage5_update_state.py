# -*- coding: utf-8 -*-
"""Stage 5 — update recovery/STATE.md and manifest.json with the Stage-5 status."""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

STATE_ADD = """
## Completed — Stage 5 (preparation + protocol fix; NO GPU job, NO training, NO Test scoring)

| Step | Status | Evidence |
| --- | --- | --- |
| Reuse map / classification fixed (36 NEW_FIT + 8 NEW_EVAL; A0 separate BLOCKED) | DONE | `recovery/stage5/final_run_matrix.csv`, `recovery/stage5/a0_diagnostic_record.csv` |
| Protocol frozen: D-split 676/97/193, D-target average_MSE_4L, D-holdout retrospective-only | RECORDED | `recovery/stage5/frozen_protocol_stage5.md` |
| Window-containment defect found and fixed (D-windows, `--containment strict`) | DONE | `recovery/stage5/window_counts_verify.md`; counts match the Stage-5 table for all L |
| Full SHA-256 for code / data / protocol configs | DONE | `recovery/stage5/hashes_stage5.json` |
| Compute-node preflight script prepared (check #7 + resources) | PREPARED, NOT SUBMITTED | `recovery/stage5/preflight_compute_node.py`, `preflight_sbatch.sh` |
| Launch commands for all 44 rows prepared | PREPARED, NOT SUBMITTED | `recovery/stage5/launch_commands.md` |
| Chinese reports | DONE (no numeric results exist yet) | `recovery/stage5/results_report_zh.md`, `supervisor_brief_zh.md` |

**Status: `PREPARED` / `PREFLIGHT_READY`.** Nothing is `SUBMITTED`, `RUNNING` or `COMPLETED`.

### Blocking (unchanged, not invented)

- **D-compute** — GPU-hour ceiling + queue/node + concurrency: not authorized ⇒ no GPU job
  submitted, including the preflight.
- **D-a0-env** — A0 replay environment: not authorized ⇒ A0-01 stays `BLOCKED`.
"""

p = os.path.join(ROOT, "recovery", "STATE.md")
with io.open(p, "r", encoding="utf-8") as f:
    src = f.read()
marker = "## Next executable action"
if "## Completed — Stage 5" not in src:
    src = src.replace(marker, STATE_ADD.strip() + "\n\n" + marker, 1)
with io.open(p, "w", encoding="utf-8") as f:
    f.write(src)
print("STATE.md updated")

mp = os.path.join(ROOT, "recovery", "manifest.json")
with io.open(mp, "r", encoding="utf-8") as f:
    m = json.load(f)
m["stage5_preparation"] = {
    "status": "PREPARED_PREFLIGHT_READY",
    "date": "2026-09-24",
    "note": "classification fixed, protocol frozen, window-containment fix applied and verified on CPU; "
            "no GPU job, no training, no Test scoring",
    "matrix": {"rows": 44, "new_fit": 36, "new_eval": 8, "a0_blocked": 1},
    "recorded_decisions": ["D-split=676/97/193", "D-target=average_MSE_4L",
                           "D-windows=strict target containment", "D-holdout=retrospective only"],
    "open_decisions": ["D-compute", "D-a0-env"],
    "code_change": "scripts/{train_miflu,train_ablation,train_nlinear_966}.py: --containment {start,strict}; "
                   "default 'start' preserves legacy behaviour, A2 uses 'strict'",
    "window_counts_author_966_strict": {"24": [549, 74, 170], "36": [537, 62, 158],
                                        "48": [525, 50, 146], "60": [513, 38, 134]},
    "deliverables": [
        "recovery/stage5/frozen_protocol_stage5.md",
        "recovery/stage5/final_run_matrix.csv",
        "recovery/stage5/a0_diagnostic_record.csv",
        "recovery/stage5/hashes_stage5.json",
        "recovery/stage5/window_counts_verify.md",
        "recovery/stage5/preflight_compute_node.py",
        "recovery/stage5/preflight_sbatch.sh",
        "recovery/stage5/launch_commands.md",
        "recovery/stage5/launch_decisions_stage5.md",
        "recovery/stage5/results_report_zh.md",
        "recovery/stage5/supervisor_brief_zh.md",
    ],
}
with io.open(mp, "w", encoding="utf-8") as f:
    json.dump(m, f, indent=2, ensure_ascii=False)
print("manifest.json updated")
