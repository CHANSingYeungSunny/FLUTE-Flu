"""scripts/v3/figure_style.py — the SINGLE reusable plotting-style module for MIFlu v3.

Authoritative source of truth:
    docs/FIGURE_STYLE_GUIDE.md            (SHA-256 recorded in figure_style_audit.json)
    results/ili/figures/fig_q1_step_sweep_L24_L60_step0.png   (layout/visual reference)

Every v3 plotting script MUST import this module instead of redefining style.
It encodes, and does not reinterpret, the frozen rules below.

Frozen rules carried over from the guide
----------------------------------------
* canvas: hero 7 x 4.2 in; diagnostics 13 x 4.2 in (1x2); DPI 300 on export,
  figure.dpi 100 for on-screen, backend Agg.
* fonts: font.size 9, axes.titlesize 10/11, legend.fontsize 8, tick labelsize 8.
* legacy hero palette: ground truth #1f77b4 (blue dashed), prediction #d62728 (red solid),
  true peak blue inverted triangle, predicted peak red triangle up.
* flu-phase backgrounds: baseline #e8e8e8, ramp-up #fde0dd, peak #f9c0bb, decay #d9d2e9.
* directional-accuracy panel: #2ca02c with chance=0.5 and overall mean line #d62728 dotted.

v3 generalisation (documented deviations)
-----------------------------------------
* Ground truth is reserved as BLACK (#000000, dashed) in multi-model v3 figures so it can
  never collide with a model colour. The guide's #1f77b4 remains the ground-truth colour
  for the legacy two-figure v2 reproduction only.
* A colour-blind-safe Okabe-Ito-derived palette gives every model a STABLE identity that
  never changes between figures. Colour is never the only channel: every model also has a
  fixed line style and marker.
* Fixed-step encoding: step s has constant lead time (s+1) weeks (per
  `innovation.metrics.aggregate_fixed_step`). Step 0 is the primary endpoint; steps 1-3
  are mandatory supplementary lead-time analyses. Steps are NEVER averaged together.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

# ── canvas / export ─────────────────────────────────────────────────────────
EXPORT_DPI = 300
APPROVED_STEP_SWEEP_DPI = 190
SCREEN_DPI = 100
CANVAS = {
    "hero": (7.0, 4.2),          # single-panel continuous forecast
    "diagnostics": (13.0, 4.2),  # 1x2 panel
    "step_sweep": (13.0, 7.0),   # exact canvas of the approved q1 step-sweep template
    "group": (11.0, 4.2),
    "resource": (7.0, 4.6),
    "square": (7.0, 7.0),
}

# ── fonts ───────────────────────────────────────────────────────────────────
FONT = {"font.size": 9, "axes.titlesize": 11, "axes.labelsize": 9,
        "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "figure.titlesize": 11, "axes.titleweight": "bold"}

# ── colour ──────────────────────────────────────────────────────────────────
GT_COLOR = "#000000"           # reserved ground truth in v3 multi-model figures
LEGACY_GT_COLOR = "#1f77b4"    # guide palette, legacy v2 hero figure only
LEGACY_PRED_COLOR = "#d62728"
PHASE_COLORS = {"baseline": "#e8e8e8", "ramp_up": "#fde0dd",
                "peak": "#f9c0bb", "decay": "#d9d2e9"}
DIRECTION_COLOR = "#2ca02c"
OVERALL_LINE_COLOR = "#d62728"

MODEL_IDENTITY = {
    # Group A — Non-LLM
    "nlinear":      {"color": "#0072B2", "ls": "-",    "marker": "o", "label": "NLinear"},
    "dlinear":      {"color": "#56B4E9", "ls": "-",    "marker": "s", "label": "DLinear"},
    "patchtst":     {"color": "#009E73", "ls": "--",   "marker": "^", "label": "PatchTST-inspired"},
    "itransformer": {"color": "#E69F00", "ls": "-.",   "marker": "D", "label": "iTransformer-aligned"},
    # Group B — LLM-based
    "gpt2_miflu":   {"color": "#D55E00", "ls": "-",    "marker": "v", "label": "MIFlu GPT-2"},
    "qwen_time_llm": {"color": "#CC79A7", "ls": "--",  "marker": "P", "label": "Qwen2.5-1.5B Time-LLM-inspired"},
    "calf_llm":     {"color": "#8C564B", "ls": "-.",   "marker": "X", "label": "CALF-inspired Cross-Modal LLM"},
    "timecma_llm":  {"color": "#6A3D9A", "ls": (0, (3, 1, 1, 1)), "marker": "*", "label": "TimeCMA-inspired LLM"},
    # Cheap reference baselines (NOT primary architectures)
    "last_value_naive": {"color": "#7F7F7F", "ls": ":", "marker": "x", "label": "Last-value naive"},
    "seasonal_naive":   {"color": "#4D4D4D", "ls": (0, (1, 2)), "marker": "+", "label": "Seasonal naive"},
    # Negative controls (inherit the parent colour, differ by line style + hollow marker)
    "zero_text":     {"color": "#D55E00", "ls": (0, (1, 3)), "marker": "o", "label": "zero-text control"},
    "shuffled_text": {"color": "#D55E00", "ls": (0, (3, 1, 1, 1, 1, 1)), "marker": "s", "label": "shuffled-text control"},
    "llm_removed_or_alignment_only":
                     {"color": "#6A3D9A", "ls": (0, (5, 2)), "marker": "^", "label": "LLM-removed / alignment-only"},
}

GROUP_COLORS = {"A_non_llm": "#0072B2", "B_llm": "#D55E00",
                "naive": "#7F7F7F", "control": "#6A3D9A"}

# ── fixed-step encoding ─────────────────────────────────────────────────────
STEPS = (0, 1, 2, 3)
STEP_LEAD_WEEKS = {0: 1, 1: 2, 2: 3, 3: 4}      # step s -> constant (s+1) weeks ahead
STEP_LINESTYLE = {0: "-", 1: "--", 2: "-.", 3: ":"}
STEP_MARKER = {0: "o", 1: "s", 2: "^", 3: "D"}
PRIMARY_STEP = 0

HORIZONS = (24, 36, 48, 60)


def step_lead_label(step: int) -> str:
    """Human label for a fixed step, e.g. 0 -> '1-week ahead'."""
    step = int(step)
    if step not in STEP_LEAD_WEEKS:
        raise ValueError(f"unsupported fixed step {step}; allowed {STEPS}")
    return f"{STEP_LEAD_WEEKS[step]}-week ahead"


def model_identity(model_key: str) -> dict:
    """Stable visual identity for a model. Unknown keys fail loudly (not silently)."""
    if model_key not in MODEL_IDENTITY:
        raise KeyError(
            f"no registered visual identity for model '{model_key}'. "
            f"Add it to MODEL_IDENTITY so the same model never changes appearance.")
    return dict(MODEL_IDENTITY[model_key])


def apply_style() -> None:
    """Apply the frozen style guide rcParams."""
    plt.rcParams.update(FONT)
    plt.rcParams.update({
        "figure.dpi": SCREEN_DPI,
        "savefig.dpi": EXPORT_DPI,
        "savefig.bbox": "tight",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "legend.frameon": False,
        "font.family": "DejaVu Sans",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def new_figure(kind: str = "hero", nrows: int = 1, ncols: int = 1, **kwargs):
    """Create a figure with the canvas size frozen for that figure kind."""
    if kind not in CANVAS:
        raise ValueError(f"unknown figure kind '{kind}'; allowed {sorted(CANVAS)}")
    apply_style()
    w, h = CANVAS[kind]
    if (nrows, ncols) != (1, 1):
        w = w * ncols if kind == "diagnostics" else w
    fig, axes = plt.subplots(nrows, ncols, figsize=(w, h), **kwargs)
    return fig, axes


def style_line(ax, line, model_key: str, step: int = PRIMARY_STEP) -> None:
    """Apply the stable model + step identity to a Line2D."""
    ident = model_identity(model_key)
    line.set_color(ident["color"])
    line.set_linestyle(ident["ls"])
    line.set_marker(ident["marker"])
    line.set_markersize(3.5 if step == PRIMARY_STEP else 2.5)
    line.set_linewidth(1.6 if step == PRIMARY_STEP else 1.2)
    line.set_label(f"{ident['label']} ({step_lead_label(step)})")


def ground_truth_line(ax, xs, ys, label: str = "Ground truth"):
    (ln,) = ax.plot(xs, ys, color=GT_COLOR, ls="--", lw=1.8, marker=None, label=label)
    return ln


def shade_phases(ax, dates, phases) -> None:
    """Shade flu-phase backgrounds using the guide's phase palette."""
    seen = set()
    for d, p in zip(dates, phases):
        key = (p,)
        ax.axvspan(d, d, color=PHASE_COLORS.get(p, "#ffffff"), alpha=0.0)
        seen.add(p)
    # legend proxies for the phases actually present
    handles = [plt.Rectangle((0, 0), 1, 1, color=PHASE_COLORS[p], label=p.replace("_", " ").title())
               for p in sorted(seen) if p in PHASE_COLORS]
    if handles:
        ax.add_artist(ax.legend(handles=handles, loc="upper left", fontsize=7, title="phase"))


