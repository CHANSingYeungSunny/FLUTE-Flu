# Architecture equivalence (pre-HPC)

Fidelity levels: `REFERENCE_FAITHFUL`, `REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS`, `INSPIRED_SIMPLIFICATION`.

## `dlinear` — **REFERENCE_FAITHFUL**

- display name: DLinear (Zeng et al., AAAI 2023)
- published: DLinear (Zeng et al., AAAI 2023)

Component-level evidence (file:line):
  - `backbones/dlinear.py:26-37 moving-average decomposition (AvgPool1d stride 1, replication padding)`
  - `backbones/dlinear.py:58-61 seasonal = x - trend`
  - `backbones/dlinear.py:47-56 Linear(T->L) applied along the TIME axis, weights shared across channels (individual=False default)`
  - `backbones/dlinear.py:43 kernel_size=25 (the paper default)`

Deviations: none material.

## `nlinear` — **REFERENCE_FAITHFUL**

- display name: NLinear (Zeng et al., AAAI 2023)
- published: NLinear (Zeng et al., AAAI 2023)

Component-level evidence (file:line):
  - `backbones/dlinear.py:97-98 last = x[:, :, -1:] (last-value subtraction)`
  - `backbones/dlinear.py:92-94 shared Linear(T->L) along the time axis`
  - `backbones/dlinear.py:104 last value added back`

Deviations: none material.

## `patchtst` — **INSPIRED_SIMPLIFICATION**

- display name: PatchTST-inspired (supervised, reduced-capacity re-implementation)
- published: PatchTST (Nie et al., ICLR 2023)

Component-level evidence (file:line):
  - `backbones/patchtst.py:54-55 channel-independent patching via unfold`
  - `backbones/patchtst.py:43 shared Linear(patch_len -> d_model) patch embedding`
  - `backbones/patchtst.py:44 learnable per-patch positional embedding`
  - `backbones/patchtst.py:45-49 TransformerEncoder (dim_feedforward=2*d_model, gelu)`
  - `backbones/patchtst.py:50,58 flatten head Linear(n_patches*d_model -> L)`

Deviations from the published architecture:
  - **training regime** — no self-supervised pretraining (paper: pretrain + fine-tune) (`backbones/patchtst.py:14-19,68-71`, disclosed=True)
  - **instance normalisation** — no RevIN / InstanceNorm applied before patching (`backbones/patchtst.py:53-55`, disclosed=True)
  - **patching** — no end-padding to cover the tail of the series (`backbones/patchtst.py:41`, disclosed=True)
  - **capacity** — d_model=64, n_heads=4, n_layers=2 (below paper scale) (`backbones/patchtst.py:33-35`, disclosed=True)

## `itransformer` — **REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS**

- display name: iTransformer (Liu et al., ICLR 2024) — aligned, with disclosed deviations
- published: iTransformer (Liu et al., ICLR 2024 Spotlight)

Component-level evidence (file:line):
  - `backbones/itransformer.py:34 variate embedding = shared Linear(T -> d_model)`
  - `backbones/itransformer.py:43-47 TransformerEncoder over variate TOKENS => cross-variate attention`
  - `backbones/itransformer.py:41,47 shared Linear(d_model -> L) head per variate`
  - `backbones/itransformer.py:36-40 norms are only the encoder layer's own LayerNorms`

Deviations from the published architecture:
  - **normalisation** — no per-variate InstanceNorm/RevIN layer (paper normalises the variate representations) (`backbones/itransformer.py:36-40`, disclosed=True)
  - **positional encoding** — adds a learnable PER-VARIATE positional embedding; the published iTransformer uses NO positional encoding (it is permutation-invariant over variates) (`backbones/itransformer.py:35`, disclosed=True)
  - **capacity** — d_model=64, n_heads=4, n_layers=2 (`backbones/itransformer.py:28-30`, disclosed=True)

## `fusion_forecaster` — **None**

- display name: None
- published: None

Deviations: none material.

## `gpt2_miflu` — **REFERENCE_FAITHFUL**

- display name: MIFlu (IEEE JBHI 2025) — exact adapter
- published: MIFlu (IEEE JBHI 2025, DOI 10.1109/JBHI.2025.3561214)

Component-level evidence (file:line):
  - `backbones/gpt2_miflu_adapter.py:45 imports the existing miflu_model.MIFlu`
  - `backbones/gpt2_miflu_adapter.py:49-52 builds the existing MIFlu unchanged`
  - `backbones/gpt2_miflu_adapter.py:54-59 unpacks the 4-tuple and returns yh_rev (z-space) only`
  - `miflu_model.py:522-575 MIFlu.forward returns (y_hat_rev, y_phys, means, stdevs)`

Deviations from the published architecture:
  - **physical branch** — adapter passes train_mean=0/train_std=1 placeholders and discards y_phys (the runner inverts with the scaler instead) (`backbones/gpt2_miflu_adapter.py:55-59`, disclosed=True)
