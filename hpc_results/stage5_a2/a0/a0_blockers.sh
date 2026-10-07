#!/bin/bash
#SBATCH --job-name=a0_blockers
#SBATCH --partition=stingy
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/sychan552/a2_stage5/logs/a0_blockers_%j.out
#SBATCH --error=/scratch/sychan552/a2_stage5/logs/a0_blockers_%j.err
# CPU-only => ZERO GPU-hours.
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
A0=/scratch/sychan552/a0_replay
export HF_HOME=/home/sychan552/.cache/huggingface TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
echo "[a0b] $(date -u +%FT%TZ) host=$(hostname)"

echo
echo "=== B1. is einops obtainable without network? ==="
ls -d /home/sychan552/.conda/envs/*/lib/python*/site-packages/einops 2>/dev/null | sed 's/^/  found-in-env: /'
find /home/sychan552/.cache/pip /home/sychan552/.conda -maxdepth 6 -iname "einops*" 2>/dev/null | head -5 | sed 's/^/  cached: /'
$PY -c "import einops" 2>&1 | tail -1 | sed 's/^/  import: /'
echo "  => einops is a pure-python wheel with no compiled extension; if no copy is"
echo "     cached it needs ONE network install (pip install einops) or a vendored"
echo "     substitute. Neither is present in the current environment."

echo
echo "=== B2. what does models/GPT4TS_lora.py actually need from embed.py? ==="
grep -n -E "DataEmbedding|from embed|import embed" "$A0/models/"*.py | sed 's/^/  /'

echo
echo "=== B3. is the released embed module recoverable from its .pyc? ==="
ls -la "$A0/__pycache__/" 2>/dev/null | sed 's/^/  /'
$PY - <<'PY' 2>&1 | sed 's/^/  /'
import dis, importlib.util, marshal, os, sys
p = "/scratch/sychan552/a0_replay/__pycache__/embed.cpython-39.pyc"
if not os.path.exists(p):
    print("no .pyc present"); raise SystemExit
data = open(p, "rb").read()
print("pyc magic", data[:4].hex(), "python", sys.version.split()[0])
try:
    code = marshal.loads(data[16:])
except Exception as e:
    print("marshal failed:", e); raise SystemExit
print("co_names  :", sorted(set(code.co_names))[:40])
consts = [c for c in code.co_consts if isinstance(c, str)]
print("doc/strs  :", consts[:12])
def walk(c, d=0):
    for k in c.co_consts:
        if hasattr(k, "co_name"):
            print("  " * d + f"class/def {k.co_name}  args={k.co_varnames[:k.co_argcount]}")
            walk(k, d + 1)
walk(code)
PY

echo
echo "=== B4. does the PROJECT already contain an equivalent embedding module? ==="
for p in /scratch/sychan552/a2_stage5/scripts/innovation/encoders/gpt2_encoder.py \
         /scratch/sychan552/a2_stage5/scripts/innovation/encoders/none_encoder.py; do
  [ -f "$p" ] && echo "  present: $p ($(stat -c%s "$p") bytes)"
done
grep -rln "class DataEmbedding" /scratch/sychan552/a2_stage5/scripts 2>/dev/null | sed 's/^/  DataEmbedding found in: /' | head
echo "  => no DataEmbedding/DataEmbedding_wo_time implementation ships with the"
echo "     project either; a faithful reconstruction would be NEW code, not the"
echo "     author's, and must be recorded as a deviation."

echo
echo "=== B5. can the released model file be made importable with a STUB embed? ==="
# Prove that embed.py + einops are the ONLY import blockers, by stubbing them
# in a throwaway sys.path entry. Nothing in the author's tree is modified.
STUB=$(mktemp -d)
cat > "$STUB/einops.py" <<'EOS'
def rearrange(tensor, pattern, **axes):
    # minimal subset used by GPT4TS_lora: 'b l m -> b m l' and 'b m n p -> (b m) n p'
    import torch
    if pattern == "b l m -> b m l":
        return tensor.permute(0, 2, 1)
    if pattern == "b m n p -> (b m) n p":
        b, m, n, p = tensor.shape
        return tensor.reshape(b * m, n, p)
    if pattern == "(b m) l -> b l m":
        bm, l = tensor.shape
        b = bm // 7
        return tensor.reshape(b, 7, l).permute(0, 2, 1)
    raise NotImplementedError(pattern)
EOS
cat > "$STUB/embed.py" <<'EOS'
import torch, torch.nn as nn
class DataEmbedding(nn.Module):
    def __init__(self, c_in, d_model, embed='fixed', freq='h', dropout=0.1, **kw):
        super().__init__()
        self.value_embedding = nn.Linear(c_in, d_model)
        self.dropout = nn.Dropout(dropout)
    def forward(self, x, x_mark=None):
        return self.dropout(self.value_embedding(x))
class DataEmbedding_wo_time(nn.Module):
    def __init__(self, c_in, d_model, dropout=0.1, **kw):
        super().__init__()
        self.value_embedding = nn.Linear(c_in, d_model)
        self.dropout = nn.Dropout(dropout)
    def forward(self, x):
        return self.dropout(self.value_embedding(x))
EOS
cd "$A0"
PYTHONPATH="$STUB:$A0" $PY - <<'PY' 2>&1 | sed 's/^/  /'
import sys, torch
sys.path.insert(0, "/scratch/sychan552/a0_replay")
import models.GPT4TS_lora as G
print("import models.GPT4TS_lora: OK (with stub einops + stub embed)")
m = G.GPT4TS(seq_len=104, pred_len=24, patch_size=24, stride=2, d_model=768,
             n_heads=4, e_layers=3, d_ff=768, dropout=0.2, gpt_layers=6,
             multitask=0, enc_in=7, c_out=7, textmodel="gpt2", multimodal=0,
             lora_r=4, PEFT=0)
tot = sum(p.numel() for p in m.parameters())
tr = sum(p.numel() for p in m.parameters() if p.requires_grad)
frozen = tot - tr
print(f"params total={tot:,} trainable={tr:,} effectively_frozen={frozen:,}")
x = torch.randn(4, 1, 104)
with torch.no_grad():
    y = m(x)
print("forward(x[4,1,104]) ->", tuple(y.shape))
print("=> NOTE: this instantiation proves importability ONLY. The stub embed is")
print("   NOT the author's module and MUST NOT be used for any reported number.")
PY
rm -rf "$STUB"

echo
echo "[a0b] blocker analysis done $(date -u +%FT%TZ)"
