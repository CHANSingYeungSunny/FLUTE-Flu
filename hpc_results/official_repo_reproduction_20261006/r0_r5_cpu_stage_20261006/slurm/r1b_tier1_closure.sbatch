#!/bin/bash
#SBATCH --job-name=r1b_tier1
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r0_r5_cpu_stage_20261006/logs/r1b_tier1_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r0_r5_cpu_stage_20261006/logs/r1b_tier1_%j.err
#
# ===========================================================================
# TIER-1 ENGINEERING CLOSURE   --   CPU-ONLY, ZERO GPU-HOURS
# ===========================================================================
# Closes the three R1-B acceptance gates that cannot run locally:
#   T19  LoRA modules exist                 (needs the real peft installed)
#   T20  intended LoRA parameters trainable
#   plus the exact trainable/frozen parameter inventory
#   T29  checkpoint save -> reload -> prediction equivalence
#
# No GPU is requested, so this costs ZERO GPU-hours by construction. It is the
# cheapest unblocking action available and requires no authorization.
#
# It imports the author's tree UNMODIFIED and the R1-B subclass from $HOME.
# ===========================================================================
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
R1B=${ROOT}/r0_r5_cpu_stage_20261006/r1b
COMPAT=${ROOT}/hpc_compat
A0=/scratch/sychan552/a0_replay
OUT=${ROOT}/r0_r5_cpu_stage_20261006/r1b
mkdir -p "${OUT}"

if [[ "$(hostname)" == hpclogin* ]]; then echo "[t1] REFUSING login node"; exit 3; fi
echo "[t1] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"

cd "${A0}" || exit 2
export PYTHONPATH="${COMPAT}:${A0}:${R1B}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
export OUTDIR="${OUT}"
export OUTJSON="${OUT}/tier1_closure_result.json"

$PY - <<'PYEOF'
import argparse, json, os, sys, numpy as np, torch
print(f"python {sys.version.split()[0]} | torch {torch.__version__} | "
      f"cuda_available {torch.cuda.is_available()}")

import peft
print(f"peft {peft.__version__}")

from r1b_model import R1BCorrectedMIFlu, run_text_influence_check

def cfg(L, peft_flag, mm=1):
    return argparse.Namespace(
        model_id="r1b", checkpoints="./c/", multimodal=mm, root_path="./d/",
        data_path="national_illness.csv", data="custom", features="M", freq=0,
        target="OT", embed="timeF", percent=100,
        lora_r=4, target_modules=["c_attn"],      # the author LIST default - never override
        PEFT=peft_flag, seq_len=104, pred_len=L, label_len=18, decay_fac=0.75,
        learning_rate=5e-4, batch_size=16, num_workers=0, train_epochs=20,
        lradj="type1", patience=3, gpt_layers=6, backbone="gpt2", textmodel="gpt2",
        e_layers=3, d_model=768, n_heads=4, d_ff=768, dropout=0.2,
        enc_in=7, c_out=7, patch_size=24, kernel_size=25, loss_func="mse",
        pretrain=1, freeze=1, model="model", stride=2, max_len=-1,
        hid_dim=16, tmax=10, itr=1, cos=0)

R = {"job": os.environ.get("SLURM_JOB_ID"), "host": os.environ.get("HOSTNAME"),
     "torch": torch.__version__, "peft": peft.__version__,
     "cuda_available": torch.cuda.is_available()}

torch.manual_seed(1234); np.random.seed(1234)
L, B, M = 24, 2, 7
TEXT_A = np.random.RandomState(0).randn(17, 768).astype(np.float32)
TEXT_B = np.random.RandomState(1).randn(17, 768).astype(np.float32)

# ── T19/T20: LoRA with PEFT=1 ────────────────────────────────────────────
m = R1BCorrectedMIFlu(cfg(L, peft_flag=1), torch.device("cpu"), text_embeddings=TEXT_A)
names = dict(m.named_parameters())
lora = {n: p for n, p in names.items() if "lora_" in n}
tgt  = {n: p for n, p in names.items() if "lora_" in n and "c_attn" in n}
tot  = sum(p.numel() for p in m.parameters())
trn  = sum(p.numel() for p in m.parameters() if p.requires_grad)
ltot = sum(p.numel() for p in lora.values())
print(f"\n[t1] total={tot:,}  trainable={trn:,} ({100*trn/tot:.2f}%)")
print(f"[t1] LoRA tensors={len(lora)}  LoRA params={ltot:,}  c_attn-LoRA tensors={len(tgt)}")

