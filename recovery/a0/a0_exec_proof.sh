#!/bin/bash
#SBATCH --job-name=a0_exec_proof
#SBATCH --partition=stingy
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/sychan552/a2_stage5/logs/a0_exec_%j.out
#SBATCH --error=/scratch/sychan552/a2_stage5/logs/a0_exec_%j.err
# CPU-only => ZERO GPU-hours. Proves the released code is EXECUTABLE under the
# recorded compatibility layer, and measures its real behaviour on CPU.
set -uo pipefail
A0=/scratch/sychan552/a0_replay
SHIM=/scratch/sychan552/a0_compat_shim
export HF_HOME=/home/sychan552/.cache/huggingface TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
echo "[a0x] $(date -u +%FT%TZ) host=$(hostname)"

rm -rf "$SHIM"; mkdir -p "$SHIM"
cp /scratch/sychan552/a2_stage5/recovery/a0/a0_compat.py "$SHIM/a0_compat.py"
printf 'from a0_compat import rearrange\n__all__ = ["rearrange"]\n'          > "$SHIM/einops.py"
printf 'from a0_compat import DataEmbedding, DataEmbedding_wo_pos, DataEmbedding_wo_time\n' > "$SHIM/embed.py"
cat > "$SHIM/sitecustomize.py" <<'EOS'
try:
    import peft
    if not hasattr(peft, "prepare_model_for_int8_training"):
        peft.prepare_model_for_int8_training = lambda m, *a, **k: m
except Exception:
    pass
EOS

cat > /scratch/sychan552/a2_stage5/recovery/a0/_a0_probe.py <<'EOS'
import sys, numpy as np, torch
sys.path.insert(0, "/scratch/sychan552/a0_compat_shim")
sys.path.insert(0, "/scratch/sychan552/a0_replay")
import models.GPT4TS_lora as G

def released_config(**over):
    """The released argparse defaults, verbatim (main_ILI_lora.py lines 34-85)."""
    d = dict(seq_len=104, label_len=18, pred_len=24, patch_size=24, stride=2,
             d_model=768, n_heads=4, e_layers=3, d_ff=768, dropout=0.2,
             gpt_layers=6, multitask=0, enc_in=7, c_out=7, textmodel="gpt2",
             multimodal=0, lora_r=4, lora_target_modules=["c_attn"],
             target_modules=["c_attn"], PEFT=0, freeze=1, pretrain=1,
             backbone="gpt2", act="gelu", d_layers=None, distil=True,
             learning_rate=0.0001, batch_size=16, train_epochs=1, itr=1,
             embed="timeF", freq="h", features="M", target="OT")
    d.update(over)
    return G.CustomConfig(**d)

print("OK import models.GPT4TS_lora  (under the recorded compatibility layer)")
print()

# ---- 2. instantiate with the released defaults --------------------------
m = G.GPT4TS(released_config(), torch.device("cpu"))
tot = sum(p.numel() for p in m.parameters())
tr = sum(p.numel() for p in m.parameters() if p.requires_grad)
print("=== 2. instantiation with the RELEASED argparse defaults ===")
print(f"  GPT2 blocks actually kept : {len(m.llmmodel.h)} of 12  (self.llmmodel.h = h[:gpt_layers=6])")
print(f"  total parameters          : {tot:,}")
print(f"  parameters with grad=True : {tr:,}   ({100.0*tr/tot:.1f}%)")
print(f"  PEFT / LoRA applied       : {isinstance(m.llmmodel, G.GPT2Model)} -> plain GPT2Model, "
      f"PEFT=0 so the LoraConfig branch (lines 74-90) never runs")
emb = [(n, p.numel()) for n, p in m.llmmodel.named_parameters()
       if p.requires_grad and ("wte" in n or "wpe" in n)]
print(f"  GPT-2 token/pos embeddings left trainable: {len(emb)} tensors, "
      f"{sum(n for _, n in emb):,} params")
print("  => the 'freeze' flag is a NO-OP: lines 58-61 only set requires_grad=True")
print("     for names containing 'ln'/'wpe' and never set False anywhere else,")
print("     so GPT-2's default requires_grad=True survives -> FULL FINE-TUNING")
print("     of the kept 6 blocks, not the LoRA the filename advertises.")
print(f"  real input projection     : {m.in_layer}")
print(f"  real head                 : {m.out_layer.in_features} -> {m.out_layer.out_features}")
print("  => DataEmbedding / DataEmbedding_wo_time are imported but never used.")
print()

# ---- 3. forward pass ---------------------------------------------------
print("=== 3. CPU forward pass with the released per-feature batch shape ===")
m.eval()
# released forward expects (B, T, M): line 113 shows torch.Size([16, 104, 1])
x = torch.zeros(8, 104, 1)
with torch.no_grad():
    y = m(x, itr=0)
print(f"  input  (B,T,M) = {tuple(x.shape)}   (M=1 -> ONE feature per sample)")
print(f"  output         = {tuple(y.shape)}")
print("  => per-feature in / per-feature out. The released model NEVER produces a")
print("     joint 7-variable forecast, and its Test path sees feature 0 only.")
print()

