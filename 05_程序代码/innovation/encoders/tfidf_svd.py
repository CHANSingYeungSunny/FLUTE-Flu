"""
tfidf_svd.py — TF-IDF + TruncatedSVD text encoder (train-only fit).
==================================================================

IMPORTANT LIMITATION (revision 6)
---------------------------------
The MIFlu prompt is a SINGLE formatted string per horizon: its variables are the
train-set min/max statistics, which are identical across all training weeks.
The prompt therefore varies ONLY by the horizon `L`. Across the four horizons
there are AT MOST 4 distinct prompts — one per horizon — and zero variation
within a horizon. The resulting TF-IDF+SVD context is consequently a
FIXED CONTEXTUAL EMBEDDING baseline (constant across weeks), not a per-window
text feature. The audit (`results/innovation/audit/prompt_variation_report.json`)
records the exact unique-prompt count and embedding variance so this can never
be silently overstated.

Fitting uses TRAIN prompts only (leakage gate: `fit_on_train_only`).
"""

from __future__ import annotations

import numpy as np

from innovation.interfaces import TextEncoder
from innovation.paths import HORIZONS


class TfidfSvdEncoder(TextEncoder):
    name = "tfidf_svd"

    def __init__(self, n_components: int = 16, horizon: int | None = None):
        self.n_components = int(n_components)
        self.horizon = horizon
        self.vectorizer = None
        self.svd = None
        self._vecs: dict[int, np.ndarray] = {}
        self._dim: int | None = None
        try:
            import sklearn  # noqa: F401
            self._sklearn = True
        except Exception:
            self._sklearn = False
            self.availability_note = "UNAVAILABLE_LOCAL_DEPENDENCY: sklearn missing"

    def is_available(self) -> bool:
        return bool(getattr(self, "_sklearn", False))

    def fit_on_train_only(self, train_df, horizon: int, seed: int) -> None:
        if not self.is_available():
            raise RuntimeError("UNAVAILABLE_LOCAL_DEPENDENCY: sklearn not installed")
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        from textual_embedder import build_prompt

        # Prompts for ALL horizons, built from train_df ONLY.
        prompts = {L: build_prompt(train_df, T=104, L=L) for L in HORIZONS}
        corpus = [prompts[L] for L in HORIZONS]
        self.vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 1))
        X = self.vectorizer.fit_transform(corpus)
        n_comp = max(1, min(self.n_components, X.shape[0] - 1, X.shape[1] - 1))
        self.svd = TruncatedSVD(n_components=n_comp, random_state=int(seed))
        self.svd.fit(X)
        for L in HORIZONS:
            self._vecs[L] = self.svd.transform(
                self.vectorizer.transform([prompts[L]]))[0]
        self._dim = int(n_comp)
        self.horizon = int(horizon)

    def encode(self, batch_size: int, device: str = "cpu", horizon: int | None = None):
        import torch

        h = int(horizon if horizon is not None else self.horizon)
        if h not in self._vecs:
            raise KeyError(f"encoder not fitted for horizon {h}")
        v = torch.as_tensor(self._vecs[h], dtype=torch.float32)
        return v.view(1, 1, -1).expand(batch_size, 1, -1).to(device)

    def context_dim(self):
        return self._dim

    def describe(self) -> dict:
        d = super().describe()
        d["kind"] = "fixed_contextual_embedding_baseline"
        d["unique_prompts"] = len(HORIZONS)
        return d
