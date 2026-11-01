"""Smoke test: single-variable (N=1) batching plumbing vs packed N=7 model."""
import os, sys, io, torch
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from miflu_model import MIFlu          # noqa: E402
from train_miflu import forward_all_vars  # noqa: E402

T, L, Lp, S, K, r = 104, 24, 24, 2, 6, 4
dev = "cpu"
torch.manual_seed(0)

common = dict(T=T, L=L, Lp=Lp, S=S, K=K, lora_r=r, device=dev, flatten_head=True)
m1 = MIFlu(N=1, **common).eval()
m7 = MIFlu(N=7, **common).eval()
# identical parameter set? (N must not change parameters)
sd1, sd7 = m1.state_dict(), m7.state_dict()
same_keys = set(sd1) == set(sd7)
print("same param keys:", same_keys, "| n params:", len(sd1))
if same_keys:
    bad = [k for k in sd1 if sd1[k].shape != sd7[k].shape]
    print("shape mismatches:", len(bad), bad[:5])
    m7.load_state_dict(sd1)          # share weights so outputs must match
    print("load_state_dict(N=1 -> N=7): OK")

B, TEXT = 4, 369
x_all = torch.randn(B, 7, T)
ht = torch.randn(B, TEXT, 768)
tm = torch.randn(1, 7); ts = torch.rand(1, 7) + 0.5

# 1) single-variable forward on N=1 model
x_sv = torch.randn(B, 1, T)
o = m1(x_sv, htext=ht, train_mean=tm[:, :1], train_std=ts[:, :1])
print("N=1 single-var out:", tuple(o[0].shape), "expect", (B, 1, L))

# 2) all-variable forward through the looping helper
o_all = forward_all_vars(m1, x_all, ht, tm, ts)
print("forward_all_vars out:", tuple(o_all[0].shape), "expect", (B, 7, L))

# 3) equivalence: N=7 packed model vs N=1 looped model (same weights)
o7 = m7(x_all, htext=ht, train_mean=tm, train_std=ts)
d = (o_all[0] - o7[0]).abs().max().item()
print(f"max|N=1-loop - N=7-packed| = {d:.3e}   (want ~0)")

# 4) a real gradient step with author-style 16 single-variable samples
m1.train()
opt = torch.optim.Adam([p for p in m1.parameters() if p.requires_grad], lr=1e-4)
xb = torch.randn(16, 1, T); yb = torch.randn(16, 1, L)
opt.zero_grad()
yh = m1(xb, htext=torch.randn(16, TEXT, 768), train_mean=tm[:, :1], train_std=ts[:, :1])[0]
loss = torch.nn.functional.mse_loss(yh, yb)
loss.backward(); opt.step()
print("train step (B=16 single-var): OK  loss=%.4f" % loss.item())
print("PASS")
