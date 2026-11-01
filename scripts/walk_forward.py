#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""walk_forward.py — rolling-origin (expanding-window) splitter for the A-track.

WHY THIS FILE EXISTS
--------------------
Every number this project has produced so far comes from **one fixed split**:
`train_miflu.build_windows` / `train_nlinear_966.build_windows` take a single
`(train_end, val_end)` pair, and for the author 966-row profile that pair is
`(676, 773)` (`num_train = int(966*0.7)`, `num_test = int(966*0.2)`). A single
split means a single test period, so "the model generalises" is asserted from one
193-row block of the epidemic record. `SKILL.md` §11 blocker 4 and
`docs/WORK_BREAKDOWN.md` §13.D both list **rolling origin (5 folds)** as *missing
code*, not as missing compute: there was no K-fold origin abstraction to train
against, so no GPU could have produced it either.

This module supplies exactly that abstraction and nothing else. It does **not**
train anything, does **not** touch `hpc_experiments/queue/*`, and is additive:
importing it changes no existing behaviour.

WHAT A FOLD IS
--------------
A `Fold` is an **expanding prefix** of the same series plus one designated test
block::

    rows 0 .................................................. test_end
    |<---------- train ------------->|<-- val -->|<-- test -->|
    0                          train_end      val_end     test_end

* **expanding window** — every fold reads only rows `[0, test_end)`; folds
  differ in how far the prefix reaches, so fold *i*'s training set is a superset
  of fold *i-1*'s. That is the rolling-origin (walk-forward) protocol.
* **70/10/20 *within the fold window*** — `test = int(0.20*n)`,
  `val = int(0.10*n)`, train = the rest, i.e. exactly the author's own split rule
  (`configs.split_for_profile`, `author_676_97_193`). A fold therefore has the
  *same shape* as the national split; only the origin moves.
* **`containment="strict"`** — every window's whole target block must lie inside
  one split (the Stage-5 rule). Window counts follow from the borders alone and
  `Fold.window_counts()` reproduces them exactly:
  train `= train_end - T - L + 1`, val `= val_end - train_end - L + 1`,
  test `= test_end - val_end - L + 1`.

WHY THE ORIGINS ARE GEOMETRIC (growth >= 1.25), NOT EQUALLY SPACED
-----------------------------------------------------------------
Three requirements collide on a 966-row series with `K=5` folds: (a) 70/10/20
*within each fold window*, (b) **test blocks disjoint**, (c) folds strictly
ordered in time. Under (a) fold *i*'s test block is `[0.8*n_i, n_i)`, so
disjointness requires

    0.8 * n_{i+1} >= n_i      i.e.      n_{i+1} >= 1.25 * n_i

