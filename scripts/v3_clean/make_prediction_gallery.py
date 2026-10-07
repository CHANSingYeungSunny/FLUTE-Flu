"""Generate one PNG per accepted experiment (580) from the authoritative
ILITOTAL predictions, plus an index CSV + manifest. Compact but complete:
each panel shows the forecast window only (ground truth + prediction) with
true/pred peak markers and physical MSE/MAE.
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS = ROOT / "results" / "v3_clean" / "analysis"
GALLERY = ANALYSIS / "figures" / "gallery"
GALLERY.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT / "scripts"))
from cdc_calendar import load_week_calendar  # noqa: E402

MODEL_COLOR = {
    "nlinear": "#08519c", "dlinear": "#2c7fb8", "patchtst": "#6baed6",
    "itransformer": "#a6bddb", "gpt2_miflu": "#a50f15", "qwen_time_llm": "#d95f0e",
    "calf_llm": "#f16913", "timecma_llm": "#fdae6b",
    "seasonal_naive": "#252525", "last_value_naive": "#969696",
}

T = 104
ORIGIN = 715

RAW = pd.read_csv(ROOT / "data/raw/national_illness_raw.csv")
ILI = RAW["ILITOTAL"].to_numpy(np.float64)
_cal = load_week_calendar(str(ROOT / "data/raw/national_illness_raw.csv"))
CAL = {int(r.abs_week): str(r.week_start_date)[:10] for r in _cal.itertuples()}

EXTRACT = pd.read_csv(ROOT / "_tmp_audit/ili_ilitotal_extract.csv.gz",
                      compression="gzip")
EXTRACT["abs_week"] = EXTRACT.forecast_origin + T + EXTRACT.step

# pre-group by run_key for speed
GRP = {rk: g for rk, g in EXTRACT.groupby("run_key")}

WIDTH = {24: 6.6, 36: 7.6, 48: 8.6, 60: 10.0}


def draw(run_key, path):
    p = run_key.split("__")
    model = "__".join(p[1:-2])
    horizon = int(p[-2][1:])
    seed = p[-1][4:]
    color = MODEL_COLOR.get(model, "#444444")
    g = GRP[run_key]
    g = g[g.forecast_origin == ORIGIN].sort_values("step")
    pred_aw = ORIGIN + T + g.step.to_numpy()
    pred_y = g.y_pred_physical.to_numpy(np.float64)
    gt_y = ILI[pred_aw]
    mse = float(np.mean((gt_y - pred_y) ** 2))
    mae = float(np.mean(np.abs(gt_y - pred_y)))

    fig, ax = plt.subplots(figsize=(WIDTH[horizon], 3.0))
    ax.plot(pred_aw, gt_y, "-", color="#111111", lw=1.4)
    ax.plot(pred_aw, pred_y, "--", color=color, lw=1.4)
    ax.scatter([pred_aw[int(np.argmax(gt_y))]], [gt_y.max()], marker="*", s=110,
               color="#111111", zorder=5)
    ax.scatter([pred_aw[int(np.argmax(pred_y))]], [pred_y.max()], marker="v", s=55,
               color=color, zorder=5)
    tick = np.linspace(pred_aw.min(), pred_aw.max(), 6).astype(int)
    ax.set_xticks(tick)
    ax.set_xticklabels([CAL.get(int(a), "")[5:] for a in tick], rotation=30,
                       ha="right", fontsize=6.5)
    ax.set_ylabel("ILITOTAL", fontsize=7)
    ax.set_title(f"{model}  L{horizon}  seed={seed}   MSE={mse:.0f}  MAE={mae:.0f}",
                 fontsize=8)
    ax.grid(True, linestyle="--", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path); plt.close(fig)
    return mse, mae


def main():
    rows = []
    for rk in sorted(GRP):
        p = rk.split("__")
        arm = p[0]
        model = "__".join(p[1:-2])
        horizon = int(p[-2][1:])
        seed = p[-1][4:]
        path = GALLERY / f"{rk}.png"
        mse, mae = draw(rk, path)
        rows.append(dict(run_key=rk, arm=arm, model=model, horizon=horizon,
                         seed=seed, png=str(path.relative_to(ANALYSIS)),
                         ilitotal_mse_phys=mse, ilitotal_mae_phys=mae))
    idx = pd.DataFrame(rows)
    idx.to_csv(GALLERY / "index.csv", index=False)
    # manifest
    manifest = {
        "n_panels": len(idx),
        "source": "_tmp_audit/ili_ilitotal_extract.csv.gz (HPC durable evidence)",
        "forecast_origin": ORIGIN,
        "scale": "inverse-transformed ILITOTAL (physical)",
        "peak_markers": "true peak (*), predicted peak (v)",
        "layout": "forecast window only (ground truth + prediction + peaks)",
    }
    import json
    (GALLERY / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("wrote", len(idx), "panels + index.csv + manifest.json")
    print("size MB", sum(f.stat().st_size for f in GALLERY.glob("*.png")) / 1e6)


if __name__ == "__main__":
    main()
