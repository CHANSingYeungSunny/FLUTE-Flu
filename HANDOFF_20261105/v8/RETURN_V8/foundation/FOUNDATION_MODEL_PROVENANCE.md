# FOUNDATION MODEL PROVENANCE — TASK 2 (v8)

Two faithful, source-pinned **numerical** time-series foundation-model controls
(Chronos family, TimesFM family). This roster is deliberately **separate** from
the 11 frozen language encoders and from the frozen 28-arm family; it must not be
merged into them (AGENTS.md RULE 4 / NEXT_DEEPSEEK_PROMPT HARD RULE 7).

Verified on **2026-11-06 (UTC)** from the Windows project root, by exact
commands recorded in `HANDOFF_20261105/v8/evidence/foundation_*`.
This document is **provenance only**: no model inference was run, no
`torch.load` / `import torch` / `transformers` / `from_pretrained` was executed,
and **no measured model result is claimed**. See `T2_VERDICT.md` for status.

---

## 0. Benchmark contract these controls must be adapted to

| item | value |
|---|---|
| lookback | `T = 104` |
| horizons | `L ∈ {24, 36, 48, 60}` |
| channels | `SEVEN` standardized channels (z-space) |
| seeds | `2021–2030` |
| scoring space | benchmark z-space (standardized) |

Every context/prediction limit below is compared against this contract.

---

## 1. Chronos family

### 1.1 Source / package / tag (exact, verified)

| item | value | verification |
|---|---|---|
| repo | `amazon-science/chronos-forecasting` | `https://github.com/amazon-science/chronos-forecasting` → HTTP 200 |
| licence | Apache-2.0 | PyPI JSON `info.license = "Apache License Version 2.0, January 2004 ..."` |
| PyPI | `chronos-forecasting 2.3.2` | `https://pypi.org/pypi/chronos-forecasting/json` → HTTP 200, `info.version = 2.3.2` |
| release / tag | `v2.3.2`, published `2026-09-08T14:06:51Z` | `https://api.github.com/repos/amazon-science/chronos-forecasting/releases/latest` → HTTP 200, `tag_name=v2.3.2` |
| release URL | `https://github.com/amazon-science/chronos-forecasting/releases/tag/v2.3.2` | observed `html_url` in the release JSON |
| tag commit | `0aba28e9360b6355d5a919596c90b16c25939f02` | `https://api.github.com/repos/amazon-science/chronos-forecasting/commits/0aba28e9360b6355d5a919596c90b16c25939f02` → HTTP 200; commit date `2026-09-08T14:04:54Z`, msg `Bump version to 2.3.2 (#533)` |

### 1.2 HF checkpoints — exact repo id + revision + licence

All revisions were re-verified against `https://huggingface.co/api/models/<repo_id>`
(HTTP 200, `sha` and `cardData.license` read back) and against a pinned-revision
`resolve` probe (`.../resolve/<sha>/config.json` → 307 redirect to CDN = pin valid).

| model | repo_id | pinned revision | licence |
|---|---|---|---|
| Chronos-Bolt-Tiny (9M) | `amazon/chronos-bolt-tiny` | `a0e552de83495b5c28c14c71c374f3e33280b340` | apache-2.0 |
| Chronos-T5-Small | `amazon/chronos-t5-small` | `a971ba21945c4f1796b17a91fe69214b5f4ad472` | apache-2.0 |
| Chronos-Bolt-Base | `amazon/chronos-bolt-base` | `5d9f166d69f47aef3401367a7b842e78fe97b121` | apache-2.0 |
| Chronos-2 | `amazon/chronos-2` | `29ec3766d36d6f73f0696f85560a422f50e8498c` | apache-2.0 |

HF API `gated=false`, `private=false` for all four.

### 1.3 Capability table (verified from the official Chronos-2 model card)

Source: `https://huggingface.co/amazon/chronos-2/raw/29ec3766d36d6f73f0696f85560a422f50e8498c/README.md`
(the pinned revision). Verbatim rows:

```
| Capability              | Chronos-2 | Chronos-Bolt | Chronos |
| Univariate Forecasting  | ✅        | ✅           | ✅      |
| Multivariate Forecasting| ✅        | ❌           | ❌      |
| Max. Context Length     | 8192      | 2048         | 512     |
| Max. Prediction Length  | 1024      | 64           | 64      |
```

Also verbatim: `license: apache-2.0`, and
`Chronos & Chronos-Bolt do not natively support future covariates ...`.

