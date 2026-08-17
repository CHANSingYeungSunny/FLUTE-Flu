"""
diagnose_miflu.py — 4-Step Deep Diagnostic for MIFlu Text Fusion
=================================================================
Run on A100: python diagnose_miflu.py
Covers: Step 1 (baseline check), Step 2 (prompt), Step 3 (LoRA grad), Step 4 (attention)
"""
import torch, numpy as np, pandas as pd, sys
sys.path.insert(0, '.')
from miflu_model import MIFlu
from textual_embedder import TextualInputEmbedder, build_prompt, PROMPT_TEMPLATE
from torch.utils.data import DataLoader, TensorDataset

VAR_COLS = ['% WEIGHTED ILI','% UNWEIGHTED ILI','AGE 0-4','AGE 5-24','ILITOTAL','NUM. OF PROVIDERS','OT']
T, L = 104, 24
dev = 'cuda'

print('='*65)
print('  MIFlu 4-STEP DIAGNOSTIC')
print('='*65)

# Load data
df = pd.read_csv('../data/raw/national_illness_raw.csv')
data = df[VAR_COLS].values.astype(np.float32)
n = len(data); t_end = int(n*0.7); v_end = t_end + int(n*0.1)
mean = data[:t_end].mean(0, keepdims=1)
std  = data[:t_end].std(0, keepdims=1) + 1e-8
data_norm = (data - mean) / std

# Build windows
nw = n - T - L + 1
X = np.zeros((nw,7,T), dtype=np.float32); Y = np.zeros((nw,7,L), dtype=np.float32)
splits = np.zeros(nw, dtype=np.int8)
for i in range(nw):
    X[i] = data_norm[i:i+T].T; Y[i] = data_norm[i+T:i+T+L].T
    splits[i] = 0 if (i+T)<t_end else (1 if (i+T)<v_end else 2)
Xt, Yt = X[splits==0], Y[splits==0]

print(f'\nData: {n} weeks, Train windows: {len(Xt)}')

# ═══════════════════════════════════════════════════════════
# STEP 1: Unimodal Baseline Check + LoRA Gradients
# ═══════════════════════════════════════════════════════════
print('\n' + '='*50)
print('STEP 1: Unimodal Baseline + LoRA Gradient Check')
print('='*50)

model = MIFlu(N=7, T=104, L=24, K=6, device=dev)
opt = torch.optim.Adam([p for p in model.parameters() if p.requires_grad], lr=0.0005)
crit = torch.nn.MSELoss()
tl = DataLoader(TensorDataset(torch.from_numpy(Xt), torch.from_numpy(Yt)), batch_size=16, shuffle=True)

# Train 2 epochs, capture gradients
model.train()
for ep in range(2):
    for i, (bx, by) in enumerate(tl):
        bx, by = bx.to(dev), by.to(dev)
        opt.zero_grad()
        yh, _, _ = model(bx, htext=None)
        L = crit(yh, by); L.backward()
        if ep == 0 and i == 0:
            # After first batch: check LoRA gradients
            for j, lm in enumerate(model.forecasting_llm.lora_modules):
                ga = lm.lora_A.grad.norm().item()
                gb = lm.lora_B.grad.norm().item()
                print(f'  Layer {j} LoRA grad: |A|={ga:.6f}, |B|={gb:.6f} {"OK" if gb > 0 else "DEAD"}')
        opt.step()

with torch.no_grad():
    yh, _, _ = model(torch.from_numpy(Xt[:50]).to(dev), htext=None)
print(f'  After 2 epochs: y_pred mean={yh.mean():.4f} std={yh.std():.4f}')
print(f'  Train target:    mean={Yt[:50].mean():.4f} std={Yt[:50].std():.4f}')
print(f'  Scale OK: {abs(yh.std() - Yt[:50].std()) < 0.5}')

# ═══════════════════════════════════════════════════════════
# STEP 2: Prompt Semantic Check
# ═══════════════════════════════════════════════════════════
print('\n' + '='*50)
print('STEP 2: Prompt Semantic Completeness')
print('='*50)

prompt = build_prompt(df.iloc[:t_end], T=104, L=24)
checks = [
    ('This variable peaks 1 time for 1 year' in prompt, 'Peak pattern present'),
    ('The overall trend is upward' in prompt, 'Trend description present'),
    ('Predict the next 24 steps' in prompt, 'Task instruction with L=24'),
    ('[Dataset information]' in prompt, 'Section header 1'),
    ('[Input variable description]' in prompt, 'Section header 2'),
    ('[Task instruction]' in prompt, 'Section header 3'),
    ('***' in prompt, 'Section separators'),
]
for ok, name in checks:
    print(f'  [{"PASS" if ok else "FAIL"}] {name}')
