# -*- coding: utf-8 -*-
"""Stage 5 — add a DEFER_TEST isolation gate to train_miflu.py.

Test scoring must happen ONCE from the separate scoring entry, after every
scheduled checkpoint is selected and locked. While DEFER_TEST=1 the Test loader
is never evaluated and export_prediction_csv is skipped.
"""
import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "scripts", "train_miflu.py")
s = io.open(P, encoding="utf-8").read()

GATE = '''    # ---- Stage 5 test-isolation gate ----
    # Test scoring happens ONCE from the separate scoring entry, after every
    # scheduled checkpoint has been selected and locked. While DEFER_TEST=1 the
    # Test loader is never evaluated, so no Test number exists yet.
    if os.environ.get("DEFER_TEST") == "1":
        log("  L=%s rep seed=%s: DEFER_TEST=1 - Test NOT evaluated (validation-only fit)"
            % (L, seed))
        os.makedirs(CKPT_DIR, exist_ok=True)
        rep_ckpt = os.path.join(CKPT_DIR, "_rep_miflu_L%s_seed%s.pth" % (L, seed))
        torch.save(model.state_dict(), rep_ckpt)
        del model
        torch.cuda.empty_cache() if device == "cuda" else None
        return {"L": L, "test_mse_all": None, "test_mae_all": None,
                "test_mse_ili": None, "test_mae_ili": None, "test_pcc_ili": None,
                "test_mse_ili_phys": None, "test_mae_ili_phys": None,
                "test_gt_ili": None, "test_pr_ili": None,
                "rep_ckpt": rep_ckpt, "best_val": best_val, "seed": seed,
                "discarded": False, "test_deferred": True}

'''

ANCHOR = "    (t_mse_all, t_mae_all, t_mse_ili, t_mae_ili, t_pcc_ili, t_gt_ili, t_pr_ili,"
assert ANCHOR in s, "test-eval anchor not found"
if "DEFER_TEST" not in s:
    s = s.replace(ANCHOR, GATE + ANCHOR, 1)
    print("DEFER_TEST gate inserted before the Test evaluation")

# skip export_prediction_csv while deferred (it would write test-split rows)
OLD = "            pred_csv = export_prediction_csv("
if "DEFER_TEST" in s and "if os.environ.get(\"DEFER_TEST\") != \"1\":\n            pred_csv" not in s:
    s = s.replace(OLD, "            if os.environ.get(\"DEFER_TEST\") == \"1\":\n"
                       "                pred_csv = None\n"
                       "                log(\"  [DEFER_TEST] prediction export skipped (locked-batch step)\")\n"
                       "            else:\n"
                       "                pred_csv = export_prediction_csv(", 1)
    print("export gated")

io.open(P, "w", encoding="utf-8").write(s)