**Careful reading (no over-claim):** the third column is labelled `Chronos`
(the original T5 family), **not** literally `Chronos-T5`. The card does **not**
contain the string `Chronos-T5` and does **not** literally state
`T5/Bolt are univariate`. What it does state unambiguously is that
`Multivariate Forecasting` is `❌` for the `Chronos` and `Chronos-Bolt` columns
and `✅` only for `Chronos-2`. Because the benchmark needs 7 channels, the
original-T5 and Bolt checkpoints must therefore be treated as **univariate**
through the adapter in §3; they cannot consume the 7 channels jointly.

### 1.4 Context / prediction / channel limits vs benchmark

- Chronos-T5: context `512`, max prediction `64`. `T=104` and `L≤60` fit.
- Chronos-Bolt: context `2048`, max prediction `64`. `T=104` and `L≤60` fit.
- Chronos-2: context `8192`, max prediction `1024`, **native multivariate**.
  It fits and would need no channel adapter, but it is a different architecture
  and was **not** downloaded in this task (see `T2_VERDICT.md`).
- T5/Bolt are univariate → 7 channels require the adapter in §3.

### 1.5 Internal normalization (verified)

`https://huggingface.co/amazon/chronos-t5-small/raw/a971ba21945c4f1796b17a91fe69214b5f4ad472/README.md`
states verbatim:

> `A time series is transformed into a sequence of tokens via scaling and quantization, and a language model is trained on these tokens using the cross-entropy loss.`
> `The input time series is scaled and quantized to obtain a sequence of tokens.`
> `During inference, we autoregressively sample tokens from the model and map them back to numerical values.`

So Chronos applies **its own** scaling/quantization to whatever numeric sequence
it is given, then maps tokens back. Feeding benchmark z-scores is therefore
**not** equivalent to feeding the original-scale series. The card does not
publish the exact scaling denominator, so the convention must be fixed and
documented by the adapter (§3, limit 2).

---

## 2. TimesFM family

### 2.1 Source / package / tag (exact, verified)

| item | value | verification |
|---|---|---|
| repo | `google-research/timesfm` | `https://github.com/google-research/timesfm` → HTTP 200 |
| source licence | Apache-2.0 | GitHub README, verbatim: `The TimesFM source code in this repository is licensed under Apache-2.0` |
| PyPI | `timesfm 3.0.2` | `https://pypi.org/pypi/timesfm/json` → HTTP 200, `info.version = 3.0.2`, `info.license = Apache-2.0` |
| tags (observed) | `v3.0.2`, `v3.0.0`, `v2.0.2`, `v2.0.1`, `v1.2.6`, `v1.2.1` | `https://api.github.com/repos/google-research/timesfm/tags` → HTTP 200 |
| `v3.0.0` commit | `331c6d33cb1ac2611de3056d0ac7164aab6301eb` | tag JSON `commit.sha`; `/commits/<sha>` → HTTP 200 |
| `v1.2.6` commit | `e77303c5513c84aa8b32639851c3f7f92f59645e` | tag JSON `commit.sha`; `/commits/<sha>` → HTTP 200 |
| weights ≤ 2.5 licence | Apache-2.0 | GitHub README verbatim: `model weights up to version 2.5 remain Apache-2.0` |
| 1.0/2.0 code path | archived in `v1/`; `pip install timesfm==1.3.0` | GitHub README verbatim (attributed, not re-verified on PyPI here) |
| 3.0 weights licence | `timesfm-non-commercial-license-v1.0` (non-commercial, non-production) | §2.4 |

### 2.2 HF checkpoints — exact repo id + revision + licence

| model | repo_id | pinned revision | licence |
|---|---|---|---|
| TimesFM 1.0 200M | `google/timesfm-1.0-200m` | `8775f7531211ac864b739fe776b0b255c277e2be` | apache-2.0 |
| TimesFM 2.0 500M (PyTorch) | `google/timesfm-2.0-500m-pytorch` | `dc2443792ce5516872b89b37cf1bc058c3bf0c10` | apache-2.0 |
| TimesFM 3.0 (PyTorch) | `google/timesfm-3.0-pytorch` | `43046b85ec22d584a13f8098c2ed39c889e129c2` | `timesfm-non-commercial-license-v1.0` (HF API `cardData.license = other`) |

