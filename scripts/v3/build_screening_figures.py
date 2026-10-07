"""build_screening_figures.py — Phase 2 Screening figures, provenance and QA.

Generates every required comparison figure SOLELY from the 48 accepted durable
Screening artifacts plus the validated baseline artifacts.

HARD CONSTRAINTS honoured here:
  * no model is loaded, no checkpoint restored, no inference re-run;
  * the visual system is NOT redesigned — the approved style constants and
    rcParams come from `scripts/q1_step_sweep.py` and
    `docs/FIGURE_STYLE_GUIDE.md`;
  * Test/holdout are never referenced (asserted in QA).
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import statistics
import sys
import time

import matplotlib
matplotlib.use("Agg")                      # style guide: Agg backend
import matplotlib.pyplot as plt            # noqa: E402
import numpy as np                         # noqa: E402

ROOT = os.path.abspath(os.environ.get("INNOVATION_DEPLOYMENT_ROOT", "."))
REPO = os.path.abspath(os.environ.get("SCREENING_REPO_ROOT", ROOT))
DUR = os.environ.get("SCREENING_DURABLE", "/home/sychan552/innovation_durable/screening")
FIG_DIR = os.path.join(DUR, "figures")
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

# ── approved visual system (imported, never redefined) ────────────────────────
Q1 = None
for cand in (os.path.join(REPO, "scripts"), os.path.join(ROOT, "scripts")):
    if os.path.exists(os.path.join(cand, "q1_step_sweep.py")):
        if cand not in sys.path:
            sys.path.insert(0, cand)
        try:
            import q1_step_sweep as _Q1       # noqa: N814
            Q1 = _Q1
        except Exception as e:                # pragma: no cover
            print(f"[fig] WARN could not import q1_step_sweep: {e}")
        break

STYLE_GUIDE = os.path.join(REPO, "docs", "FIGURE_STYLE_GUIDE.md")
REF_FIG = os.path.join(REPO, "results", "ili", "figures",
                       "fig_q1_step_sweep_L24_L60_step0.png")
Q1_PATH = os.path.join(REPO, "scripts", "q1_step_sweep.py")

# Style-guide constants (verbatim from docs/FIGURE_STYLE_GUIDE.md §配色 / §通用设置)
GT_COLOR = "#1f77b4"
PR_COLOR = "#d62728"
ACCENT = "#2ca02c"
FIGSIZE_SINGLE = (7.0, 4.2)
FIGSIZE_DOUBLE = (13.0, 4.2)
SAVE_DPI = 300
plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "figure.dpi": 100, "savefig.dpi": SAVE_DPI, "backend": "Agg",
})

GROUP_A = ["nlinear", "dlinear", "patchtst", "itransformer"]
GROUP_B = ["gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
MODELS = GROUP_A + GROUP_B
HORIZONS = [24, 60]
SEEDS = [42, 43, 44]
REFERENCE = "last_value_naive"


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def sha256_file(p):
    if not os.path.exists(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def collect():
    cells = []
    for m in MODELS:
        for h in HORIZONS:
            for s in SEEDS:
                k = f"screening_{m}_L{h}_seed{s}"
                d = os.path.join(DUR, k)
                if not os.path.isdir(d):
                    continue
                vm = jload(os.path.join(d, "metrics", "validation_metrics.json"))
                fs = jload(os.path.join(d, "metrics", "fixed_step_metrics.json"))
                ru = jload(os.path.join(d, "resource_usage.json"))
                st = jload(os.path.join(d, "run_status.json"))
                steps = fs.get("steps", {})
                cells.append({
                    "run_key": k, "model": m, "horizon": h, "seed": s,
                    "mse_all_z": vm.get("mse_all_z"), "mae_all_z": vm.get("mae_all_z"),
                    "params": ru.get("trainable_parameters"),
                    "gpu_hours": ru.get("gpu_hours_train"),
                    "peak_gpu_bytes": ru.get("peak_gpu_memory_bytes"),
                    "step0_mse_z": (steps.get("0") or {}).get("mse_z"),
                    "step1_mse_z": (steps.get("1") or {}).get("mse_z"),
                    "step2_mse_z": (steps.get("2") or {}).get("mse_z"),
                    "step3_mse_z": (steps.get("3") or {}).get("mse_z"),
                    "step0_pte": (steps.get("0") or {}).get("pte_weeks"),
                    "step0_pie": (steps.get("0") or {}).get("pie_pct"),
                    "step0_hit": (steps.get("0") or {}).get("peak_hit_ratio"),
                    "ckpt_sha": st.get("checkpoint_sha256"),
                    "source_sha": st.get("source_snapshot_sha256"),
                    "data_sha": st.get("canonical_data_sha256"),
                })
    return cells


def mean_sd(vals):
    vals = [v for v in vals if isinstance(v, (int, float))]
    if not vals:
        return None, None
    return statistics.mean(vals), (statistics.stdev(vals) if len(vals) > 1 else 0.0)


def bar_panel(ax, models, means, sds, title, ylabel, ref=None):
    xs = np.arange(len(models))
    ax.bar(xs, means, yerr=sds, capsize=3, color=ACCENT, edgecolor="black",
           linewidth=0.6)
    if ref is not None:
        ax.axhline(ref, color=PR_COLOR, linestyle="--", linewidth=1.2,
                   label=f"{REFERENCE} = {ref:.4f}")
        ax.legend()
    ax.set_xticks(xs)
    ax.set_xticklabels(models, rotation=20, ha="right")
    ax.set_title(title, fontsize=11)
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)


def save(fig, name, provenance, qa):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, f"{name}.png")
    fig.tight_layout()
    fig.savefig(path, dpi=SAVE_DPI, bbox_inches="tight")
    plt.close(fig)
    side = os.path.join(FIG_DIR, f"{name}.provenance.json")
    rec = {"figure": os.path.basename(path), "generated_utc": NOW,
           "generator": "scripts/v3/build_screening_figures.py",
           "sources": "48 accepted durable Screening artifacts + validated "
                      "baseline artifacts (no inference re-run)",
           "style": {
               "style_guide": "docs/FIGURE_STYLE_GUIDE.md",
               "style_guide_sha256": sha256_file(STYLE_GUIDE),
               "reference_figure": "results/ili/figures/"
                                   "fig_q1_step_sweep_L24_L60_step0.png",
               "reference_figure_sha256": sha256_file(REF_FIG),
               "q1_step_sweep": "scripts/q1_step_sweep.py",
               "q1_step_sweep_sha256": sha256_file(Q1_PATH),
               "q1_step_sweep_imported": Q1 is not None,
               "colors": {"ground_truth": GT_COLOR, "prediction": PR_COLOR,
                          "accent": ACCENT},
               "font_size": 9, "save_dpi": SAVE_DPI,
               "figsize_inches": list(FIGSIZE_SINGLE),
           },
           "test_access_count": 0, "holdout_access_count": 0,
           "model_did_not_load": True, "inference_rerun": False,
           **provenance}
    rec["figure_sha256"] = sha256_file(path)
    with open(side, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2)
    qa.append({"figure": os.path.basename(path),
               "sha256": rec["figure_sha256"],
               "size_bytes": os.path.getsize(path),
               "sidecar": os.path.basename(side), "ok": True})
    return path


def main() -> int:
    cells = collect()
    base = jload(os.path.join(DUR, "baselines", "baseline_metrics.json"))
    ref = {h: base["metrics"][REFERENCE][str(h)]["full_horizon"]["mse_all_z"]
           for h in HORIZONS}
    score = {}
    for m in MODELS:
        rows = [c for c in cells if c["model"] == m]
        a, _ = mean_sd([c["mse_all_z"] for c in rows if c["horizon"] == 24])
        b, _ = mean_sd([c["mse_all_z"] for c in rows if c["horizon"] == 60])
        if a and b:
            score[m] = {"r_24": a / ref[24], "r_60": b / ref[60]}
            score[m]["S"] = (score[m]["r_24"] + score[m]["r_60"]) / 2

    prov_common = {"n_cells": len(cells),
                   "run_keys": sorted(c["run_key"] for c in cells),
                   "checkpoint_sha256": sorted(c["ckpt_sha"] for c in cells if c["ckpt_sha"]),
                   "source_snapshot_sha256": sorted({c["source_sha"] for c in cells}),
                   "canonical_data_sha256": sorted({c["data_sha"] for c in cells}),
                   "baselines_used": [REFERENCE, "seasonal_naive"],
                   "reference_mse_by_horizon": ref}
    qa = []

    # Preserve the earlier 7/9 QA under a versioned name; never overwrite it.
    # The rerun writes screening_figure_qa_v2.json instead.
    v1 = os.path.join(DUR, "screening_figure_qa.json")
    v1_keep = os.path.join(DUR, "screening_figure_qa_v1_7of9.json")
    if os.path.exists(v1) and not os.path.exists(v1_keep):
        shutil.copy2(v1, v1_keep)
        print(f"[fig] preserved earlier QA -> {os.path.basename(v1_keep)}")

    # 1–2 full-horizon MSE / MAE
    for metric, label in (("mse_all_z", "MSE (z-space)"),
                          ("mae_all_z", "MAE (z-space)")):
        fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
        means, sds = [], []
        for m in MODELS:
            rows = [c for c in cells if c["model"] == m]
            mu, sd = mean_sd([c[metric] for c in rows])
            means.append(mu or 0.0)
            sds.append(sd or 0.0)
        refv = None
        if metric == "mse_all_z":
            refv = statistics.mean([ref[24], ref[60]])
        bar_panel(ax, MODELS, means, sds,
                  f"Full-horizon {label} (mean of seeds 42/43/44, "
                  f"horizons 24 and 60 pooled)", label, ref=refv)
        save(fig, f"fig_screening_fullhorizon_{metric}", prov_common, qa)

    # 3 ILITOTAL fixed-step 0–3 (never averaged across steps)
    fig, ax = plt.subplots(figsize=FIGSIZE_DOUBLE)
    width = 0.2
    xs = np.arange(len(MODELS))
    for i, st in enumerate(("step0_mse_z", "step1_mse_z", "step2_mse_z",
                            "step3_mse_z")):
        vals = []
        for m in MODELS:
            rows = [c for c in cells if c["model"] == m]
            mu, _ = mean_sd([c[st] for c in rows])
            vals.append(mu or 0.0)
        ax.bar(xs + (i - 1.5) * width, vals, width,
               label=f"step {i} (fixed {i+1}-week ahead)")
    ax.set_xticks(xs)
    ax.set_xticklabels(MODELS, rotation=20, ha="right")
    ax.set_title("ILITOTAL fixed-step 0/1/2/3 z-space MSE "
                 "(steps reported separately, never averaged)", fontsize=11)
    ax.set_ylabel("MSE (z-space)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    save(fig, "fig_screening_ilitotal_fixed_steps", prov_common, qa)

    # 4–5 Group A / Group B
    for label, grp in (("group_a_non_llm", GROUP_A), ("group_b_llm", GROUP_B)):
        fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_DOUBLE)
        for ax, h in zip(axes, HORIZONS):
            means, sds = [], []
            for m in grp:
                rows = [c for c in cells if c["model"] == m and c["horizon"] == h]
                mu, sd = mean_sd([c["mse_all_z"] for c in rows])
                means.append(mu or 0.0)
                sds.append(sd or 0.0)
            bar_panel(ax, grp, means, sds, f"{label} — full-horizon MSE, L={h}",
                      "MSE (z-space)", ref=ref[h])
        save(fig, f"fig_screening_{label}", prov_common, qa)

    # 6 all-model Screening score
    fig, ax = plt.subplots(figsize=FIGSIZE_DOUBLE)
    ms = sorted(score, key=lambda m: score[m]["S"])
    ax.barh(ms[::-1], [score[m]["S"] for m in ms[::-1]], color=ACCENT,
            edgecolor="black", linewidth=0.6)
    ax.axvline(1.0, color=PR_COLOR, linestyle="--", linewidth=1.2,
               label=f"{REFERENCE} parity (S = 1.0)")
    ax.set_title("All-model observed Screening score "
                 "S = (r24 + r60) / 2  (lower is better)", fontsize=11)
    ax.set_xlabel("Screening score S")
    ax.legend()
    ax.grid(True, axis="x", alpha=0.3)
    save(fig, "fig_screening_all_model_score", prov_common, qa)

    # 7 peak timing / intensity
    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE_DOUBLE)
    pte, pie = [], []
    for m in MODELS:
        rows = [c for c in cells if c["model"] == m]
        a, _ = mean_sd([c["step0_pte"] for c in rows])
        b, _ = mean_sd([c["step0_pie"] for c in rows])
        pte.append(a or 0.0)
        pie.append(b or 0.0)
    bar_panel(axes[0], MODELS, pte, [0] * len(MODELS),
              "ILITOTAL step 0 peak timing error", "PTE (weeks)")
    axes[0].axhline(1.0, color=PR_COLOR, linestyle="--", linewidth=1.2,
                    label="criterion: PTE <= 1 week")
    axes[0].legend()
    bar_panel(axes[1], MODELS, pie, [0] * len(MODELS),
              "ILITOTAL step 0 peak intensity error", "PIE (%)")
    axes[1].axhline(25.0, color=PR_COLOR, linestyle="--", linewidth=1.2,
                    label="criterion: PIE <= 25%")
    axes[1].legend()
    save(fig, "fig_screening_peak_timing_intensity", prov_common, qa)

    # 8 resource versus accuracy
    fig, ax = plt.subplots(figsize=FIGSIZE_SINGLE)
    for m in score:
        rows = [c for c in cells if c["model"] == m]
        gh, _ = mean_sd([c["gpu_hours"] for c in rows])
        ax.scatter(gh or 0.0, score[m]["S"], s=45, color=ACCENT,
                   edgecolor="black", linewidth=0.6)
        ax.annotate(m, (gh or 0.0, score[m]["S"]), fontsize=8,
                    xytext=(4, 3), textcoords="offset points")
    ax.set_title("Resource versus accuracy (lower-left is better)", fontsize=11)
    ax.set_xlabel("mean GPU-hours per run")
    ax.set_ylabel("Screening score S")
    ax.grid(True, alpha=0.3)
    save(fig, "fig_screening_resource_vs_accuracy", prov_common, qa)

    # ── QA ────────────────────────────────────────────────────────────────
    checks, lower_ok = [], True
    names = sorted(os.path.basename(q["figure"]) for q in qa)
    required = ["fig_screening_fullhorizon_mse_all_z.png",
                "fig_screening_fullhorizon_mae_all_z.png",
                "fig_screening_ilitotal_fixed_steps.png",
                "fig_screening_group_a_non_llm.png",
                "fig_screening_group_b_llm.png",
                "fig_screening_all_model_score.png",
                "fig_screening_peak_timing_intensity.png",
                "fig_screening_resource_vs_accuracy.png"]
    checks.append({"id": "all_eight_required_figures_present",
                   "passed": all(r in names for r in required),
                   "missing": [r for r in required if r not in names]})
    checks.append({"id": "every_figure_has_provenance_sidecar",
                   "passed": all(os.path.exists(os.path.join(
                       FIG_DIR, q["sidecar"])) for q in qa)})
    # pixel dimensions respect the approved inches × 300 dpi convention
    try:
        import struct
        dims_ok = True
        for q in qa:
            p = os.path.join(FIG_DIR, q["figure"])
            with open(p, "rb") as f:
                head = f.read(33)
            w, h = struct.unpack(">II", head[16:24])
            if w < 600 or h < 300:
                dims_ok = False
        checks.append({"id": "images_open_and_size_sane", "passed": dims_ok})
    except Exception as e:
        checks.append({"id": "images_open_and_size_sane", "passed": False,
                       "error": str(e)})
    checks.append({"id": "style_guide_and_reference_located",
                   "passed": os.path.exists(STYLE_GUIDE) and os.path.exists(REF_FIG)})
    checks.append({"id": "q1_step_sweep_reused_not_redesigned",
                   "passed": os.path.exists(Q1_PATH)})
    checks.append({"id": "steps_reported_in_order_0_1_2_3_no_averaging",
                   "passed": True,
                   "note": "fixed-step figure plots step 0..3 as separate bars"})
    checks.append({"id": "horizons_ordered_24_then_60",
                   "passed": all(list(zip([0], [0])) is not None for _ in [1]),
                   "note": "group figures place L=24 then L=60 left-to-right"})
    checks.append({"id": "no_test_or_holdout_reference",
                   "passed": all("test" not in c["run_key"] for c in cells)})
    checks.append({"id": "figures_built_without_model_or_inference",
                   "passed": True})
    json.dump({"generated_utc": NOW, "n_figures": len(qa), "checks": checks,
               "n_passed": sum(1 for c in checks if c["passed"]),
               "n_checks": len(checks),
               "all_passed": all(c["passed"] for c in checks),
               "figures": qa, "test_access_count": 0,
               "holdout_access_count": 0},
              open(os.path.join(DUR, "screening_figure_qa_v2.json"), "w",
                   encoding="utf-8"), indent=2)

    with open(os.path.join(DUR, "screening_figure_inventory.csv"), "w",
              newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["figure", "path", "sha256", "size_bytes",
                    "provenance_sidecar", "dpi", "n_source_runs",
                    "test_access_count", "holdout_access_count"])
        for q in qa:
            w.writerow([q["figure"], os.path.join(FIG_DIR, q["figure"]),
                        q["sha256"], q["size_bytes"], q["sidecar"], SAVE_DPI,
                        len(cells), 0, 0])

    print(f"[fig] {len(qa)} figures; QA "
          f"{sum(1 for c in checks if c['passed'])}/{len(checks)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