so the origins must grow by at least 25 % per fold, and the splitter is built
**backwards** from the last row with exactly that ratio::

    test_end_K = n_rows
    test_end_i = min(test_end_{i+1} // 1.25, val_end_{i+1} - 1)

The `val_end_{i+1} - 1` term guarantees a >=1-row gap even after integer
truncation, so disjointness is a property of the construction, not of luck.
`assert_folds` re-checks it anyway, because a property that is only "true by
construction" is one refactor away from being false. Equal spacing does **not**
work here: origins 394/537/680/823/966 overlap at the third fold
(`0.8*680 = 544 < 537`... and `0.8*823 = 658 < 680` outright).

THE VALIDATION FLOOR — the one place the 70/10/20 shape must yield
-----------------------------------------------------------------
`K=5` forces the first origin to `966 / 1.25^4 = 396` rows, so fold 1's
validation block is `int(0.1*396) = 39` rows. But the validation loader drops its
last partial batch (`drop_last=True`, batch 16 in `train_miflu.train_L`), so a 39-row
validation block yields `39 - L + 1` validation windows — **16 at L=24, but only 4
at L=36, -8 at L=48 and -20 at L=60**. A fold with zero validation windows cannot
select a checkpoint, so a strictly-10 % validation block is *arithmetically
impossible* for the longer horizons, no matter how the code is written.

The fix is explicit and asserted rather than silent: `val_floor_rows` widens the
validation block backwards into the training prefix (never forwards — `val_end`
and `test_end` are untouched, so the **test blocks still obey 20 % exactly and
remain disjoint**). The floor is sized to what the training loop actually needs:

    val_floor_rows = L_max + min_val_windows - 1      # 16 windows at L_max

With `L_max = 60`, `min_val_windows = 16` the floor is 75 rows: fold 1 keeps its
78-row test block, its 75-row validation block (19 % of its window instead of
10 %) and drops to 241 training rows (61 % instead of 70 %). `Fold.val_floor_applied`
records this per fold, `Fold.as_dict()` carries it into every manifest, and
`assert_folds` verifies the floor binds **only** when needed. Fold 5 — the one
that ends at the last row — is unaffected at any horizon because 10 % of 966 is
already 97 rows.

So the published statement is: *test blocks are 20 % of the fold window and
disjoint; validation is 10 % of the fold window, widened only where 10 % cannot
yield 16 validation windows at the horizon actually trained.*

A USEFUL INVARIANT (asserted in `tests/test_walk_forward.py`)
------------------------------------------------------------
The **last** fold ends at the last row, so on the 966-row series fold `K` ends at
`test_end = 966`. With `val_floor_rows = 0` its borders are exactly
`(676, 773, 966)` — the existing single split. Rolling origin therefore *contains*
the protocol that produced every published number instead of replacing it.

HOW TO USE IT
-------------
Print / validate the fold table (no GPU, no data read)::

    python scripts/walk_forward.py --rows 966 --k 5

Consume a fold from a training script (the `--fold` hook both national runners
accept; `--fold 0`, the default, is the existing fixed split, unchanged)::

    python scripts/train_miflu.py --horizon 24 --reps 1 \
        --profile author_repo_966 --containment strict --fold 3 \
        --export-dir hpc_results/walk_forward/f3/L24_s2021

    python scripts/train_backbone_966.py --backbone nlinear --horizon 24 --seed 42 \
        --profile author_966 --containment strict --fold 3

Programmatic use::

    from walk_forward import make_folds, resolve_split
    folds = make_folds(966, k=5)                  # tuple[Fold, ...], validated
    train_end, val_end = folds[2].split()         # feed straight into build_windows
    rows = fold_data(data_norm, folds[2])         # rows[0:test_end] — nothing newer
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

#: Number of folds of the rolling-origin experiment (WORK_BREAKDOWN §13.D).
DEFAULT_K = 5

#: The author's split rule, reused verbatim so a fold has the *same shape* as the
#: national split: `train_end = int(0.70*n)`, `test = int(0.20*n)`, val = rest.
TRAIN_FRAC = 0.70
VAL_FRAC = 0.10
TEST_FRAC = 0.20

#: Minimum origin growth that keeps test blocks disjoint under a 70/10/20 shape:
#: `1 / (1 - TEST_FRAC) == 1.25`. Derived in the module docstring.
GROWTH = 1.25

#: The A-track look-back (`configs.NATIONAL_CONFIG["T"]`), duplicated here so the
#: module stays importable without `configs` (and therefore without torch).
LOOKBACK = 104

#: Horizons the A-track trains, used for the window-feasibility assertion.
HORIZONS = (24, 36, 48, 60)

#: Validation windows a fold must yield: the val loader is built with
#: `batch_size=16, drop_last=True`, so fewer than 16 windows means **zero**
#: validation batches and therefore no checkpoint selection at all.
MIN_VAL_WINDOWS = 16

#: Minimum windows on the other two splits. 1 for val-like sanity, but train/test
#: below a single batch would make the fit or the evaluation meaningless, so the
#: default is one full batch (16) for the test split and one for training.
MIN_TEST_WINDOWS = 16
MIN_TRAIN_WINDOWS = 16


class FoldError(ValueError):
    """Raised when a fold layout is impossible or the assertions fail."""


def val_floor_for(horizons: Sequence[int] = HORIZONS,
                  min_val_windows: int = MIN_VAL_WINDOWS) -> int:
    """Validation rows needed to yield `min_val_windows` windows at the longest
    horizon of the run (`n_val_windows = val_rows - L + 1`)."""
    return int(max(horizons)) + int(min_val_windows) - 1


@dataclass(frozen=True)
class Fold:
    """One rolling-origin fold: an expanding prefix plus its test block.

    Attributes
    ----------
    index : int
        1-based fold number (`f1` … `fK`); fold 1 is the earliest origin.
    train_end : int
        Exclusive end of the training rows (also the validation block's lower
        border under `containment="strict"`).
    val_end : int
        Exclusive end of the validation rows (the test block's lower border).
    test_end : int
        Exclusive end of the test rows **and** of the whole fold window: the fold
        may only read `rows[0:test_end]`. Must grow with `index`.
    n_rows : int, optional
        Total rows of the underlying series; asserted when given.
    val_floor_rows : int
        The minimum validation block this fold was built with (0 = pure 10 %).
        Recorded so the manifest can state whether the shape deviated.
    """

    index: int
    train_end: int
    val_end: int
    test_end: int
    n_rows: Optional[int] = None
    val_floor_rows: int = 0

    # ── construction guards ────────────────────────────────────────────────
    def __post_init__(self) -> None:
        for name in ("index", "train_end", "val_end", "test_end",
                     "val_floor_rows"):
            value = getattr(self, name)
            if not isinstance(value, int):
                raise FoldError(f"Fold.{name} must be int, got {type(value).__name__}")
            if value < 0:
                raise FoldError(f"Fold.{name} must be non-negative, got {value}")
        if self.index < 1:
            raise FoldError(f"fold index is 1-based, got {self.index}")
        if not (self.train_end < self.val_end < self.test_end):
            raise FoldError(
                "fold borders must be strictly increasing "
                f"(train_end={self.train_end}, val_end={self.val_end}, "
                f"test_end={self.test_end})")
        if self.n_rows is not None and self.test_end > self.n_rows:
            raise FoldError(
                f"fold {self.index} reads to row {self.test_end} but the series "
                f"has n_rows={self.n_rows}")
        # A floor larger than the realised validation block would mean the
        # constructor was called with mismatched arguments.
        if self.val_floor_rows > self.val_end - self.train_end:
            raise FoldError(
                f"fold {self.index}: val_floor_rows={self.val_floor_rows} > the "
                f"realised validation block ({self.val_end - self.train_end} rows)")

    # ── derived quantities ────────────────────────────────────────────────
    @property
    def n_train(self) -> int:
        """Training rows in this fold's window."""
        return self.train_end

    @property
    def n_val(self) -> int:
        """Validation rows in this fold's window."""
        return self.val_end - self.train_end

    @property
    def n_test(self) -> int:
        """Test rows in this fold's window (the block this fold is scored on)."""
        return self.test_end - self.val_end

    @property
    def label(self) -> str:
        """Short fold tag used in paths and artefact names (`f1` … `f5`)."""
        return f"f{self.index}"

    @property
    def val_floor_applied(self) -> bool:
        """True when the floor (not the 10 % remainder) set the validation block.

        Validation is the *remainder* under the author convention, so it can sit
        a row or two above exactly 10 % without any floor being involved; only a
        floor strictly larger than that remainder counts as a shape deviation.
        """
        rest = self.val_end - int(self.test_end * TRAIN_FRAC)
        return int(self.val_floor_rows) > rest

    def split(self) -> Tuple[int, int]:
        """`(train_end, val_end)` — exactly what `build_windows` expects.

        Under `containment="strict"` these two borders plus the series length
        determine every split, so a caller must slice the series to
        `rows[0:test_end]` first (`fold_data` does that).
        """
        return (self.train_end, self.val_end)

    def window_counts(self, lookback: int = LOOKBACK,
                      horizon: int = HORIZONS[0]) -> dict:
        """Number of train/val/test windows this fold yields, per the strict rule.

        Derived from the borders only (derivation in the module docstring):
        train `= train_end - T - L + 1`, val `= val_end - train_end - L + 1`,
        test `= test_end - val_end - L + 1`. Negative values mean the split is
        too short for that `(T, L)`; they are returned as-is so a caller can
        report *why* a fold is infeasible instead of getting a bare assert.
        """
        t, L = int(lookback), int(horizon)
        return {
            "n_train_windows": int(self.train_end - t - L + 1),
            "n_val_windows": int(self.val_end - self.train_end - L + 1),
            "n_test_windows": int(self.test_end - self.val_end - L + 1),
        }

    def fractions(self) -> dict:
        """Realised row proportions of the fold window (70/10/20 when no floor)."""
        n = float(self.test_end)
        return {"train": self.n_train / n, "val": self.n_val / n,
                "test": self.n_test / n}

    def as_dict(self) -> dict:
        """JSON-serialisable record (carried into every run manifest)."""
        return {"fold": self.index, "label": self.label,
                "train_end": self.train_end, "val_end": self.val_end,
                "test_end": self.test_end, "n_rows": self.n_rows,
                "n_train": self.n_train, "n_val": self.n_val,
                "n_test": self.n_test,
                "val_floor_rows": self.val_floor_rows,
                "val_floor_applied": bool(self.val_floor_applied),
                **{"frac_" + k: v for k, v in self.fractions().items()}}

    def describe(self, lookback: int = LOOKBACK,
                 horizons: Sequence[int] = HORIZONS) -> str:
        """One human-readable line per fold, with per-horizon window counts."""
        counts = "  ".join(
            "L%d:%d/%d/%d" % (
                L,
                self.window_counts(lookback, L)["n_train_windows"],
                self.window_counts(lookback, L)["n_val_windows"],
                self.window_counts(lookback, L)["n_test_windows"],
            ) for L in horizons)
        floor = "  [val floor]" if self.val_floor_applied else ""
        return ("%-3s rows[0:%3d)  train=%-4d val=%-3d test=%-3d  "
                "(%4.1f/%4.1f/%4.1f %%)%s  windows %s"
                % (self.label, self.test_end, self.n_train, self.n_val,
                   self.n_test, 100 * self.fractions()["train"],
                   100 * self.fractions()["val"], 100 * self.fractions()["test"],
                   floor, counts))


# ──────────────────────────────────────────────────────────────────────────
# construction
# ──────────────────────────────────────────────────────────────────────────
def _split_for(n_rows: int, val_floor_rows: int = 0,
               train_frac: float = TRAIN_FRAC,
               test_frac: float = TEST_FRAC) -> Tuple[int, int]:
    """`(train_end, val_end)` for a fold window of `n_rows` rows.

    With `val_floor_rows = 0` this is the author convention exactly: the test
    block is `int(n*0.20)`, the training block is `int(n*0.70)`, and validation
    is the **remainder** (`configs.split_for_profile`, `author_676_97_193`). For
    `n_rows = 966` it therefore returns `(676, 773)` — bit-identical to
    `configs.split_for_profile("author_966", 966)`.

    With a floor, only the training border moves back; `val_end` (and therefore
    the scored test block) is untouched.
    """
    n_rows = int(n_rows)
    test_n = int(n_rows * test_frac)
    val_end = n_rows - test_n
    val_rows = max(val_end - int(n_rows * train_frac), int(val_floor_rows))
    train_end = val_end - val_rows
    return train_end, val_end


def make_folds(n_rows: int, k: int = DEFAULT_K, growth: float = GROWTH,
               lookback: int = LOOKBACK,
               horizons: Sequence[int] = HORIZONS,
               val_floor_rows: Optional[int] = None,
               min_val_windows: int = MIN_VAL_WINDOWS,
               min_train_windows: int = MIN_TRAIN_WINDOWS,
               min_test_windows: int = MIN_TEST_WINDOWS,
               train_frac: float = TRAIN_FRAC,
               test_frac: float = TEST_FRAC) -> Tuple[Fold, ...]:
    """Build and validate `k` expanding-window folds over `n_rows` rows.

    Parameters
    ----------
    n_rows : int
        Rows of the series the folds are cut from (966 for the A-track).
    k : int
        Number of folds (5 for the §13.D experiment). Must be >= 2.
    growth : float
        Origin growth factor; must be `>= 1/(1-test_frac)` (1.25 by default),
        otherwise the test blocks cannot be disjoint under a 70/10/20 shape and
        `FoldError` is raised before anything is trained.
    lookback, horizons
        `T` and the horizons the feasibility check runs over.
    val_floor_rows
        Validation rows the earliest folds must keep (see the module docstring).
        `None` (the default) = `val_floor_for(horizons, min_val_windows)`, i.e.
        exactly what the validation loader needs; `0` = the pure 70/10/20 shape,
        which is **infeasible** for `K=5` at `L >= 36` on 966 rows (that error is
        itself tested). Only `train_end` moves when a floor binds.
    min_val_windows, min_train_windows, min_test_windows
        Per-split window floors for the feasibility assertion.
    train_frac, test_frac
        The split shape (author 0.70/0.20, val = remainder).

    Returns
    -------
    tuple of Fold
        `k` folds, index 1..k, earliest first, test blocks disjoint and strictly
        ordered in time.

    Raises
    ------
    FoldError
        If the request is geometrically impossible, with the arithmetic and the
        largest feasible `k` in the message.
    """
    n_rows, k = int(n_rows), int(k)
    if val_floor_rows is None:
        val_floor_rows = val_floor_for(horizons, min_val_windows)
    val_floor_rows = int(val_floor_rows)
    if k < 2:
        raise FoldError(f"rolling origin needs k >= 2 folds, got {k}")
    if n_rows <= 0:
        raise FoldError(f"n_rows must be positive, got {n_rows}")
    min_growth = 1.0 / (1.0 - float(test_frac))
    if float(growth) < min_growth - 1e-12:
        raise FoldError(
            "growth=%.4f cannot make the test blocks disjoint: with a %.0f%% test "
            "block the origin must grow by at least %.4f per fold"
            % (float(growth), 100 * float(test_frac), min_growth))

    # Build the origins BACKWARDS from the last row (see the module docstring).
    ends = [n_rows]
    for _ in range(k - 1):
        nxt = ends[-1]
        _, val_end_next = _split_for(nxt, val_floor_rows, train_frac, test_frac)
        cand = min(int(nxt / float(growth)), int(val_end_next) - 1)
        if cand <= 0:
            raise FoldError(
                f"cannot place {k} folds on {n_rows} rows with growth={growth}: "
                f"origin fell to {cand}. Largest feasible k on this series is "
                f"{max_feasible_k(n_rows, growth, lookback, horizons, val_floor_rows, min_train_windows, min_val_windows, min_test_windows, test_frac)}.")
        ends.append(cand)
    ends.reverse()

    folds = []
    for i, end in enumerate(ends, start=1):
        train_end, val_end = _split_for(end, val_floor_rows, train_frac, test_frac)
        folds.append(Fold(index=i, train_end=train_end, val_end=val_end,
                          test_end=end, n_rows=n_rows,
                          val_floor_rows=int(val_floor_rows)))
    folds = tuple(folds)
    assert_folds(folds, lookback=lookback, horizons=horizons,
                 min_val_windows=min_val_windows,
                 min_train_windows=min_train_windows,
                 min_test_windows=min_test_windows, n_rows=n_rows)
    return folds


def max_feasible_k(n_rows: int, growth: float = GROWTH,
                   lookback: int = LOOKBACK, horizons: Sequence[int] = HORIZONS,
                   val_floor_rows: Optional[int] = None,
                   min_train_windows: int = MIN_TRAIN_WINDOWS,
                   min_val_windows: int = MIN_VAL_WINDOWS,
                   min_test_windows: int = MIN_TEST_WINDOWS,
                   test_frac: float = TEST_FRAC) -> int:
    """Largest `k` for which `make_folds` succeeds (0 if not even `k=2` does).

    Used by the error messages so a caller learns the feasible alternative
    instead of only that its request failed.
    """
    if val_floor_rows is None:
        val_floor_rows = val_floor_for(horizons, min_val_windows)
    best = 0
    for k in range(2, 12):
        try:
            make_folds(n_rows, k=k, growth=growth, lookback=lookback,
                       horizons=horizons, val_floor_rows=val_floor_rows,
                       min_val_windows=min_val_windows,
                       min_train_windows=min_train_windows,
                       min_test_windows=min_test_windows, test_frac=test_frac)
        except FoldError:
            break
        best = k
    return best


def assert_folds(folds: Sequence[Fold], lookback: int = LOOKBACK,
                 horizons: Sequence[int] = HORIZONS,
                 min_val_windows: int = MIN_VAL_WINDOWS,
                 min_train_windows: int = MIN_TRAIN_WINDOWS,
                 min_test_windows: int = MIN_TEST_WINDOWS,
                 n_rows: Optional[int] = None) -> bool:
    """Assert the six properties a rolling-origin layout must have.

    1. **Disjoint test segments** — no row is scored by two folds.
    2. **Strictly ordered in time** — `train_end`, `val_end` and `test_end` all
       increase with the fold index, and each fold's test block starts strictly
       after the previous fold's test block ended.
    3. **Expanding window** — fold *i*'s training prefix contains fold *i-1*'s.
    4. **20 % test block / 10 % validation block** — the test block is
       `int(0.20*n)` (+-1 row) and validation is at least `int(0.10*n)`, or the
       documented floor where 10 % cannot yield `min_val_windows` windows.
    5. **Feasible windows** — every split yields at least its minimum number of
       windows on every horizon, so the fold can actually be trained and scored.
    6. **The last fold reaches the last row** — the origin never stops early.

    Returns `True`; raises `FoldError` naming the offending fold otherwise.
    """
    folds = tuple(folds)
    if len(folds) < 2:
        raise FoldError(f"need at least 2 folds, got {len(folds)}")
    if [f.index for f in folds] != list(range(1, len(folds) + 1)):
        raise FoldError(f"fold indices must be 1..{len(folds)}, got "
                        f"{[f.index for f in folds]}")

    prev = None
    for f in folds:
        if f.n_rows is not None and n_rows is not None and f.n_rows != n_rows:
            raise FoldError(f"fold {f.index} n_rows={f.n_rows} != {n_rows}")
        if prev is not None:
            # (2) strictly ordered in time, (3) expanding, (1) disjoint tests
            if not (f.train_end > prev.train_end):
                raise FoldError(
                    f"fold {f.index} train_end={f.train_end} does not extend "
                    f"fold {prev.index} (train_end={prev.train_end})")
            if not (f.val_end > prev.val_end):
                raise FoldError(
                    f"fold {f.index} val_end={f.val_end} does not advance past "
                    f"fold {prev.index} (val_end={prev.val_end})")
            if not (f.test_end > prev.test_end):
                raise FoldError(
                    f"fold {f.index} test_end={f.test_end} is not after fold "
                    f"{prev.index} (test_end={prev.test_end})")
            if f.val_end <= prev.test_end:
                raise FoldError(
                    "TEST SEGMENTS OVERLAP: fold %d scores [%d, %d) but fold %d "
                    "starts its test at %d; need val_end > %d"
                    % (prev.index, prev.val_end, prev.test_end, f.index,
                       f.val_end, prev.test_end))
        # (4) 20 % test block, 10 % (or floored) validation block
        n = f.test_end
        want_test = int(n * TEST_FRAC)
        if abs(f.n_test - want_test) > 1:
            raise FoldError(
                f"fold {f.index} test block is {f.n_test} rows, not ~20%% of its "
                f"{n}-row window ({want_test})")
        want_val = int(n * VAL_FRAC)
        if f.n_val < min(want_val, f.val_floor_rows) - 1:
            raise FoldError(
                f"fold {f.index} validation block is {f.n_val} rows, below both "
                f"10% of its window ({want_val}) and the floor "
                f"({f.val_floor_rows})")
        if f.val_floor_applied and f.val_floor_rows <= want_val:
            raise FoldError(
                f"fold {f.index} widened its validation block to {f.n_val} rows "
                f"although 10% of its window ({want_val}) already exceeded the "
                f"floor ({f.val_floor_rows}); the floor must bind only when needed")
        # (5) window feasibility on every horizon, per split
        for L in horizons:
            wc = f.window_counts(lookback, L)
            for split_name, count, floor in (
                    ("train", wc["n_train_windows"], min_train_windows),
                    ("val", wc["n_val_windows"], min_val_windows),
                    ("test", wc["n_test_windows"], min_test_windows)):
                if count < floor:
                    raise FoldError(
                        f"fold {f.index} is too short for L={L}: {split_name} "
                        f"yields {count} windows (< {floor}); fold window="
                        f"{f.test_end} rows, T={lookback}")
        prev = f

    # (6) the origin must reach the end of the series
    if n_rows is not None and folds[-1].test_end != int(n_rows):
        raise FoldError(
            "the LAST fold must reach the end of the series "
            f"(test_end={folds[-1].test_end} != n_rows={n_rows}); otherwise the "
            "rolling origin never scores the most recent block")
    return True


# ──────────────────────────────────────────────────────────────────────────
# consumers
# ──────────────────────────────────────────────────────────────────────────
def resolve_fold(n_rows: int, fold: Optional[int], k: int = DEFAULT_K,
                 lookback: int = LOOKBACK,
                 horizons: Sequence[int] = HORIZONS,
                 val_floor_rows: Optional[int] = None,
                 min_val_windows: int = MIN_VAL_WINDOWS) -> Optional[Fold]:
    """Return fold number `fold` (1-based), or `None` for the fixed split.

    `fold in (None, 0)` means **"the existing single split"** and returns `None`,
    which is what keeps every current script byte-identical when `--fold` is
    absent. `fold > k` raises rather than silently wrapping.

    `val_floor_rows=None` sizes the validation floor for the longest horizon in
    `horizons` (`val_floor_for`), which is what a runner training all four
    horizons needs; pass `0` for the pure 70/10/20 shape.
    """
    if fold in (None, 0):
        return None
    if val_floor_rows is None:
        val_floor_rows = val_floor_for(horizons, min_val_windows)
    fold = int(fold)
    folds = make_folds(n_rows, k=k, lookback=lookback, horizons=horizons,
                       val_floor_rows=int(val_floor_rows),
                       min_val_windows=min_val_windows)
    if fold < 1 or fold > len(folds):
        raise FoldError(f"--fold {fold} out of range: this series has "
                        f"{len(folds)} folds (1..{len(folds)})")
    return folds[fold - 1]


def resolve_split(profile: str, n_rows: int, fold: Optional[int] = None,
                  k: int = DEFAULT_K, lookback: int = LOOKBACK,
                  horizons: Sequence[int] = HORIZONS,
                  val_floor_rows: Optional[int] = None,
                  min_val_windows: int = MIN_VAL_WINDOWS
                  ) -> Tuple[int, int, Optional[Fold]]:
    """`(train_end, val_end, fold_or_None)` — the single entry point for runners.

    With `fold` unset this returns the profile's own borders
    (`configs.split_for_profile`), i.e. the protocol behind every published
    number, so a caller that passes `None` cannot drift.
    """
    if fold in (None, 0):
        from configs import split_for_profile          # torch-free import
        train_end, val_end = split_for_profile(profile, int(n_rows))
        return int(train_end), int(val_end), None
    f = resolve_fold(n_rows, fold, k=k, lookback=lookback, horizons=horizons,
                     val_floor_rows=val_floor_rows,
                     min_val_windows=min_val_windows)
    return f.train_end, f.val_end, f


def fold_data(data_norm, fold: Fold):
    """Slice the series to what `fold` is allowed to read (`rows[0:test_end]`).

    A fold never sees a row past `test_end`; slicing here — rather than relying
    on `build_windows` to ignore the tail — is what makes the leakage argument
    structural instead of incidental. Without it, `build_windows` would label
    every window from `val_end` to the END of the full series as "test", i.e. a
    fold would be scored on rows it was supposed to hold out.
    """
    import numpy as np                                   # local: torch-free module
    arr = np.asarray(data_norm)
    if fold.test_end > arr.shape[0]:
        raise FoldError(f"fold {fold.index} needs {fold.test_end} rows, series "
                        f"has {arr.shape[0]}")
    return arr[: fold.test_end]


def restrict_data(data_dict, fold: Fold) -> dict:
    """Return a copy of a loaded `data_dict` truncated to `fold`'s window.

    Every runner that honours `--fold` must call this between
    `load_and_normalize(...)` and `build_windows(...)`: it truncates `data_norm`
    to `rows[0:test_end]`, sets `n` to the fold's length, and records the fold so
    it lands in the manifest. `train_df` (the train-only slices used by the
    prompt builders and prompt statistics) is already `rows[0:train_end]` and is
    re-sliced defensively.
    """
    if fold.test_end > int(data_dict["data_norm"].shape[0]):
        raise FoldError(f"fold {fold.index} needs {fold.test_end} rows, series "
                        f"has {data_dict['data_norm'].shape[0]}")
    out = dict(data_dict)
    out["data_norm"] = fold_data(data_dict["data_norm"], fold)
    out["n"] = int(fold.test_end)
    if data_dict.get("train_df") is not None:
        out["train_df"] = data_dict["train_df"].iloc[: fold.train_end]
    out["fold"] = fold.as_dict()
    out["split_source"] = "walk_forward_fold"
    return out


def add_fold_argument(ap: argparse.ArgumentParser, k: int = DEFAULT_K) -> None:
    """Add the shared `--fold` hook to a runner's parser (identical in all runners).

    Default `0` = the existing single split. Additive by design: a runner that
    never passes `--fold` behaves exactly as before the hook existed.
    """
    ap.add_argument(
        "--fold", type=int, default=0,
        help="Rolling-origin fold (1..%d) from scripts/walk_forward.py; "
             "0 (default) = the existing single fixed split, unchanged." % k)


def fold_from_args(args, n_rows: int, profile: str, horizon: Optional[int] = None,
                   k: int = DEFAULT_K):
    """Convenience wrapper: `(train_end, val_end, Fold|None)` from parsed args.

    `horizon` (when given) sizes the validation floor for that single horizon;
    otherwise the floor is sized for the longest horizon in `HORIZONS`, so one
    fold geometry serves the whole run.
    """
    fold = int(getattr(args, "fold", 0) or 0)
    if not fold:
        return resolve_split(profile, n_rows, None)
    horizons = (int(horizon),) if horizon is not None else HORIZONS
    return resolve_split(profile, n_rows, fold, k=k, horizons=horizons)


# ──────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Print / validate the rolling-origin folds for a series.")
    ap.add_argument("--rows", type=int, default=966,
                    help="Rows of the series (966 = A-track national).")
    ap.add_argument("--k", type=int, default=DEFAULT_K)
    ap.add_argument("--growth", type=float, default=GROWTH)
    ap.add_argument("--lookback", type=int, default=LOOKBACK)
    ap.add_argument("--horizons", default=",".join(str(h) for h in HORIZONS),
                    help="Comma-separated horizons for the feasibility check.")
    ap.add_argument("--val-floor-rows", type=int, default=None,
                    help="Validation rows the earliest folds keep; default = "
                         "sized for the longest horizon (see val_floor_for).")
    ap.add_argument("--pure-shape", action="store_true",
                    help="Force val_floor_rows=0 (pure 70/10/20). On 966 rows "
                         "this is infeasible for K=5 at L>=36 and reports why.")
    ap.add_argument("--json", action="store_true", help="Emit JSON, not a table.")
    a = ap.parse_args(argv)
    horizons = tuple(int(x) for x in a.horizons.split(",") if x.strip())
    floor = 0 if a.pure_shape else (
        a.val_floor_rows if a.val_floor_rows is not None
        else val_floor_for(horizons))

    try:
        folds = make_folds(a.rows, k=a.k, growth=a.growth, lookback=a.lookback,
                           horizons=horizons, val_floor_rows=floor)
    except FoldError as exc:
        print("[walk-forward] INFEASIBLE: %s" % exc)
        print("[walk-forward] largest feasible k for this series/horizons: %d"
              % max_feasible_k(a.rows, a.growth, a.lookback, horizons, floor))
        return 2

    if a.json:
        print(json.dumps([f.as_dict() for f in folds], indent=2))
        return 0
    print("rolling origin: %d folds over %d rows, expanding window, 70/10/20 "
          "test-block, containment=strict, T=%d, val_floor_rows=%d"
          % (len(folds), a.rows, a.lookback, floor))
    for f in folds:
        print("  " + f.describe(a.lookback, horizons))
    print("  all assertions passed: disjoint test segments, strictly ordered, "
          "expanding, 20% test block, windows feasible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
