"""
configs.py — Single Source of Truth for MIFlu
=============================================

WHY THIS MODULE EXISTS
----------------------
Before this refactor every training script re-declared its own `CONFIG = {}`
(5 copies) and scattered magic numbers (`104`, `24`, `2`, `768`, `0.70`, `0.10`)
through the model and training code. That is a reproducibility hazard for a
journal artefact: a reviewer cannot tell which knob is authoritative, and a
single edit in one copy silently desynchronises the others.

This module is now the ONLY place where hyper-parameters and data-window
constants are defined. Every training script imports from here.

NON-NEGOTIABLE CONSTANTS (enforced by assertion, not by convention)
--------------------------------------------------------------------
  FULL_ROWS  = 1025   the complete 2002-2021 CDC national window
  TRAIN_END  = 717    scaler is fit on data[:717] ONLY
  VAL_END    = 819    717 + 102 val + 206 test = 1025

`derive_split()` recomputes the split from `TRAIN_FRAC`/`VAL_FRAC` and ASSERTS
it lands on 717/819, so a truncated (966-row) CSV cannot silently produce a
different split — the run crashes instead. That is the "no truncation to 966"
guard.

BEHAVIOUR-PRESERVING
--------------------
Every value below is byte-identical to the literals that were previously
hard-coded in the five scripts. This refactor must NOT change any published
number; `no_text_ln = 1,028,520` and `gated_inject = 17,537,449` trainable
parameters are the regression gate that proves it.
"""

from __future__ import annotations

import os
import random

import numpy as np

# ──────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)

DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_PATH = os.path.join(DATA_DIR, "raw", "national_illness_raw.csv")
REGIONAL_DATA_PATH = os.path.join(DATA_DIR, "us_region_raw.csv")
SCALER_PATH = os.path.join(DATA_DIR, "scaler_miflu_national.json")
CKPT_DIR = os.path.join(PROJECT_ROOT, "checkpoints")

JOURNAL_EVIDENCE_ROOT = os.path.join(PROJECT_ROOT, "hpc_results", "journal_evidence")
FIGURES_DIR = os.path.join(JOURNAL_EVIDENCE_ROOT, "figures")
LOGS_DIR = os.path.join(JOURNAL_EVIDENCE_ROOT, "logs")

# ──────────────────────────────────────────────────────────────────────────
# Channel definitions (N=7, national)
# ──────────────────────────────────────────────────────────────────────────
VAR_COLS = [
    "% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4", "AGE 5-24",
    "ILITOTAL", "NUM. OF PROVIDERS", "OT",
]
ILI_CHANNEL = 4          # index of "ILITOTAL" inside VAR_COLS
ILI_COL = "ILITOTAL"
N_CHANNELS = len(VAR_COLS)   # 7
N_HEADS = 8              # attention heads of ModalityAligner's cross-attention

HHS_COLS = [f"HHS{i}" for i in range(1, 11)]   # regional, N=10

# ──────────────────────────────────────────────────────────────────────────
# NON-NEGOTIABLE: full 1025-row window
# ──────────────────────────────────────────────────────────────────────────
FULL_ROWS = 1025
TRAIN_FRAC = 0.70
VAL_FRAC = 0.10
TRAIN_END = 717
VAL_END = 819

# ──────────────────────────────────────────────────────────────────────────
# Immutable dataset profiles (Stage 4 adapter — additive, hash-pinned)
# ──────────────────────────────────────────────────────────────────────────
# The project 1025-row path is byte-for-byte unchanged. `author_966` is a
# SEPARATE profile so track A (author 966-row vintage) and track B (July 1025
# snapshot) can never be silently conflated. Each profile pins its own data
# hash, split rule, scaler path and prompt date-range; nothing is inferred
# from file contents alone. No profile deletes the 1025-row guard — the default
# profile still refuses a truncated CSV.
DATA_PROFILES = {
    "project_1025": {
        "data_path": RAW_DATA_PATH,
        "sha256": "c2b983af2bf38614adbb4c984fa6b63fb3f73f3b148c54dcc4ef5a14efa4c70d",
        "n_rows": 1025,
        "split_rule": "project_70_10_20",
        "train_end": 717,
        "val_end": 819,
        "date_range_string": "between 2002 and 2021",
        "scaler_path": SCALER_PATH,
    },
    "author_966": {
        "data_path": os.path.join(DATA_DIR, "raw",
                                  "national_illness_raw_paper_exact.csv"),
        "sha256": "31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a",
        "n_rows": 966,
        "split_rule": "author_676_97_193",
        "train_end": 676,
        "val_end": 773,
        "date_range_string": "between 2002 and 2020",
        "scaler_path": os.path.join(DATA_DIR, "scaler_miflu_author966.json"),
    },
}

