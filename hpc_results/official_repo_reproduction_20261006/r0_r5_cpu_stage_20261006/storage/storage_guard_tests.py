#!/usr/bin/env python3
"""
storage_guard_tests.py — S4: synthetic CPU-only guard tests.

Every artefact used here is SYNTHETIC and tiny. The tests exercise the guard's
decision logic and its atomic-write behaviour; they do not simulate experimental
results and they write nothing to the HPC.

Run:  python storage_guard_tests.py
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import storage_guard as SG


def main():
    res = []

    def check(name, cond, detail=""):
        res.append((name, bool(cond), detail))
        print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))

    tmp = tempfile.mkdtemp(prefix="sg_tests_")
    try:
        print("=" * 74)
        print("STORAGE GUARD TESTS  (SYNTHETIC artefacts, CPU only, nothing on HPC)")
        print("=" * 74)

        # ── A. projection arithmetic ────────────────────────────────────────
        print("\nA. projections use MEASURED sizes, not assumptions")

        pil = SG.project_output_bytes(4, [24, 36, 48, 60], trainer="locked")
        full = SG.project_output_bytes(4, [24, 36, 48, 60], trainer="full")
        check("A1 locked-checkpoint pilot projection is small",
              pil["projected_total_mib"] < 100,
              f"{pil['projected_total_mib']} MiB")
        check("A2 full-state_dict projection is ~85x larger (the F1 surprise)",
              full["projected_total_bytes"] / pil["projected_total_bytes"] > 50,
              f"ratio {full['projected_total_bytes']/pil['projected_total_bytes']:.0f}x")
        check("A3 measured checkpoint size is the real one (329 MB full)",
              SG.measure_checkpoint_bytes("full") == 328_585_240,
              f"{SG.measure_checkpoint_bytes('full'):,} bytes")

        ten = SG.project_output_bytes(40, [24, 36, 48, 60], trainer="locked")
        ten_full = SG.project_output_bytes(40, [24, 36, 48, 60], trainer="full")
        check("A4 10-repetition projection (locked) fits comfortably in home",
              ten["projected_total_mib"] < 2000, f"{ten['projected_total_mib']} MiB")
        check("A5 10-repetition projection (full) is the one to worry about",
              ten_full["projected_total_gib"] > 10, f"{ten_full['projected_total_gib']} GiB")

        repl = SG.project_output_bytes(40, [24, 36, 48, 60], trainer="locked")
        check("A6 historical-replacement projection (40 fits, locked)",
              repl["n_fits"] == 40, f"{repl['projected_total_mib']} MiB")

        # ── B. preflight refusals ──────────────────────────────────────────
        print("\nB. preflight refuses unsafe targets")

        home = os.path.join(tmp, "home_like")
        os.makedirs(home, exist_ok=True)
        r = SG.preflight("/gpfs1/scratch/sychan552/CHATTIME/Chattime/x", pil,
                         scratch_declared_healthy=False)
        check("B1 refuses a scratch target when scratch is not declared healthy",
              r["verdict"] == "STORAGE_PREFLIGHT_REFUSED" and r["on_scratch"],
              r["reasons"][0] if r["reasons"] else "")

        r2 = SG.preflight("/gpfs1/scratch/sychan552/x", pil, scratch_declared_healthy=True)
        check("B2a the scratch-block reason disappears once explicitly declared healthy",
              not any("declared healthy" in x for x in r2["reasons"]),
              "the scratch guard is bypassed only by explicit declaration")
        # an unmeasurable filesystem must be refused rather than assumed safe.
        # Force that branch directly, since a Windows dev box always has an
        # existing ancestor (C:\) and would otherwise never reach it.
        real_fs = SG.fs_stats
        SG.fs_stats = lambda _p: {"path": _p, "resolved": None, "free_bytes": None,
                                  "total_bytes": None, "free_gib": None, "known": False}
        try:
            r3 = SG.preflight(home, pil)
        finally:
            SG.fs_stats = real_fs
        check("B2b an unmeasurable target is refused (free space UNKNOWN)",
              r3["verdict"] == "STORAGE_PREFLIGHT_REFUSED" and not r3["free_known"],
              r3["reasons"][0] if r3["reasons"] else "not refused")

        r = SG.preflight(home, pil)
        check("B3 allows a normal target with ample space", r["ok"],
              f"free {r['free_bytes']/2**30:.1f} GiB")
        check("B4 required headroom is max(1 GiB, 10x projected)",
              r["required_bytes"] == max(1 << 30, 10 * pil["projected_total_bytes"]),
              f"{r['required_bytes']:,} bytes")

        # simulate a nearly-full filesystem by demanding an impossible projection
        huge = {"projected_total_bytes": 1 << 60}
        r = SG.preflight(home, huge)
        check("B5 refuses when free space is below the required headroom",
              r["verdict"] == "STORAGE_PREFLIGHT_REFUSED",
              r["reasons"][0] if r["reasons"] else "")

        # ── C. atomic writes ───────────────────────────────────────────────
        print("\nC. atomic saves leave no partial artefacts")

        p = os.path.join(tmp, "pred_test.npz")
        n = SG.atomic_save_npz(p, pred=np.zeros((2, 7, 24), np.float32),
                               target=np.zeros((2, 7, 24), np.float32))
        check("C1 NPZ written and readable", os.path.exists(p) and n > 0, f"{n} bytes")
        with np.load(p) as z:
            check("C2 reloaded arrays match", z["pred"].shape == (2, 7, 24),
                  str(z["pred"].shape))

        ck = os.path.join(tmp, "ckpt.pth")
        nb = SG.atomic_save_torch(ck, {"w": torch.zeros(8)})
        check("C3 torch checkpoint written", os.path.exists(ck) and nb > 0, f"{nb} bytes")
        check("C4 no .part residue after a successful save",
              not [f for f in os.listdir(tmp) if f.endswith(".part")],
              str(os.listdir(tmp)))

        # an overwrite must not corrupt the existing file on failure
        before = open(p, "rb").read()
        real_replace = os.replace
        try:
            def boom(a, b):
                raise OSError("simulated failure during replace")
            os.replace = boom
            try:
                SG.atomic_save_npz(p, pred=np.ones((1, 1, 1), np.float32))
                check("C5 simulated failure raises", False, "no exception")
            except OSError:
                check("C5 simulated failure raises", True, "")
        finally:
            os.replace = real_replace
        check("C6 the original file is intact after a failed overwrite",
              open(p, "rb").read() == before, "byte-identical")
        check("C7 no .part residue after a failed save",
              not [f for f in os.listdir(tmp) if f.endswith(".part")],
              str(os.listdir(tmp)))

        # ── D. postflight ──────────────────────────────────────────────────
        print("\nD. postflight detects residue and counts artefacts")
        pf = SG.postflight(tmp)
        check("D1 postflight passes on a clean directory", pf["verdict"] == "STORAGE_POSTFLIGHT_PASS",
              f"{pf['n_files']} files, {pf['total_mib']} MiB")
        open(os.path.join(tmp, "leftover.part"), "wb").write(b"x")
        pf2 = SG.postflight(tmp)
        check("D2 postflight FAILS when a .part file is present",
              pf2["verdict"] == "STORAGE_POSTFLIGHT_FAIL"
              and pf2["partial_files_left_behind"] == ["leftover.part"],
              str(pf2["partial_files_left_behind"]))
        os.unlink(os.path.join(tmp, "leftover.part"))

        # ── E. retention policy is explicit ────────────────────────────────
        print("\nE. the retention policy names what is kept and what never is")
        keep = SG.RETENTION_POLICY["keep"]
        never = SG.RETENTION_POLICY["never_keep"]
        check("E1 keeps exactly one checkpoint per (model,L,rep)",
              any("best validation-selected checkpoint" in k for k in keep), "")
        check("E2 never keeps per-epoch checkpoints or optimizer state",
              any("per-epoch checkpoints" in n for n in never)
              and any("optimizer state" in n for n in never), "")
        check("E3 lifecycle states the peak is bounded during training",
              "at most 2 checkpoints" in SG.RETENTION_POLICY["lifecycle"]["during_training"],
              "")

        print("\n" + "=" * 74)
        npass = sum(1 for _, c, _ in res if c)
        print(f"RESULT: {npass}/{len(res)} checks passed")
        print("=" * 74)
        return 0 if npass == len(res) else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())