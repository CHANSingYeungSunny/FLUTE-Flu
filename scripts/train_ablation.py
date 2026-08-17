"""
train_ablation.py — Table VIII Ablation Variants
==================================================
Runs MIFlu ablation variants via --variant flag.

Variants (matching Table VIII):
  full        = MIFlu (text + LoRA + all prompt sections)
  no_dataset  = w/o Dataset information section
  no_task     = w/o Task instruction section
  no_vardesc  = w/o Input variable description section
  no_lora     = w/o LoRA (only PE + LN trainable)
  no_multi    = w/o multimodality (no text, LoRA kept) = baseline
  no_lora_multi = w/o LoRA + multimodality (no text, no LoRA)

Usage:
  python train_ablation.py --variant no_dataset
  python train_ablation.py --variant no_lora
"""

import torch, torch.nn as nn, numpy as np, pandas as pd, os, sys, time, argparse
from datetime import datetime
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(__file__))
from miflu_model import MIFlu
from textual_embedder import TextualInputEmbedder, build_prompt, PROMPT_TEMPLATE

# ── Config (Table IV) ──────────────────────────────────────────────────────
CONFIG = {
    "T": 104, "L_list": [24, 36, 48, 60], "N": 7,
    "Lp": 24, "S": 2, "K": 6, "lora_r": 4, "D": 768,
    "batch_size": 16, "learning_rate": 0.0005, "epochs": 20,
    "num_repetitions": 10,
}

VAR_COLS = [
    "% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
    "ILITOTAL", "NUM. OF PROVIDERS", "OT",
]

BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "raw", "national_illness_raw.csv")

# ── Prompt variant builders ────────────────────────────────────────────────

def build_prompt_no_dataset(train_df, T, L):
    """Remove [Dataset information] section."""
    prompt = build_prompt(train_df, T, L)
    # Remove from start to first ***
    idx = prompt.find("***")
    return prompt[idx:] if idx > 0 else prompt

def build_prompt_no_task(train_df, T, L):
    """Remove [Task instruction] section."""
    prompt = build_prompt(train_df, T, L)
    idx = prompt.rfind("*** [Task instruction]")
    return prompt[:idx].rstrip() if idx > 0 else prompt

def build_prompt_no_vardesc(train_df, T, L):
    """Remove [Input variable description] section, keep only headers."""
    prompt = build_prompt(train_df, T, L)
    # Keep Dataset info + Task instruction, remove middle section
    parts = prompt.split("***")
    if len(parts) >= 3:
        return parts[0] + "***\n" + parts[2]
    return prompt

# ── Logging ─────────────────────────────────────────────────────────────────
_log_file = None

def log_init(path):
    global _log_file
    os.makedirs(os.path.dirname(path), exist_ok=True)
    _log_file = open(path, "w", encoding="utf-8", buffering=1)

def log(msg=""):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    if _log_file: _log_file.write(line + "\n")

# ── Data ────────────────────────────────────────────────────────────────────
def load_and_normalize():
    df = pd.read_csv(DATA_PATH)
    data = df[VAR_COLS].values.astype(np.float32)
    n = len(data)
    t_end, v_end = int(n * 0.70), int(n * 0.70) + int(n * 0.10)
    train_mean = data[:t_end].mean(axis=0, keepdims=True)
    train_std  = data[:t_end].std(axis=0, keepdims=True) + 1e-8
    data_norm = (data - train_mean) / train_std
    log(f"Data: {n} total | Train={t_end} | Val={v_end-t_end} | Test={n-v_end}")
    return {"data_norm": data_norm, "train_end": t_end, "val_end": v_end,
            "train_df": df.iloc[:t_end]}

def build_windows(data_norm, T, L, train_end, val_end):
    total = data_norm.shape[0]; nw = total - T - L + 1
    X = np.zeros((nw, CONFIG["N"], T), dtype=np.float32)
    Y = np.zeros((nw, CONFIG["N"], L), dtype=np.float32)
    splits = np.zeros(nw, dtype=np.int8)
    for i in range(nw):
        X[i] = data_norm[i:i+T].T; Y[i] = data_norm[i+T:i+T+L].T
        splits[i] = 0 if (i+T) < train_end else (1 if (i+T) < val_end else 2)
    return (X[splits==0], Y[splits==0], X[splits==1], Y[splits==1], X[splits==2], Y[splits==2])