# Priority subset for the journal submission (no prompt ablations).
CORE_VARIANTS = ("full", "no_lora", "no_text_ln", "gated_inject")


def resolve_profile(name: str) -> dict:
    """Return a copy of the immutable profile, or raise on an unknown name."""
    if name not in DATA_PROFILES:
        raise ValueError(f"unknown data profile {name!r}; "
                         f"known={sorted(DATA_PROFILES)}")
    return dict(DATA_PROFILES[name])


def split_for_profile(name: str, n_rows: int) -> tuple[int, int]:
    """Recompute (train_end, val_end) for a named profile and assert it matches.

    project_1025 keeps the historical 70/10/20 convention; author_966 uses the
    author's num_vali=remainder convention (676/97/193).
    """
    p = resolve_profile(name)
    n = int(n_rows)
    if n != p["n_rows"]:
        raise ValueError(f"profile {name!r} expects {p['n_rows']} rows, got {n}")
    if p["split_rule"] == "author_676_97_193":
        train_end = int(n * TRAIN_FRAC)      # 676
        test_n = int(n * 0.20)               # 193
        val_end = n - test_n                 # 773 (num_vali = remainder)
    else:
        train_end = int(n * TRAIN_FRAC)
        val_end = train_end + int(n * VAL_FRAC)
    if (train_end, val_end) != (p["train_end"], p["val_end"]):
        raise ValueError(f"profile {name!r} split drift: got "
                         f"({train_end},{val_end}) expected "
                         f"({p['train_end']},{p['val_end']})")
    return train_end, val_end


def verify_profile_hash(name: str) -> str:
    """Verify the profile's data file hash; return it on success."""
    import hashlib
    p = resolve_profile(name)
    h = hashlib.sha256(open(p["data_path"], "rb").read()).hexdigest()
    if h != p["sha256"]:
        raise ValueError(f"profile {name!r} hash mismatch: expected "
                         f"{p['sha256']} got {h}")
    return h


def assert_full_window(n_rows: int) -> int:
    """Crash loudly if the CSV is not the complete 2002-2021 window.

    The 966-row variant (COVID tail trimmed) would silently shrink the test
    split and remove the very distribution shift the paper studies.
    """
    n_rows = int(n_rows)
    if n_rows != FULL_ROWS:
        raise ValueError(
            f"expected the FULL {FULL_ROWS}-row window (2002-2021) but got "
            f"{n_rows} rows. Refusing to run on a truncated dataset.")
    return n_rows


def derive_split(n_rows: int) -> tuple[int, int]:
    """Recompute (train_end, val_end) and ASSERT they match 717 / 819.

    Reproduces the historical convention exactly:
        train_end = int(n * 0.70)
        val_end   = train_end + int(n * 0.10)
    """
    n_rows = int(n_rows)
    train_end = int(n_rows * TRAIN_FRAC)
    val_end = train_end + int(n_rows * VAL_FRAC)
    if (train_end, val_end) != (TRAIN_END, VAL_END):
        raise ValueError(
            f"split drift: got train_end={train_end}, val_end={val_end} but the "
            f"published split is {TRAIN_END}/{VAL_END} (n={n_rows}).")
    return train_end, val_end


# ──────────────────────────────────────────────────────────────────────────
# Hyper-parameters (MIFlu paper Table IV)
# ──────────────────────────────────────────────────────────────────────────
# National / ablation config — shared by train_ablation.py, train_miflu.py,
# train_baseline.py (previously duplicated verbatim in all three).
NATIONAL_CONFIG: dict = {
    "T": 104,                      # look-back window (weeks)
    "L_list": [24, 36, 48, 60],    # forecast horizons, trained INDEPENDENTLY
    "N": 7,                        # channels
    "Lp": 24,                      # patch length
    "S": 2,                        # stride
    "K": 6,                        # GPT2 layers
    "lora_r": 4,                   # LoRA rank
    "lora_alpha": 4.0,             # LoRA scaling
    "D": 768,                      # GPT2-small hidden size
    "attn_heads": 8,               # ModalityAligner cross-attention heads
    "batch_size": 16,
    "learning_rate": 0.0005,
    "epochs": 20,
    "num_repetitions": 10,
    "seed": 42,
}

