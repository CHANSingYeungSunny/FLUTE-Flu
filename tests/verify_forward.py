"""Smoke test: confirm MIFlu.forward returns 4 values and a fwd/bwd step runs.

Used to validate the train_ablation.py fix (y_hat_rev, y_phys, means, stdevs)
without burning a whole SLURM job. Runs on CPU with a tiny batch.
"""
import sys, os, torch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))
from miflu_model import MIFlu

dev = "cpu"
print("building MIFlu (L=24)...")
m = MIFlu(N=7, T=104, L=24, Lp=24, S=2, K=6, lora_r=4, device=dev)

bx = torch.randn(2, 7, 104)
print("forward with htext=None (the no_lora_multi / GPT4TS path)...")
out = m(bx, htext=None)
print("n_returns =", len(out))
assert len(out) == 4, f"expected 4 returns, got {len(out)}"
y_hat_rev, y_phys, means, stdevs = out
print("y_hat_rev", tuple(y_hat_rev.shape), "y_phys", tuple(y_phys.shape))

# one fwd/bwd step, exactly like train_ablation.train_epoch with htext=None
crit = torch.nn.MSELoss()
opt = torch.optim.AdamW([p for p in m.parameters() if p.requires_grad], lr=1e-4)
by = torch.randn(2, 7, 24)
opt.zero_grad(); yh, _, _, _ = m(bx, htext=None)
loss = crit(yh, by); loss.backward(); opt.step()
print("fwd/bwd OK, loss =", float(loss))
print("VERIFY_OK")