def panel_label(ax, label: str) -> None:
    """Add a panel label such as (a) in the top-left corner."""
    ax.text(0.01, 0.98, label, transform=ax.transAxes, ha="left", va="top",
            fontsize=10, fontweight="bold")


def save_figure(fig, path: str) -> str:
    """Export at publication DPI and return the written path."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, dpi=EXPORT_DPI)
    plt.close(fig)
    return path


def _sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_provenance(figure_path: str, *, plotting_script: str,
                     style_guide_sha256: str, reference_figure_sha256: str,
                     source_prediction_files, source_metric_files,
                     source_run_ids, checkpoint_hashes,
                     protocol_version: str, implementation_source_version: str,
                     extra: dict | None = None) -> str:
    """Write the mandatory provenance sidecar next to a figure."""
    rec = {
        "figure_path": figure_path,
        "figure_sha256": _sha(figure_path),
        "plotting_script": plotting_script,
        "plotting_script_sha256": _sha(plotting_script),
        "style_guide_sha256": style_guide_sha256,
        "reference_figure_sha256": reference_figure_sha256,
        "source_prediction_files": sorted(source_prediction_files or []),
        "source_metric_files": sorted(source_metric_files or []),
        "source_run_ids": sorted(source_run_ids or []),
        "checkpoint_hashes": checkpoint_hashes or {},
        "protocol_version": protocol_version,
        "implementation_source_version": implementation_source_version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "primary_step": PRIMARY_STEP,
        "steps_present": list(STEPS),
        "step_lead_weeks": {str(k): v for k, v in STEP_LEAD_WEEKS.items()},
        "steps_averaged": False,
    }
    if extra:
        rec.update(extra)
    sidecar = os.path.splitext(figure_path)[0] + ".provenance.json"
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=2)
    return sidecar


def model_legend_handles(model_keys):
    """Legend proxies in a stable, preregistered model order."""
    out = []
    for k in model_keys:
        ident = model_identity(k)
        out.append(Line2D([], [], color=ident["color"], ls=ident["ls"],
                          marker=ident["marker"], label=ident["label"]))
    return out