# ── Training ────────────────────────────────────────────────────────────────
def train_epoch(model, loader, opt, crit, dev, prompt_cache):
    model.train(); loss_sum = 0.0
    for bx, by in loader:
        bx, by = bx.to(dev), by.to(dev); bsz = bx.size(0)
        ht = prompt_cache.expand(bsz, -1, -1) if prompt_cache is not None and prompt_cache.shape[0] == 1 else (prompt_cache[:bsz] if prompt_cache is not None else None)
        opt.zero_grad(); yh, _, _ = model(bx, htext=ht)
        L = crit(yh, by); L.backward(); opt.step()
        loss_sum += L.item() * bsz
    return loss_sum / len(loader.dataset)

@torch.no_grad()
def evaluate(model, loader, crit, dev, prompt_cache):
    model.eval(); preds, targets = [], []
    for bx, by in loader:
        bx = bx.to(dev); bsz = bx.size(0)
        ht = prompt_cache.expand(bsz, -1, -1) if prompt_cache is not None and prompt_cache.shape[0] == 1 else (prompt_cache[:bsz] if prompt_cache is not None else None)
        yh, _, _ = model(bx, htext=ht)
        preds.append(yh.cpu().numpy()); targets.append(by.numpy())
    p = np.concatenate(preds); t = np.concatenate(targets)
    mse_all = np.mean((p-t)**2); mae_all = np.mean(np.abs(p-t))
    mse_ili = np.mean((p[:,4,:]-t[:,4,:])**2)
    return mse_all, mae_all, mse_ili, np.mean(np.abs(p[:,4,:]-t[:,4,:]))

def train_L(data_dict, L, config, device, prompt_cache, use_lora, use_text):
    Xt, Yt, Xv, Yv, Xte, Yte = build_windows(
        data_dict["data_norm"], config["T"], L, data_dict["train_end"], data_dict["val_end"])
    log(f"  L={L}: train={len(Xt)} val={len(Xv)} test={len(Xte)} windows")

    tl = DataLoader(TensorDataset(torch.from_numpy(Xt), torch.from_numpy(Yt)), batch_size=config["batch_size"], shuffle=True)
    vl = DataLoader(TensorDataset(torch.from_numpy(Xv), torch.from_numpy(Yv)), batch_size=config["batch_size"], shuffle=False)
    el = DataLoader(TensorDataset(torch.from_numpy(Xte), torch.from_numpy(Yte)), batch_size=config["batch_size"], shuffle=False)

    model = MIFlu(N=config["N"], T=config["T"], L=L, Lp=config["Lp"],
                  S=config["S"], K=config["K"], lora_r=config["lora_r"], device=device)

    # ── Control LoRA ──
    if not use_lora:
        # Freeze all LoRA parameters
        for lm in model.forecasting_llm.lora_modules:
            lm.lora_A.requires_grad = False
            lm.lora_B.requires_grad = False

    opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=config["learning_rate"])
    crit = nn.MSELoss()

    for ep in range(config["epochs"]):
        t0 = time.time()
        tl_loss = train_epoch(model, tl, opt, crit, device, prompt_cache if use_text else None)
        v_mse_all, v_mae_all, v_mse_ili, v_mae_ili = evaluate(model, vl, crit, device, prompt_cache if use_text else None)
        dt = time.time() - t0
        log(f"    ep {ep+1:2d}/{config['epochs']} | train_loss={tl_loss:.6f} | val_mse={v_mse_all:.6f}(All) {v_mse_ili:.4f}(ILI) | val_mae={v_mae_all:.6f} | {dt:.1f}s | GPU={torch.cuda.memory_allocated()/1e9:.2f}GB" if device=="cuda" else f"    ep {ep+1:2d} | train_loss={tl_loss:.6f} | val_mse={v_mse_all:.6f}(All) | val_mae={v_mae_all:.6f} | {dt:.1f}s")
    t_mse_all, t_mae_all, t_mse_ili, t_mae_ili = evaluate(model, el, crit, device, prompt_cache if use_text else None)
    log(f"  L={L} DONE: test_mse={t_mse_all:.6f}(All) {t_mse_ili:.4f}(ILI) test_mae={t_mae_all:.6f}")
    del model; torch.cuda.empty_cache() if device=="cuda" else None
    return {"L": L, "test_mse_all": t_mse_all, "test_mae_all": t_mae_all,
            "test_mse_ili": t_mse_ili, "test_mae_ili": t_mae_ili}

