import torch, miflu_model as m

for kw, label in [(dict(use_text_ln=False), "no_text_ln"),
                 (dict(gated_inject=True, unfreeze_first_k=2), "gated_inject")]:
    net = m.MIFlu(N=7, T=104, L=24, Lp=24, S=2, K=6, lora_r=4,
                  device="cpu", **kw)
    x = torch.randn(2, 7, 104)
    tx = torch.randn(2, 367, 768)
    y, _ = net(x, tx)[:2]
    tp = sum(p.numel() for p in net.parameters() if p.requires_grad)
    print("OK", label, "yshape", tuple(y.shape), "trainable", tp)
print("SMOKE PASS")