**Invalid repo (verified):** `google/timesfm-2.0-500m` (without `-pytorch`) is
**not a usable repository**. Observed:
`https://huggingface.co/api/models/google/timesfm-2.0-500m` → **HTTP 401**,
body `{"error":"Invalid username or password."}`; and
`https://huggingface.co/google/timesfm-2.0-500m/resolve/main/config.json` →
**HTTP 401**. It must not be used as a substitute.

**No `config.json` in TimesFM 1.0 200M (verified):** the HF API siblings for
`google/timesfm-1.0-200m` are
`.gitattributes`, `README.md`,
`checkpoints/checkpoint_1100000/descriptor/descriptor.pbtxt`,
`checkpoints/checkpoint_1100000/metadata/metadata`,
`checkpoints/checkpoint_1100000/state/checkpoint`.
A pinned `resolve/8775f753.../config.json` returns **HTTP 404**. It is a Flax
checkpoint repo, not a standard `transformers` config repo; it must be loaded
through the `v1` code path, not the 3.0 package. This is why the local probe
for this repo fetched only `README.md`.

### 2.3 Context / prediction / channel / frequency limits (verified)

`google/timesfm-1.0-200m` card (pinned revision), verbatim:

> `It performs univariate time series forecasting for context lengths up to 512 time points and any horizon lengths, with an optional frequency indicator.`
> `The horizon length can be set to anything.`
> `license: apache-2.0`

`google/timesfm-2.0-500m-pytorch` card (pinned revision), verbatim:

> `It performs univariate time series forecasting for context lengths up to 2048 time points and any horizon lengths, with an optional frequency indicator.`
> `Note that it can go even beyond 2048 context even though it was trained with that as the maximum context.`
> `license: apache-2.0`

Both cards: `TimesFM expects a categorical indicator valued in {0, 1, 2}`:

> `0` (default): high frequency, up to daily granularity.
> `1`: medium frequency time series. We recommend using this for **weekly** and monthly data.
> `2`: low frequency, beyond monthly (quarterly, yearly).
> For dataframe inputs: `- 1: W, M`
> `Notice you do NOT have to strictly follow our recommendation here. ... you can also view the frequency input as a free parameter ...`

Therefore, for a faithful **weekly** ILI benchmark, set **`freq = 1`** for
TimesFM 1.0 / 2.0. This is the training-time convention (recommended, not
hard-required by the card); it must be fixed and recorded. TimesFM 2.5+ removed
the frequency indicator entirely (GitHub README verbatim: `gets rid of the
frequency indicator`), so this requirement is specific to 1.0/2.0.

**Normalization:** the 1.0 and 2.0 model cards do **not** document any
normalization/scaling of the input series (explicitly checked; the 2.0 card
only mentions NaN linear interpolation and padding/truncation). Consequently
the adapter must **not assume** the model preserves the benchmark z-space, and
must handle z-space explicitly (§3, limit 2).

**Benchmark fit:** `T=104` ≤ 512 (1.0) and ≤ 2048 (2.0); `L≤60` is allowed
("any horizon lengths"). Both are **univariate** → the 7-channel adapter §3 is
mandatory.

### 2.4 TimesFM 3.0 licence — excluded

`https://github.com/google-research/timesfm` README, verbatim:

> `Important: The TimesFM source code in this repository is licensed under Apache-2.0, and model weights up to version 2.5 remain Apache-2.0. However, TimesFM 3.0 pretrained weights are distributed under the separate timesfm-non-commercial-license-v1.0 license and are restricted to non-commercial, non-production use. Commercial or production use of downloaded / self-hosted weights is not permitted.`
> `Commercial and production use of TimesFM 3.0 is fully permitted through authorized Google Cloud services, including BigQuery ML, which are governed by the Google Cloud Terms of Service.`

TimesFM 3.0 is **natively multivariate** and would avoid the per-channel
adapter, but self-hosted 3.0 weights are **non-commercial / non-production**.
Running them as local self-hosted controls on the project HPC is outside that
licence; the permitted path is an authorized Google Cloud service, which is not
a faithful local control. **TimesFM 3.0 is therefore excluded from this
benchmark on licence grounds.** HF API additionally reports
`cardData.license = other` for `google/timesfm-3.0-pytorch`.

---

## 3. Documented minimal adapter: per-channel independent forecasting

Because Chronos T5/Bolt and TimesFM 1.0/2.0 are univariate and the benchmark has
SEVEN channels, the minimal faithful adapter is **channel independence**
(per-channel independent forecasting):

