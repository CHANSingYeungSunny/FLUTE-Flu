"""
extract_ablation.py — Extract and format Table VIII results.
Run after all ablation variants complete:
  python extract_ablation.py
"""
import pandas as pd, numpy as np, os, json

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Load ground truth
with open('miflu_ground_truth.json') as f:
    gt = json.load(f)
paper = gt['table_VIII_ablation']['schemes']

# Mapping: variant -> Table VIII name
variant_map = {
    "full":          "MIFlu",
    "no_dataset":    "MIFlu w/o Dataset information",
    "no_task":       "MIFlu w/o Task instruction",
    "no_vardesc":    "MIFlu w/o Input variable description",
    "no_lora":       "MIFlu w/o LoRA",
    "no_multi":      "MIFlu w/o multimodality",
    "no_lora_multi": "MIFlu w/o LoRA+multimodality",
}

print("=" * 70)
print("  Table VIII — Ablation Study Results")
print("=" * 70)
print()
print(f"  {'Scheme':<40s} {'Ours MSE':>10s} {'Paper MSE':>10s} {'Gap':>8s}")
print("  " + "-" * 70)

for variant, name in variant_map.items():
    csv_path = os.path.join(DATA_DIR, f"results_ablation_{variant}.csv")
    our_mse = None

    # Try ablation CSV first, then fall back to main results
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        our_mse = df['mse_all'].mean()
    elif variant == "no_multi":
        # Use baseline results
        bl_path = os.path.join(DATA_DIR, "results_baseline.csv")
        if os.path.exists(bl_path):
            df = pd.read_csv(bl_path)
            our_mse = df['mse_all'].mean()
    elif variant == "full":
        # Use MIFlu results
        mf_path = os.path.join(DATA_DIR, "results_miflu.csv")
        if os.path.exists(mf_path):
            df = pd.read_csv(mf_path)
            our_mse = df['mse_all'].mean()

    paper_mse = paper.get(name, {}).get("MSE", None) if name in paper else None

    if our_mse is not None:
        gap = f"{our_mse - paper_mse:+.4f}" if paper_mse else "N/A"
        print(f"  {name:<40s} {our_mse:>10.4f} {str(paper_mse) if paper_mse else 'N/A':>10s} {gap:>8s}")
    else:
        print(f"  {name:<40s} {'NOT RUN':>10s} {str(paper_mse) if paper_mse else 'N/A':>10s} {'—':>8s}")

print()
print("  Use: python extract_ablation.py after all variants complete")