# Regional config — shared by train_regional_miflu.py and
# train_regional_baseline.py (previously duplicated verbatim in both).
REGIONAL_CONFIG: dict = {
    "T": 20,
    "L_list": [2, 3, 5, 10, 13, 15, 20],
    "N": 10,
    "Lp": 4,
    "S": 2,
    "K": 4,
    "lora_r": 4,
    "lora_alpha": 4.0,
    "D": 768,
    "attn_heads": 8,
    "batch_size": 32,
    "learning_rate": 0.0005,
    "epochs": 50,
    "num_repetitions": 10,
    "seed": 42,
}

# Default alias: the national setting is the paper's main configuration.
CONFIG = NATIONAL_CONFIG


# ──────────────────────────────────────────────────────────────────────────
# Deterministic execution
# ──────────────────────────────────────────────────────────────────────────
def set_seed(seed: int) -> None:
    """Seed every RNG that can affect a training run.

    Covers `random`, `numpy`, `torch`, `torch.cuda` and cuDNN. Previously only
    `torch.manual_seed(seed + L)` was called, leaving numpy / cuDNN
    non-deterministic — a reproducibility hole for a journal artefact.

    Trade-off: `cudnn.deterministic = True` disables non-deterministic
    convolution algorithms and typically costs 10-20% throughput. That is the
    price of bit-reproducible results and is deliberate.
    """
    seed = int(seed)
    random.seed(seed)
    np.random.seed(seed)

    import torch  # local import: keeps configs.py importable without torch
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ──────────────────────────────────────────────────────────────────────────
# Artifact layout helpers (PHASE 4 strict tree)
# ──────────────────────────────────────────────────────────────────────────
def reps_root(variant: str, root: str = JOURNAL_EVIDENCE_ROOT) -> str:
    """.../journal_evidence/{variant}/reps_1_to_10"""
    return os.path.join(root, variant, "reps_1_to_10")


def rep_dir(variant: str, rep: int, root: str = JOURNAL_EVIDENCE_ROOT) -> str:
    """.../journal_evidence/{variant}/reps_1_to_10/rep_{NN}"""
    return os.path.join(reps_root(variant, root), f"rep_{rep:02d}")


def ckpt_dir(variant: str, rep: int, root: str = JOURNAL_EVIDENCE_ROOT) -> str:
    """.../rep_{NN}/checkpoints"""
    return os.path.join(rep_dir(variant, rep, root), "checkpoints")


def best_model_path(variant: str, rep: int,
                    root: str = JOURNAL_EVIDENCE_ROOT) -> str:
    """.../rep_{NN}/checkpoints/best_model.pt"""
    return os.path.join(ckpt_dir(variant, rep, root), "best_model.pt")


def _self_check() -> None:
    """Guards the invariants this module claims to enforce."""
    # 1025 rows -> 717 / 819, and nothing else.
    assert derive_split(FULL_ROWS) == (TRAIN_END, VAL_END)
    assert TRAIN_END + (VAL_END - TRAIN_END) + (FULL_ROWS - VAL_END) == FULL_ROWS
    # Channel bookkeeping used by the dual-track metrics.
    assert VAR_COLS[ILI_CHANNEL] == ILI_COL
    assert N_CHANNELS == len(VAR_COLS) == 7
    # The two configs must not have been silently merged.
    assert NATIONAL_CONFIG["T"] == 104 and REGIONAL_CONFIG["T"] == 20
    assert CONFIG is NATIONAL_CONFIG
    # Dataset profiles: distinct, hash-pinned, split-correct.
    assert split_for_profile("project_1025", 1025) == (717, 819)
    assert split_for_profile("author_966", 966) == (676, 773)
    assert resolve_profile("project_1025")["data_path"] != \
        resolve_profile("author_966")["data_path"]
    assert resolve_profile("project_1025")["scaler_path"] != \
        resolve_profile("author_966")["scaler_path"]
    print("[configs] self-check OK")
    print(f"  window: FULL_ROWS={FULL_ROWS} train_end={TRAIN_END} "
          f"val_end={VAL_END}")
    print(f"  national: T={NATIONAL_CONFIG['T']} N={NATIONAL_CONFIG['N']} "
          f"Lp={NATIONAL_CONFIG['Lp']} S={NATIONAL_CONFIG['S']} "
          f"K={NATIONAL_CONFIG['K']} D={NATIONAL_CONFIG['D']}")
    print(f"  core variants: {', '.join(CORE_VARIANTS)}")


if __name__ == "__main__":
    _self_check()