print(f'\n  Prompt excerpt (first 300 chars):')
print(f'  {prompt[:300]}...')
print(f'  Total prompt length: {len(prompt)} chars')

# ═══════════════════════════════════════════════════════════
# STEP 3: LoRA + Text Fusion Gradient Check
# ═══════════════════════════════════════════════════════════
print('\n' + '='*50)
print('STEP 3: MIFlu (text) LoRA Gradient Check')
print('='*50)

# Load text embedder and build prompt_cache
text_embedder = TextualInputEmbedder(device=dev)
prompt_cache = text_embedder(prompt)  # (1, tokens, 768)
print(f'  Text embedding shape: {tuple(prompt_cache.shape)}')
print(f'  Text embedding mean: {prompt_cache.mean():.6f}, std: {prompt_cache.std():.6f}')

# New model for MIFlu
model_mf = MIFlu(N=7, T=104, L=24, K=6, device=dev)
opt_mf = torch.optim.Adam([p for p in model_mf.parameters() if p.requires_grad], lr=0.0005)

# Single forward+backward with text
bx = torch.from_numpy(Xt[:4]).to(dev)
by = torch.from_numpy(Yt[:4]).to(dev)
ht = prompt_cache.expand(4, -1, -1)

opt_mf.zero_grad()
yh_mf, _, _ = model_mf(bx, htext=ht)
L_mf = crit(yh_mf, by)
L_mf.backward()

# Check LoRA gradients with text
print(f'  MIFlu loss (with text): {L_mf.item():.6f}')
for j, lm in enumerate(model_mf.forecasting_llm.lora_modules):
    ga = lm.lora_A.grad.norm().item()
    gb = lm.lora_B.grad.norm().item()
    print(f'  Layer {j} LoRA grad: |A|={ga:.6f}, |B|={gb:.6f} {"OK" if gb > 0 else "DEAD"}')

# Compare: MIFlu vs Baseline output on same input
with torch.no_grad():
    yh_bl, _, _ = model(torch.from_numpy(Xt[:4]).to(dev), htext=None)
    yh_mf2, _, _ = model_mf(torch.from_numpy(Xt[:4]).to(dev), htext=ht)
    diff = (yh_bl - yh_mf2).abs().mean().item()
print(f'\n  |MIFlu - Baseline| difference: {diff:.6f}')
print(f'  Text DOES change output: {diff > 0.01}')

# ═══════════════════════════════════════════════════════════
# STEP 4: Cross-Modal Attention Check
# ═══════════════════════════════════════════════════════════
print('\n' + '='*50)
print('STEP 4: Cross-Modal Attention Map')
print('='*50)

# Extract attention from first layer
fllm = model_mf.forecasting_llm
with torch.no_grad():
    htime, means, stdevs = model_mf.time_embedder(bx)
    hfuse = torch.cat([ht, htime], dim=1)  # text first, then time
    positions = torch.arange(hfuse.shape[1], device=dev).unsqueeze(0)
    hfuse = hfuse + fllm.wpe(positions)
    hidden = fllm.blocks[0].ln_1(hfuse)

    # Compute attention manually for first layer
    attn = fllm.blocks[0].attn
    qkv = attn.c_attn(hidden)
    embed_dim = attn.embed_dim
    num_heads = attn.num_heads
    head_dim = embed_dim // num_heads
    q, k, v = qkv.split(embed_dim, dim=2)
    q = q.view(4, -1, num_heads, head_dim).permute(0, 2, 1, 3)
    k = k.view(4, -1, num_heads, head_dim).permute(0, 2, 1, 3)

    seq_len = q.shape[2]
    attn_weights = (q @ k.transpose(-2, -1)) / np.sqrt(head_dim)
    # Average over batch and heads
    avg_attn = attn_weights.mean(dim=0).mean(dim=0)  # (seq, seq)

    text_len = ht.shape[1]  # 367
    time_len = htime.shape[1]  # 294

    # Attention from TIME tokens to TEXT tokens
    time_to_text = avg_attn[text_len:, :text_len].mean().item()
    time_to_time = avg_attn[text_len:, text_len:].mean().item()
    text_to_text = avg_attn[:text_len, :text_len].mean().item()

    print(f'  Avg attention (pre-softmax):')
    print(f'    TIME -> TEXT:  {time_to_text:.4f}')
    print(f'    TIME -> TIME:  {time_to_time:.4f}')
    print(f'    TEXT -> TEXT:  {text_to_text:.4f}')
    print(f'    Ratio (time->text / time->time): {time_to_text/time_to_time:.4f}')
    print(f'    Time tokens CAN see text: {time_to_text != 0}')
    print(f'    Time tokens attend MORE to text than time: {time_to_text > time_to_time}')

print('\n' + '='*65)
print('  DIAGNOSTIC COMPLETE')
print('='*65)
torch.cuda.empty_cache()