```
for c in 1..7:                       # c indexes the 7 standardized channels
    x_c = X[:, c]                    # 1-D lookback of length T=104
    y_c = model.forecast(x_c, horizon=L, freq=1_if_timesfm_1_0_or_2_0)
    Yhat[:, c] = y_c                # stack the 7 independent forecasts
score(Yhat, Y_true) in benchmark z-space
```

This is the **only** adapter used for the Apache-2.0 univariate checkpoints;
Chronos-2 / TimesFM-3.0 (native multivariate) are not part of this adapter.

### 3.1 Scientific limits (must be reported alongside any future result)

1. **Discards cross-channel dependence.** Each of the 7 channels is forecast in
   isolation; no inter-channel correlation, lead–lag, or cross-region/cross-signal
   coupling is modelled. Any skill that depends on cross-channel structure is
   structurally unavailable. The resulting control is a *channel-independent
   univariate zero-shot* baseline, **not** a multivariate model, and must never
   be described as one.

2. **Internal normalization vs benchmark z-space must be handled explicitly.**
   The benchmark channels are standardized (z-scores). Chronos applies its own
   `scaling and quantization` to whatever it is given and `map[s] them back to
   numerical values` (§1.5); TimesFM 1.0/2.0 cards document no normalization at
   all (§2.3), so the effective input distribution cannot be assumed. Feeding
   raw z-scores is therefore **not** equivalent to feeding the original-scale
   series, and metrics computed in z-space are only meaningful under a single,
   fixed, recorded convention. The adapter must either
   (a) de-standardize each channel with the **exact benchmark mean/std** before
   forecasting and re-standardize the forecast with the same constants before
   scoring, or
   (b) keep z-space throughout and explicitly document that the model re-scales
   internally, reporting which convention was used.
   **Never mix the two conventions silently.** This is a documented limit, not
   a measured result.

3. **`freq = 1` for weekly data (TimesFM 1.0 / 2.0).** The categorical
   frequency indicator ∈ {0,1,2}; weekly (`W`) maps to `1` (§2.3). Set
   `freq=1` and record that the card calls this a recommendation. TimesFM 2.5+
   dropped the indicator, so this does not generalize to newer versions.

4. **Context / horizon are compatible, channels are not.** `T=104` and
   `L∈{24,36,48,60}` fit within all listed context/prediction limits (§1.4,
   §2.3); the binding constraint is the 7-channel requirement, resolved only by
   the adapter above. Chronos-2 (native multivariate) and TimesFM-3.0 would
   avoid it but were not used (§2.4, `T2_VERDICT.md`).

5. **TimesFM 3.0 non-commercial licence.** Self-hosted 3.0 weights are
   excluded (§2.4); the benchmark must use the Apache-2.0 weights (≤ 2.5).

6. **Pretraining domain proximity (not leakage).** See §4; any "zero-shot"
   claim must be qualified by indirect domain proximity.

---

## 4. Pretraining overlap facts (stated explicitly)

- **TimesFM** — `https://arxiv.org/html/2310.10688v4`, Section 5
  *Pretraining Details*, **Table 1: Composition of TimesFM pretraining
  dataset** was retrieved and read. Verbatim:
  > `We address this problem by sourcing the bulk of data used to train our models from three major sources: Google trends, Wiki Pageview statistics and synthetic time-series.`
  Table 1 rows include `Trends hourly/daily/weekly/monthly`,
  `Wiki hourly/daily/weekly/monthly`, `Synthetic`, `Electricity`, `Traffic`,
  `Weather`, `Favorita Sales`, `LibCity`, and `M4 hourly/daily/monthly/quarterly/yearly`.
  The paper also states `These datasets have been intentionally held out from
  our pretraining data` about its evaluation sets.
  **No `CDC ILI`, `influenza`, `epidemiological`, or `health surveillance`
  dataset appears in Table 1 or Section 5.** `https://arxiv.org/abs/2310.10688v4`
  → HTTP 200.

- **Chronos** — `https://huggingface.co/api/datasets/autogluon/chronos_datasets`
  → HTTP 200; `cardData.configs` length = **67** (verified here; the "67 configs"
  fact is confirmed), `sha = eeecad0b82a8c237e212ce6f8d1abecb513e2cec`,
  `siblings_count = 1243`. Per the handoff research facts, this corpus contains
  **no CDC ILI / influenza labels**; the 67 individual configs were **not**
  enumerated in this task (stated honestly, not claimed as verified).

