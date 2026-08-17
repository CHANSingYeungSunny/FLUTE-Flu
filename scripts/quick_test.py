"""
quick_test.py — Verify MIFlu pipeline in ~2 minutes on A100.
Run: python quick_test.py
Should show train_loss dropping and y_pred NOT near-zero.
"""
import torch, numpy as np, pandas as pd, sys
sys.path.insert(0, '.')
from miflu_model import MIFlu
from torch.utils.data import DataLoader, TensorDataset

VAR_COLS = ['% WEIGHTED ILI','% UNWEIGHTED ILI','AGE 0-4','AGE 5-24','ILITOTAL','NUM. OF PROVIDERS','OT']
T, L = 104, 24

# Load & normalize
df = pd.read_csv('../data/raw/national_illness_raw.csv')
data = df[VAR_COLS].values.astype(np.float32)
n = len(data)
t_end = int(n * 0.7)
mean = data[:t_end].mean(0, keepdims=1)
std  = data[:t_end].std(0, keepdims=1) + 1e-8
data_norm = (data - mean) / std

# Build windows
nw = len(data_norm) - T - L + 1
X = np.zeros((nw, 7, T), dtype=np.float32)
Y = np.zeros((nw, 7, L), dtype=np.float32)
for i in range(nw):
    X[i] = data_norm[i:i+T].T
    Y[i] = data_norm[i+T:i+T+L].T
split = np.array([0 if (i+T)<t_end else 2 for i in range(nw)])
Xt, Yt = X[split==0], Y[split==0]
Xte, Yte = X[split==2], Y[split==2]
print(f'Train: {len(Xt)} windows, Test: {len(Xte)} windows')
print(f'Test targets: mean={Yte.mean():.4f} std={Yte.std():.4f}')

# Model
device = 'cuda'
model = MIFlu(N=7, T=104, L=24, K=6, device=device)
opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=0.0005)
crit = torch.nn.MSELoss()
tl = DataLoader(TensorDataset(torch.from_numpy(Xt), torch.from_numpy(Yt)), batch_size=16, shuffle=True)

# Train 5 epochs
print('\nTraining 5 epochs...')
for ep in range(5):
    model.train()
    loss_sum = 0
    for bx, by in tl:
        bx, by = bx.to(device), by.to(device)
        opt.zero_grad()
        yh, _, _ = model(bx, htext=None)
        L = crit(yh, by); L.backward(); opt.step()
        loss_sum += L.item()
    model.eval()
    with torch.no_grad():
        yh_test, _, _ = model(torch.from_numpy(Xte[:50]).to(device), htext=None)
        yh_test = yh_test.cpu().numpy()
        test_mse = np.mean((yh_test - Yte[:50])**2)
    print(f'  Epoch {ep+1}: train_loss={loss_sum/len(tl):.4f}, test_mse(50samples)={test_mse:.4f}')
    print(f'    y_pred: mean={yh_test.mean():.4f} std={yh_test.std():.4f}')
    print(f'    y_true: mean={Yte[:50].mean():.4f} std={Yte[:50].std():.4f}')

# Final check
yh_final, _, _ = model(torch.from_numpy(Xte[:50]).to(device), htext=None)
yh_final = yh_final.detach().cpu().numpy()
pred_mean, true_mean = yh_final.mean(), Yte[:50].mean()
print(f'\n=== VERDICT ===')
print(f'y_pred mean={pred_mean:.4f} vs y_true mean={true_mean:.4f}')
if abs(pred_mean - true_mean) < 0.5:
    print('[PASS] Model predictions are in correct range. Ready for full training.')
else:
    print('[FAIL] Predictions still near-zero. Do NOT run full training.')
torch.cuda.empty_cache()