R["T19_lora_tensors"] = len(lora)
R["T19_lora_params"] = int(ltot)
R["T19_c_attn_lora_tensors"] = len(tgt)
R["T19_example_names"] = sorted(lora)[:6]
R["T19_PASS"] = len(lora) > 0 and len(tgt) > 0

non_lora_trainable = sorted(n for n, p in names.items()
                            if p.requires_grad and "lora_" not in n)
R["T20_non_lora_trainable"] = non_lora_trainable[:20]
R["T20_non_lora_trainable_count"] = len(non_lora_trainable)
R["T20_PASS"] = (ltot > 0 and trn < tot * 0.5
                 and all(("ln" in n or "wpe" in n or n.startswith(("in_layer", "out_layer")))
                         for n in non_lora_trainable))
print(f"[t1] non-LoRA trainable tensors: {len(non_lora_trainable)}  "
      f"e.g. {non_lora_trainable[:3]}")

# frozen base parameters must be False
frozen = [n for n, p in names.items() if not p.requires_grad]
R["frozen_tensor_count"] = len(frozen)
R["frozen_examples"] = frozen[:6]
R["freeze_report"] = m.freeze_report
R["total_parameters"] = int(tot)
R["trainable_parameters"] = int(trn)
R["trainable_fraction"] = trn / tot
print(f"[t1] frozen tensors={len(frozen)}  trainable fraction={trn/tot:.4f}")

# ── T15/T16 restated on HPC: text influence with PEFT=1 ──────────────────
x = torch.randn(B, 104, M)
inf = run_text_influence_check(m, x, TEXT_A, TEXT_B)
R["text_influence_PEFT1"] = inf
print(f"[t1] PEFT=1 text influence: max|d|={inf['max_abs_prediction_difference']:.4e} "
      f"grad={inf['text_embedding_grad_norm']:.4e} -> {inf['verdict']}")

# ── T29: checkpoint save -> reload -> prediction equivalence ─────────────
with torch.no_grad():
    y_before = m(x, 0).detach().clone()
p = f"{os.environ.get('OUTDIR','/tmp')}/tier1_ckpt.pth"
torch.save(m.state_dict(), p)
m2 = R1BCorrectedMIFlu(cfg(L, peft_flag=1), torch.device("cpu"), text_embeddings=TEXT_A)
m2.load_state_dict(torch.load(p, map_location="cpu"), strict=True)
m2.eval()
with torch.no_grad():
    y_after = m2(x, 0).detach()
d = float((y_before - y_after).abs().max())
R["T29_max_abs_reload_diff"] = d
R["T29_checkpoint_bytes"] = os.path.getsize(p)
R["T29_PASS"] = d < 1e-6
print(f"[t1] reload max|d|={d:.3e}  ckpt={os.path.getsize(p):,} bytes  "
      f"-> {'PASS' if d < 1e-6 else 'FAIL'}")

# ── PEFT=0 control: confirm the flag actually changes the architecture ───
m0 = R1BCorrectedMIFlu(cfg(L, peft_flag=0), torch.device("cpu"), text_embeddings=TEXT_A)
t0 = sum(p.numel() for p in m0.parameters() if p.requires_grad)
l0 = sum(1 for n, _ in m0.named_parameters() if "lora_" in n)
R["peft0_control"] = {"trainable": int(t0), "lora_tensors": l0}
R["peft_flag_changes_architecture"] = (l0 == 0 and t0 < trn)
print(f"[t1] PEFT=0 control: trainable={t0:,} lora_tensors={l0}  "
      f"-> PEFT flag changes the architecture: {R['peft_flag_changes_architecture']}")

R["T19_T20_T29_ALL_PASS"] = bool(R["T19_PASS"] and R["T20_PASS"] and R["T29_PASS"])

out = os.environ.get("OUTJSON", "/tmp/tier1.json")
json.dump(R, open(out, "w"), indent=2, default=str)
print(f"\n[t1] wrote {out}")
print(f"[t1] ALL PASS = {R['T19_T20_T29_ALL_PASS']}")
PYEOF
rc=$?
echo "[t1] exit=${rc} end=$(date -u +%FT%TZ)"
exit ${rc}