- **Indirect domain proximity (a confound, not label leakage).** Google Trends
  search-interest and Wikipedia pageview time series (verified TimesFM Table 1)
  can correlate with population-level respiratory-illness behaviour and with
  media attention around influenza seasons. This is **indirect domain
  proximity**, not direct CDC ILI / influenza label leakage. Any future
  "zero-shot" claim for these controls must be qualified by this proximity.

---

## 5. Exact URLs actually requested on 2026-11-06 (UTC)

HF model API (all HTTP 200 unless noted):
`https://huggingface.co`
`https://huggingface.co/api/models/amazon/chronos-bolt-tiny`
`https://huggingface.co/api/models/amazon/chronos-t5-small`
`https://huggingface.co/api/models/amazon/chronos-bolt-base`
`https://huggingface.co/api/models/amazon/chronos-2`
`https://huggingface.co/api/models/google/timesfm-1.0-200m`
`https://huggingface.co/api/models/google/timesfm-2.0-500m-pytorch`
`https://huggingface.co/api/models/google/timesfm-2.0-500m` → **401**
`https://huggingface.co/api/models/google/timesfm-3.0-pytorch`
`https://huggingface.co/api/datasets/autogluon/chronos_datasets`
`https://huggingface.co/google/timesfm-2.0-500m/resolve/main/config.json` → **401**

Pinned `resolve` (all **307** = valid pin, CDN redirect, except one):
`https://huggingface.co/<repo>/resolve/<sha>/config.json` and `.../README.md`
for the 6 pinned revisions in §1.2 / §2.2 — see
`v8/evidence/foundation_commit_and_pin_verification.txt`; the single
**404** is `google/timesfm-1.0-200m/resolve/8775f753.../config.json`.

Model-card / repo content:
`https://huggingface.co/amazon/chronos-2/raw/29ec3766d36d6f73f0696f85560a422f50e8498c/README.md`
`https://huggingface.co/amazon/chronos-t5-small/raw/a971ba21945c4f1796b17a91fe69214b5f4ad472/README.md`
`https://huggingface.co/google/timesfm-1.0-200m/raw/8775f7531211ac864b739fe776b0b255c277e2be/README.md`
`https://huggingface.co/google/timesfm-2.0-500m-pytorch/raw/dc2443792ce5516872b89b37cf1bc058c3bf0c10/README.md`
`https://github.com/google-research/timesfm`
`https://arxiv.org/html/2310.10688v4`
`https://arxiv.org/abs/2310.10688v4`

GitHub / PyPI API:
`https://github.com/amazon-science/chronos-forecasting`
`https://api.github.com/repos/amazon-science/chronos-forecasting/releases/latest`
`https://api.github.com/repos/amazon-science/chronos-forecasting/commits/0aba28e9360b6355d5a919596c90b16c25939f02`
`https://api.github.com/repos/google-research/timesfm/tags`
`https://api.github.com/repos/google-research/timesfm/commits/331c6d33cb1ac2611de3056d0ac7164aab6301eb`
`https://api.github.com/repos/google-research/timesfm/commits/e77303c5513c84aa8b32639851c3f7f92f59645e`
`https://pypi.org/pypi/chronos-forecasting/json`
`https://pypi.org/pypi/timesfm/json`

---

## 6. Scope of local download (honest statement)

Full pinned weight download was **NOT completed**. Only `config.json` +
`README.md` (plus Hub metadata cache files) were fetched with
`huggingface_hub.snapshot_download(..., allow_patterns=["config.json","README.md"])`
at the pinned revisions, as a connectivity/pin probe. The actual weight tensors
were **not** present after the probes:

| checkpoint | weight files that remain UNDOWNLOADED |
|---|---|
| `amazon/chronos-bolt-tiny` | `model.safetensors` |
| `amazon/chronos-t5-small` | `model.safetensors` |
| `google/timesfm-1.0-200m` | `checkpoints/checkpoint_1100000/state/checkpoint`, `.../metadata/metadata`, `.../descriptor/descriptor.pbtxt` |

Exact bytes, file counts, SHA-256 and exit codes are in
`v8/evidence/foundation_probe_*.log` and `foundation_all_files.sha256`.
No tar was created, no `scp` was performed, no pilot, no 80-cell matrix — see
`T2_VERDICT.md`.
