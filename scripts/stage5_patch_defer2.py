# -*- coding: utf-8 -*-
"""Stage 5 — DEFER_TEST gates for the NLinear and no-text runners."""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------- NLinear ----------------
P = os.path.join(ROOT, "scripts", "train_nlinear_966.py")
s = io.open(P, encoding="utf-8").read()
OLD = "    t_mse_all, t_mae_all, t_mse_ili, t_mae_ili = eval_mse(model, el, device)"
NEW = '''    if os.environ.get("DEFER_TEST") == "1":
        print("  [nlinear] DEFER_TEST=1 - Test NOT evaluated (validation-only fit)")
        return {"L": L, "seed": seed, "mse_all": None, "mae_all": None,
                "mse_ili": None, "mae_ili": None, "best_val": best_val,
                "best_epoch": best_epoch, "n_train": int(len(Xt)),
                "n_val": int(len(Xv)), "n_test": int(len(Xte)),
                "model": model, "data_dict": data_dict, "test_deferred": True}
''' + OLD
assert OLD in s
if "DEFER_TEST" not in s:
    s = s.replace(OLD, NEW, 1)
    io.open(P, "w", encoding="utf-8").write(s)
    print("nlinear gate inserted")

# ---------------- ablation (no-text) ----------------
P2 = os.path.join(ROOT, "scripts", "train_ablation.py")
s2 = io.open(P2, encoding="utf-8").read()
ANCHOR = "     t_mse_ili_phys, t_mae_ili_phys) = evaluate("
GATE = '''    if os.environ.get("DEFER_TEST") == "1":
        log("  [ablation] DEFER_TEST=1 - Test NOT evaluated (validation-only fit)")
        os.makedirs(CKPT_DIR, exist_ok=True)
        rep_ckpt = os.path.join(CKPT_DIR, "_rep_ablation_L%s_seed%s.pth" % (L, seed))
        torch.save(model.state_dict(), rep_ckpt)
        return {"L": L, "test_mse_all": None, "test_mae_all": None,
                "test_mse_ili": None, "test_mae_ili": None,
                "test_mse_ili_phys": None, "test_mae_ili_phys": None,
                "rep_ckpt": rep_ckpt, "best_val": best_val, "seed": seed,
                "discarded": False, "test_deferred": True}

'''
assert ANCHOR in s2, "ablation test-eval anchor not found"
if "DEFER_TEST" not in s2:
    s2 = s2.replace(ANCHOR, GATE + ANCHOR, 1)
    io.open(P2, "w", encoding="utf-8").write(s2)
    print("ablation gate inserted")