# ── Main ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", type=str, default="full",
                       choices=["full","no_dataset","no_task","no_vardesc",
                               "no_lora","no_multi","no_lora_multi"])
    args = parser.parse_args()

    # Variant configuration
    variants = {
        "full":          {"use_text": True,  "use_lora": True,  "prompt_fn": build_prompt, "name": "MIFlu (full)"},
        "no_dataset":    {"use_text": True,  "use_lora": True,  "prompt_fn": build_prompt_no_dataset, "name": "w/o Dataset information"},
        "no_task":       {"use_text": True,  "use_lora": True,  "prompt_fn": build_prompt_no_task, "name": "w/o Task instruction"},
        "no_vardesc":    {"use_text": True,  "use_lora": True,  "prompt_fn": build_prompt_no_vardesc, "name": "w/o Input variable description"},
        "no_lora":       {"use_text": True,  "use_lora": False, "prompt_fn": build_prompt, "name": "w/o LoRA"},
        "no_multi":      {"use_text": False, "use_lora": True,  "prompt_fn": None, "name": "w/o multimodality"},
        "no_lora_multi": {"use_text": False, "use_lora": False, "prompt_fn": None, "name": "w/o LoRA+multimodality"},
    }
    v = variants[args.variant]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    LOG_PATH = os.path.join(BASE_DIR, "data", f"training_ablation_{args.variant}_log.txt")
    RESULTS_PATH = os.path.join(BASE_DIR, "data", f"results_ablation_{args.variant}.csv")
    log_init(LOG_PATH)

    log("=" * 60)
    log(f"  Table VIII Ablation: {v['name']}")
    log("=" * 60)
    log(f"  Variant: {args.variant}")
    log(f"  use_text={v['use_text']}, use_lora={v['use_lora']}")
    log(f"  Config: T={CONFIG['T']}, K={CONFIG['K']}, Lp={CONFIG['Lp']}, S={CONFIG['S']}")
    log(f"  batch={CONFIG['batch_size']}, lr={CONFIG['learning_rate']}, epochs={CONFIG['epochs']}, reps={CONFIG['num_repetitions']}")
    log()

    data_dict = load_and_normalize(); log()

    # Build text embedder if needed
    text_embedder = None
    if v['use_text']:
        log("Loading GPT2 text embedder...")
        text_embedder = TextualInputEmbedder(device=device)
    log()

    # Resume: skip L values already completed in existing CSV
    completed_Ls = set()
    if os.path.exists(RESULTS_PATH):
        existing = pd.read_csv(RESULTS_PATH)
        for L_val in CONFIG["L_list"]:
            count = len(existing[existing['L'] == L_val])
            if count >= CONFIG["num_repetitions"]:
                completed_Ls.add(L_val)
                log(f"  [RESUME] L={L_val}: {count} reps already done, skipping")
        if completed_Ls:
            all_rows = existing.to_dict('records')
        else:
            all_rows = []
    else:
        all_rows = []
    t_start = time.time()

    for L in CONFIG["L_list"]:
        if L in completed_Ls:
            continue
        log(f"{'─'*50}"); log(f"  HORIZON L={L}"); log(f"{'─'*50}")

        # Build prompt if using text
        prompt_cache = None
        if v['use_text'] and v['prompt_fn'] is not None:
            prompt = v['prompt_fn'](data_dict["train_df"], T=CONFIG["T"], L=L)
            prompt_cache = text_embedder(prompt)

        L_reps = []
        for rep in range(CONFIG["num_repetitions"]):
            log(f"  [L={L}] Rep {rep+1}/{CONFIG['num_repetitions']} ...")
            r = train_L(data_dict, L, CONFIG, device, prompt_cache, v['use_lora'], v['use_text'])
            L_reps.append(r)
            all_rows.append({"L": L, "rep": rep+1,
                "mse_all": r["test_mse_all"], "mae_all": r["test_mae_all"],
                "mse_ili": r["test_mse_ili"], "mae_ili": r["test_mae_ili"]})
            pd.DataFrame(all_rows).to_csv(RESULTS_PATH, index=False)

        avg_mse = np.mean([r["test_mse_all"] for r in L_reps])
        avg_mae = np.mean([r["test_mae_all"] for r in L_reps])
        log(f"  [L={L}] FINAL: MSE_AllVars={avg_mse:.6f} MAE={avg_mae:.6f}"); log()

    df = pd.DataFrame(all_rows)
    summary = df.groupby("L").agg(mse_all=("mse_all","mean"), mae_all=("mae_all","mean"))
    avg_mse = summary["mse_all"].mean()
    log("=" * 60); log(f"  ABLATION COMPLETE: {v['name']}"); log("=" * 60)
    log(f"  Avg MSE_AllVars: {avg_mse:.6f}")
    log(f"  Total time: {(time.time()-t_start)/60:.1f} min")
    log(f"  Results: {RESULTS_PATH}")
    log_close()

    # Print final MSE for easy extraction
    print(f"\nABLATION_RESULT: variant={args.variant} mse_all={avg_mse:.6f}")

if __name__ == "__main__":
    main()