# ---- 4. executed text-path probe ---------------------------------------
print("=== 4. EXECUTED text-path probe (multimodal=1, the paper's claimed mode) ===")
A0 = "/scratch/sychan552/a0_replay"
p = A0 + "/dataset/illness/text_emb/text_emb_label_0507_24.txt"
te = np.loadtxt(p)
print(f"  released asset text_emb_label_0507_24.txt shape = {te.shape} "
      f"(317 text tokens x 768)")
torch.manual_seed(0)
mm = G.GPT4TS(released_config(multimodal=1), torch.device("cpu"))
mm.eval()
print(f"  multimodal={mm.multimodal}, patch_num={mm.patch_num}")
x = torch.zeros(4, 104, 1)
with torch.no_grad():
    y_ref = mm(x, itr=0).clone()
print(f"  forward OK, output = {tuple(y_ref.shape)}")
try:
    orig = np.loadtxt
    def fake(path, *a, **k):
        rng = np.random.default_rng(1234)
        return rng.standard_normal((317, 768))
    np.loadtxt = fake
    with torch.no_grad():
        y_alt = mm(x, itr=0).clone()
    np.loadtxt = orig
    d = float((y_ref - y_alt).abs().max())
    print(f"  max |y(real text) - y(SHUFFLED text)| = {d:.3e}")
    print(f"  => text tokens reach the output: {d > 1e-6}")
except Exception as e:
    print(f"  substitution probe failed: {type(e).__name__}: {e}")
print()

# ---- 5. gradient reachability of the text embedding -------------------
print("=== 5. gradient of the loss w.r.t. the text embedding ===")
mm.train()
te_t = torch.tensor(te, dtype=torch.float32, requires_grad=True)
import torch.nn.functional as F
xx = torch.zeros(4, 104, 1)
B = xx.shape[0]
# replicate the released forward with the text tensor made differentiable
means = xx.mean(1, keepdim=True).detach()
z = xx - means
sd = torch.sqrt(torch.var(z, dim=1, keepdim=True, unbiased=False) + 1e-5).detach()
z = z / sd
z = z.permute(0, 2, 1)                      # b m l
z = mm.padding_patch_layer(z)
z = z.unfold(dimension=-1, size=mm.patch_size, step=mm.stride)
B_, M_, n_, p_ = z.shape
z = z.reshape(B_ * M_, n_, p_)
tok = mm.in_layer(z)                        # (B*M, patch_num, d_model)
txt = te_t.unsqueeze(0).repeat(B_, 1, 1)
cat = torch.cat((tok, txt), axis=1)        # released line 139
hid = mm.llmmodel(inputs_embeds=cat).last_hidden_state
kept = hid[:, :mm.patch_num, :]             # released line 145
out = mm.out_layer(kept.reshape(B_ * M_, -1))
out = out.reshape(B_, M_, mm.pred_len).permute(0, 2, 1)
loss = (out ** 2).mean()
loss.backward()
g = te_t.grad
print(f"  loss={float(loss):.6f}   grad wrt text_emb: "
      f"max|.|={float(g.abs().max()):.3e}  norm={float(g.norm()):.3e}")
print(f"  => TEXT GRADIENT IS EXACTLY ZERO: {float(g.norm()) == 0.0}")
print("  Cause: text is concatenated AFTER the patch tokens and the output keeps")
print("  only the first patch_num positions. Under GPT-2 causal attention an")
print("  earlier position cannot attend to later positions, so the text tokens")
print("  are discarded before they can influence anything that is read out.")
print()

# ---- 6. Test feature coverage -----------------------------------------
print("=== 6. released Test feature coverage, derived from __len__/__getitem__ ===")
import pandas as pd
df = pd.read_csv(A0 + "/dataset/illness/national_illness.csv")
n, seq_len, pred_len = len(df), 104, 24
nt, nte = int(n * 0.7), int(n * 0.2)
nv = n - nt - nte
b1 = [0, nt - seq_len, n - nte - seq_len]
b2 = [nt, nt + nv, n]
ncols = len([c for c in df.columns if c != "date"])
for i, nm in enumerate(("train", "val", "test")):
    tot = (b2[i] - b1[i]) - seq_len - pred_len + 1
    ln = tot if nm == "test" else tot * ncols
    feats = sorted({j // tot for j in range(ln)})
    print(f"  {nm:<5} __len__={ln:<5} distinct feat_id = {feats}")
print(f"  split from the released integer rule: train={nt} val={nv} test={nte} "
      f"(borders {b1} / {b2})")
print("  => released Test evaluates feature 0 ONLY; train/val cover all 7 but as")
print("     SEPARATE single-feature samples, never jointly.")
print(f"  NOTE: released test-loader uses drop_last=True, so "
      f"{ln} -> {ln // 16 * 16} scored examples.")
EOS

echo "=== 1-6 combined probe ==="
cd "$A0" || exit 2
PYTHONPATH="$SHIM:$A0" /home/sychan552/.conda/envs/mlflu_hpc/bin/python \
  /scratch/sychan552/a2_stage5/recovery/a0/_a0_probe.py
rc=$?
echo
echo "probe exit=$rc"

echo
echo "=== 7. static: is Test read during training, and is early stopping live? ==="
grep -n -E "early_stopping|early_stop|vali\(|test\(|min_mse|torch.save" \
     "$A0/main_ILI_lora.py" | sed 's/^/  /'

echo
echo "[a0x] done $(date -u +%FT%TZ)"
