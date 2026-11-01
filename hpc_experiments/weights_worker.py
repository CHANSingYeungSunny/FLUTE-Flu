#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""weights_worker.py — helper for `hpc_experiments/cpu_download_worker.sh`.

WHY THIS MODULE EXISTS
----------------------
The LLM arms of the benchmark (`docs/LLM_ARMS.md` §7, 14 frozen-encoder arms)
are blocked on **weights**, not on design: 13 of the 14 have `weights: missing`
in `hpc_experiments/queue/arms_registry.json`. Fetching them is a CPU job (the
`tiny`/`batch` partitions have outbound internet through the CityU proxy), which
is exactly why it must not run on the login node and must not need a GPU.

The bash worker owns the Slurm mechanics (gres-free header, `mem <= cpus*1024`,
wall clock, `scontrol requeue` near the limit). This module owns everything that
must be **testable on a laptop**: the arm list, revision pinning, the manifest
schema/parser, the coverage check, and the hidden-state probe. `tests/
test_cpu_download_worker.py` exercises all of that with no network and no model
download.

WHAT "SUPPORTED" MEANS
----------------------
An arm is `OK` only when the smoke probe proves the model can emit **per-layer
hidden states** (not merely a pooled `last_hidden_state`/CLS vector), because the
benchmark's `scripts/llm_encoder_backbone.py` mean-pools the last hidden state
per token. Anything else is recorded as `UNSUPPORTED` **with the reason** — never
silently dropped, and never counted as a usable arm.

The probe has two levels:

* `probe_config` (default, cheap): build the model class from its own config with
  `num_hidden_layers = 2` and random weights, then run one forward with
  `output_hidden_states=True`. This costs no disk and no checkpoint download and
  answers the only architectural question: does this class expose per-layer
  hidden states through the standard API?
* `probe_checkpoint` (opt-in, `--probe-checkpoint`): load the real weights when
  the parameter count is under `--max-params-b` (default 8 B) and repeat the
  probe. Larger arms stay `UNSUPPORTED` for the *checkpoint* probe with an
  explicit `reason`, while their architectural result is still recorded.

Usage (the bash worker calls these; they are also the test surface)::

    python hpc_experiments/weights_worker.py arms
    python hpc_experiments/weights_worker.py check  --manifest M --registry R
    python hpc_experiments/weights_worker.py coverage --manifest M --registry R
    python hpc_experiments/weights_worker.py check-hidden-states --json FILE
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

#: The 10 Tencent models of the LLM roster (all `tencent/*` entries of
#: `hpc_experiments/queue/arms_registry.json`), in registry order.
TENCENT_PREFIX = "tencent/"

#: The one non-Tencent model the download worker must fetch (the 33 B arm whose
#: 66 GB transfer was left incomplete — `docs/WORK_BREAKDOWN.md` §13.E).
EXTRA_MODELS = ("deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",)

#: Statuses a manifest entry may carry. `PENDING` exists so a crashed run leaves
#: a resumable record instead of a half-truth.
STATUSES = ("OK", "UNSUPPORTED", "FAILED", "PENDING")

SCHEMA = 1


# ──────────────────────────────────────────────────────────────────────────
# registry / arm selection
# ──────────────────────────────────────────────────────────────────────────
def read_registry(path: str) -> dict:
    """Read `arms_registry.json` (the queue owner's single source of truth)."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if "arms" not in data or not isinstance(data["arms"], list):
        raise ValueError(f"{path}: no `arms` list — is this arms_registry.json?")
    return data


def required_arms(registry: dict) -> list:
    """The models this worker must fetch: the 10 Tencent arms + DeepSeek-32B.

    Order is deterministic (registry order, then the extra models), so a resumed
    run and a fresh run touch arms in the same sequence.
    """
    arms = []
    seen = set()
    for arm in registry.get("arms", []):
        hf_id = arm.get("hf_id")
        if not hf_id or hf_id in seen:
            continue
        if hf_id.startswith(TENCENT_PREFIX) or hf_id in EXTRA_MODELS:
            arms.append({"hf_id": hf_id,
                         "label": arm.get("label") or hf_id.replace("/", "__"),
                         "revision": arm.get("revision"),
                         "venv": arm.get("venv", "hpc"),
                         "params_b": arm.get("params_b")})
            seen.add(hf_id)
    for hf_id in EXTRA_MODELS:                   # present even if the registry lags
        if hf_id not in seen:
            arms.append({"hf_id": hf_id, "label": hf_id.replace("/", "__"),
                         "revision": None, "venv": "hpc", "params_b": None})
            seen.add(hf_id)
    return arms


# ──────────────────────────────────────────────────────────────────────────
# hidden-state probe
# ──────────────────────────────────────────────────────────────────────────
def check_hidden_states(hidden_states, expect_layers: int = 2) -> dict:
    """Validate that a forward pass exposed **per-layer** hidden states.

    `hidden_states` is what `transformers` returns with
    `output_hidden_states=True`: a tuple of `L+1` tensors, each `(batch, seq, D)`
    (`[0]` = embeddings, `[1:]` = the layers). This is the property the benchmark
    needs: `scripts/llm_encoder_backbone.py` pools a *layer* representation, so a
    model that only exposes a pooled vector (a `last_hidden_state` or a CLS
    embedding) cannot be a frozen encoder arm.

    Returns a JSON-serialisable dict; raises `HiddenStateUnsupported` (a
    `ValueError` carrying a machine-readable `reason`) when the contract fails.
    """
    if hidden_states is None:
        raise HiddenStateUnsupported("no_hidden_states: model returned None; "
                                     "output_hidden_states is not supported")
    try:
        hs = list(hidden_states)
    except TypeError:
        raise HiddenStateUnsupported(
            f"hidden_states_not_a_sequence: {type(hidden_states).__name__}")
    if len(hs) < expect_layers + 1:
        raise HiddenStateUnsupported(
            f"too_few_layers: {len(hs)} tensors for expect_layers={expect_layers} "
            f"(need {expect_layers + 1}: embeddings + {expect_layers} layers)")
    shapes = [list(getattr(t, "shape", ())) for t in hs]
    for i, shp in enumerate(shapes):
        if len(shp) != 3:
            raise HiddenStateUnsupported(
                f"not_3d: hidden_states[{i}].shape={shp}; expected "
                "(batch, seq, hidden)")
        if shp[0] != shapes[0][0] or shp[1] != shapes[0][1]:
            raise HiddenStateUnsupported(
                f"inconsistent_batch_or_seq: layer {i} shape {shp} vs "
                f"{shapes[0]}")
    # A pooled vector would be 2-D (or 1-D); a single repeated tensor would mean
    # the "layers" are aliases of one another. Both are disqualifying.
    identical = all(shapes[i] == shapes[0] for i in range(1, 1 + expect_layers))
    if not identical:
        raise HiddenStateUnsupported(f"shape_mismatch_across_layers: {shapes}")
    return {"available": True, "api": "output_hidden_states",
            "n_layers": len(hs) - 1, "n_layers_checked": int(expect_layers),
            "shape": shapes[0], "per_layer_shapes": shapes[: expect_layers + 1],
            "pooled_vector_only": False}


def describe_pooled_only(obj) -> dict:
    """Record the *reason* a model is only poolable (used for UNSUPPORTED notes)."""
    return {"available": False, "pooled_vector_only": True,
            "api": "pooler_output|last_hidden_state only",
            "observed_attributes": sorted(a for a in
                                          ("last_hidden_state", "pooler_output",
                                           "hidden_states")
                                          if hasattr(obj, a))}


class HiddenStateUnsupported(ValueError):
    """Raised when a model cannot emit per-layer hidden states."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def classify_failure(exc: BaseException) -> str:
    """Map an exception to a stable, greppable `reason` string for the manifest."""
    if isinstance(exc, HiddenStateUnsupported):
        return exc.reason
    name = type(exc).__name__
    text = str(exc).replace("\n", " ")[:300]
    low = text.lower()
    if "trust_remote_code" in low or "custom code" in low:
        return f"requires_trust_remote_code: {text}"
    if "architecture" in low or "recognized" in low or "unrecognized" in low:
        return f"architecture_not_supported: {text}"
    if "out of memory" in low or "cannot allocate" in low:
        return f"out_of_memory: {text}"
    if "connection" in low or "timeout" in low or "404" in low or "resolve" in low:
        return f"download_failed: {text}"
    if "gated" in low or "unauthorized" in low or "401" in low or "403" in low:
        return f"gated_or_unauthorized: {text}"
    return f"{name}: {text}"


# ──────────────────────────────────────────────────────────────────────────
# manifest: schema, parser, coverage
# ──────────────────────────────────────────────────────────────────────────
def empty_manifest(**meta) -> dict:
    """A fresh manifest skeleton (the worker appends one entry per arm)."""
    payload = {"schema": SCHEMA,
               "created_utc": datetime.now(timezone.utc).isoformat(),
               "hf_home": os.environ.get("HF_HOME"),
               "hf_hub_cache": os.environ.get("HF_HUB_CACHE"),
               "proxy": os.environ.get("HTTPS_PROXY"),
               "host": os.environ.get("SLURM_NODELIST") or os.uname().nodename
                       if hasattr(os, "uname") else os.environ.get("SLURM_NODELIST"),
               "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
               "entries": []}
    payload.update(meta)
    return payload


def load_manifest(path: str) -> dict:
    """Read a manifest, returning an empty one when the file does not exist yet."""
    if not os.path.exists(path):
        return empty_manifest()
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_manifest(path: str, manifest: dict) -> str:
    """Write the manifest atomically (a killed job must never truncate it)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    os.replace(tmp, path)
    return path


def upsert_entry(manifest: dict, entry: dict) -> dict:
    """Insert or replace the entry for `entry['model']` (resume-friendly)."""
    entries = [e for e in manifest.get("entries", [])
               if e.get("model") != entry.get("model")]
    entries.append(entry)
    manifest["entries"] = entries
    manifest["updated_utc"] = datetime.now(timezone.utc).isoformat()
    return manifest


_HEX40 = set("0123456789abcdef")


def is_pinned_revision(rev) -> bool:
    """True iff `rev` looks like a 40-character lowercase hex commit sha."""
    return isinstance(rev, str) and len(rev) == 40 and set(rev) <= _HEX40


def validate_manifest(manifest: dict) -> bool:
    """Assert the manifest schema. Raises `ValueError` on the first violation.

    Rules
    -----
    * `schema` present and equal to this module's `SCHEMA`;
    * `entries` is a list of dicts with `model`, `revision`, `size_bytes`,
      `config_sha256`, `status`;
    * `status` is one of `STATUSES`;
    * a non-`OK` entry carries a non-empty `reason` (an UNSUPPORTED arm without a
      reason is unactionable, so it is a schema error, not a warning);
    * an `OK` entry carries `hidden_state.available == True` and a pinned
      revision — an unpinned download is not reproducible;
    * `config_sha256` is a 64-character hex digest when present.
    """
    if not isinstance(manifest, dict):
        raise ValueError("manifest is not a JSON object")
    if int(manifest.get("schema", -1)) != SCHEMA:
        raise ValueError(f"manifest schema={manifest.get('schema')!r}, expected {SCHEMA}")
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ValueError("manifest has no `entries` list")
    seen = set()
    for i, e in enumerate(entries):
        where = f"entries[{i}]"
        if not isinstance(e, dict):
            raise ValueError(f"{where} is not an object")
        for key in ("model", "revision", "size_bytes", "status"):
            if key not in e:
                raise ValueError(f"{where} ({e.get('model')!r}) is missing `{key}`")
        model = e["model"]
        if model in seen:
            raise ValueError(f"duplicate entry for {model!r}")
        seen.add(model)
        if e["status"] not in STATUSES:
            raise ValueError(f"{where} ({model}) status={e['status']!r} not in "
                             f"{STATUSES}")
        if e["status"] == "OK":
            if not is_pinned_revision(e.get("revision")):
                raise ValueError(f"{where} ({model}) is OK but revision="
                                 f"{e.get('revision')!r} is not a pinned sha")
            hs = e.get("hidden_state") or {}
            if not hs.get("available"):
                raise ValueError(f"{where} ({model}) is OK but hidden_state."
                                 f"available is not true")
            cfg = e.get("config_sha256")
            if cfg is not None and (len(cfg) != 64 or set(cfg) - set("0123456789abcdef")):
                raise ValueError(f"{where} ({model}) config_sha256 is not a "
                                 f"64-char hex digest: {cfg!r}")
            try:
                if int(e["size_bytes"]) <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                raise ValueError(f"{where} ({model}) size_bytes must be a "
                                 f"positive integer, got {e['size_bytes']!r}")
        else:
            if not str(e.get("reason") or "").strip():
                raise ValueError(f"{where} ({model}) status={e['status']} but has "
                                 f"no `reason`")
    return True


def coverage(manifest: dict, registry: dict) -> dict:
    """Which required arms are fetched, which are missing, which are UNSUPPORTED.

    Returns `{"required": [...], "ok": [...], "unsupported": [...],
    "missing": [...], "failed": [...], "complete": bool}`.
    """
    req = [a["hf_id"] for a in required_arms(registry)]
    by_model = {}
    for e in manifest.get("entries", []):
        by_model[e.get("model")] = e
    ok, unsupported, failed, missing = [], [], [], []
    for model in req:
        e = by_model.get(model)
        if e is None or e.get("status") in (None, "PENDING"):
            missing.append(model)
        elif e.get("status") == "OK":
            ok.append(model)
        elif e.get("status") == "UNSUPPORTED":
            unsupported.append(model)
        else:
            failed.append(model)
    return {"required": req, "ok": ok, "unsupported": unsupported,
            "failed": failed, "missing": missing,
            "complete": not missing and not failed}


def compact_entry(*, model, revision, size_bytes, config_sha256, status,
                  reason=None, label=None, snapshot_path=None,
                  hidden_state=None, n_files=None, arch=None, params_b=None,
                  checked_utc=None, extra=None) -> dict:
    """Build one manifest entry with a stable key set."""
    return {"model": model, "label": label, "revision": revision,
            "revision_pinned": is_pinned_revision(revision),
            "size_bytes": int(size_bytes or 0), "n_files": n_files,
            "config_sha256": config_sha256, "snapshot_path": snapshot_path,
            "arch": arch, "params_b": params_b,
            "status": status, "reason": reason,
            "hidden_state": hidden_state,
            "checked_utc": checked_utc or datetime.now(timezone.utc).isoformat(),
            "extra": extra or {}}


def sha256_file(path: str) -> str:
    """SHA-256 of one file (the config digest in the manifest)."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_size(path: str) -> tuple:
    """`(total_bytes, n_files)` of a snapshot directory."""
    total = n = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            if os.path.islink(fp) and not os.path.exists(fp):
                continue
            total += os.path.getsize(fp)
            n += 1
    return total, n


# ──────────────────────────────────────────────────────────────────────────
# CLI (the bash worker calls `arms`, `check` and `coverage`)
# ──────────────────────────────────────────────────────────────────────────
def merge_manifests(manifests: list) -> dict:
    """Union several manifests into one (used when two download jobs run in parallel).

    Two jobs with **disjoint** model lists share the HF cache but must not share
    a manifest file (each would read-modify-write the other's edits). They write
    `weights_manifest_A.json` / `_B.json` instead and this function unions them:
    a terminal status (`OK`, `UNSUPPORTED`) beats `FAILED`, which beats
    `PENDING`, so the merged record never downgrades a banked arm.
    """
    rank = {"OK": 3, "UNSUPPORTED": 2, "FAILED": 1, "PENDING": 0}
    out = empty_manifest()
    out["sources"] = []
    for m in manifests:
        out["sources"].append({"manifest": m.get("source_path"),
                               "created_utc": m.get("created_utc"),
                               "entries": len(m.get("entries", []))})
        for e in m.get("entries", []):
            cur = next((x for x in out["entries"] if x.get("model") == e.get("model")),
                       None)
            if cur is None or rank.get(e.get("status"), 0) > rank.get(cur.get("status"), 0):
                out["entries"] = [x for x in out["entries"]
                                  if x.get("model") != e.get("model")] + [e]
    out["entries"].sort(key=lambda e: e.get("model") or "")
    out["updated_utc"] = datetime.now(timezone.utc).isoformat()
    return out


def _default_registry() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "queue", "arms_registry.json")


# ──────────────────────────────────────────────────────────────────────────
# download + probe (lazy imports: this module must import without HF installed)
# ──────────────────────────────────────────────────────────────────────────
def resolve_revision(model_id: str, wanted: str = None) -> tuple:
    """Return `(revision_sha, source)`. `source` is `registry` or `hf_api`.

    Pinning is mandatory (`docs/LLM_ARMS.md` §7.1 blocker B): a mutable branch
    name is not a reproducible provenance record, so `main` is never written.
    """
    if is_pinned_revision(wanted):
        return wanted, "registry"
    from huggingface_hub import HfApi          # lazy: not needed for the tests
    info = HfApi().model_info(model_id, revision=wanted or "main")
    sha = getattr(info, "sha", None) or info.__dict__.get("sha")
    if not is_pinned_revision(sha):
        raise ValueError(f"HF returned a non-sha revision for {model_id}: {sha!r}")
    return sha, "hf_api"


def download_arm(model_id: str, revision: str = None, allow_patterns=None) -> dict:
    """Snapshot-download one arm at a pinned revision into `HF_HUB_CACHE`.

    Returns `{revision, revision_source, snapshot_path, size_bytes, n_files,
    config_sha256, arch}`. Honours `HF_HOME` and `HF_HUB_CACHE` from the
    environment (the worker exports both), so nothing lands in `$HOME`.

    Resumable: `snapshot_download` reuses whatever is already in the cache and
    re-fetches only the missing blobs, and `resume_download=True` is requested
    where the installed `huggingface_hub` still accepts it (it was deprecated in
    0.23 and removed in 1.0, so the call is retried without it on TypeError — the
    behaviour is the same: downloads always resume).
    """
    from huggingface_hub import snapshot_download
    sha, source = resolve_revision(model_id, revision)
    kwargs = dict(repo_id=model_id, revision=sha, allow_patterns=allow_patterns,
                  max_workers=int(os.environ.get("HF_MAX_WORKERS", "4")))
    try:
        path = snapshot_download(resume_download=True, **kwargs)
    except TypeError:
        path = snapshot_download(**kwargs)
    size, n_files = dir_size(path)
    cfg = os.path.join(path, "config.json")
    arch = None
    try:
        with open(cfg, "r", encoding="utf-8") as fh:
            arch = (json.load(fh).get("architectures") or [None])[0]
    except OSError:
        pass
    return {"revision": sha, "revision_source": source, "snapshot_path": path,
            "size_bytes": size, "n_files": n_files,
            "config_sha256": sha256_file(cfg) if os.path.exists(cfg) else None,
            "arch": arch}


def probe_hidden_states(model_id: str, snapshot_path: str = None,
                        n_layers: int = 2, seed: int = 0,
                        with_checkpoint: bool = False,
                        max_params_b: float = 8.0, params_b: float = None) -> dict:
    """CPU probe: can this architecture emit per-layer hidden states?

    Cheap level (default): instantiate the class from its own `config.json` with
    `num_hidden_layers=n_layers` and random weights — no checkpoint is read, which
    is the only way to probe a 33 B arm on a CPU node. The question answered is
    exactly the one the benchmark needs: does the class expose `hidden_states`
    (per-layer) through the standard API, or only a pooled vector?

    With `with_checkpoint=True` (and a parameter count below `max_params_b`) the
    same probe is repeated on the real weights.
    """
    import torch
    from transformers import AutoConfig, AutoModel

    torch.manual_seed(int(seed))
    if snapshot_path:
        cfg = AutoConfig.from_pretrained(snapshot_path, trust_remote_code=False)
    else:
        cfg = AutoConfig.from_pretrained(model_id, trust_remote_code=False)
    cfg.num_hidden_layers = int(n_layers)
    # Head count must remain divisible by the layer's attention dimension.
    if getattr(cfg, "num_attention_heads", 0) and "hidden_size" in cfg.to_dict():
        if cfg.hidden_size % cfg.num_attention_heads != 0:
            cfg.num_attention_heads = 1
    model = AutoModel.from_config(cfg).eval()

    ids = torch.randint(1, 1000, (1, 8))
    with torch.no_grad():
        out = model(input_ids=ids, attention_mask=torch.ones_like(ids),
                    output_hidden_states=True)
    record = check_hidden_states(getattr(out, "hidden_states", None),
                                 expect_layers=int(n_layers))
    record["probe"] = "config_only"
    record["arch"] = cfg.architectures[0] if cfg.architectures else type(model).__name__
    record["n_params_random_init"] = int(sum(p.numel() for p in model.parameters()))

    if with_checkpoint:
        if params_b is not None and float(params_b) > float(max_params_b):
            record["checkpoint_probe"] = {
                "skipped": True,
                "reason": f"checkpoint_too_large_for_cpu: {params_b}B > "
                          f"max_params_b={max_params_b}B"}
        else:
            del model
            real = AutoModel.from_pretrained(snapshot_path or model_id,
                                             trust_remote_code=False).eval()
            real.config.num_hidden_layers = int(n_layers)
            with torch.no_grad():
                out2 = real(input_ids=ids, attention_mask=torch.ones_like(ids),
                            output_hidden_states=True)
            r2 = check_hidden_states(getattr(out2, "hidden_states", None),
                                     expect_layers=int(n_layers))
            record["checkpoint_probe"] = {"skipped": False, **r2}
    return record


def download_and_probe(model_id: str, *, manifest_path: str, label: str = None,
                       revision: str = None, probe: bool = True,
                       with_checkpoint: bool = False,
                       max_params_b: float = 8.0, params_b: float = None) -> dict:
    """One arm, end to end: download -> pin -> size/config hash -> probe -> manifest.

    Never raises for an unsupported model: the failure is recorded as
    `UNSUPPORTED` with its `reason` (that is the whole point of the manifest), and
    only a manifest-write failure is fatal.
    """
    manifest = load_manifest(manifest_path)
    entry = None
    try:
        info = download_arm(model_id, revision)
        hs = None
        status, reason = "OK", None
        if probe:
            try:
                hs = probe_hidden_states(model_id, info["snapshot_path"],
                                         with_checkpoint=with_checkpoint,
                                         max_params_b=max_params_b,
                                         params_b=params_b)
            except BaseException as exc:            # noqa: BLE001 - recorded, not raised
                status, reason = "UNSUPPORTED", classify_failure(exc)
                hs = {"available": False, "reason": reason}
        entry = compact_entry(
            model=model_id, label=label, revision=info["revision"],
            size_bytes=info["size_bytes"], config_sha256=info["config_sha256"],
            status=status, reason=reason, snapshot_path=info["snapshot_path"],
            hidden_state=hs, n_files=info["n_files"], arch=info["arch"],
            params_b=params_b,
            extra={"revision_source": info["revision_source"]})
    except BaseException as exc:                    # noqa: BLE001
        status = "FAILED" if not isinstance(exc, HiddenStateUnsupported) else "UNSUPPORTED"
        entry = compact_entry(model=model_id, label=label,
                              revision=revision or "", size_bytes=0,
                              config_sha256=None, status=status,
                              reason=classify_failure(exc), params_b=params_b)
    upsert_entry(manifest, entry)
    save_manifest(manifest_path, manifest)
    return entry



def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="LLM weights worker helper (CPU only).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_arms = sub.add_parser("arms", help="Print required arms as TSV.")
    p_arms.add_argument("--registry", default=_default_registry())
    p_arms.add_argument("--models", nargs="*", default=None,
                        help="Restrict to these hf ids (two parallel download jobs "
                             "get disjoint lists). Order still follows the "
                             "registry.")

    p_chk = sub.add_parser("check", help="Validate a weights manifest.")
    p_chk.add_argument("--manifest", required=True)

    p_cov = sub.add_parser("coverage", help="Compare a manifest to the registry.")
    p_cov.add_argument("--manifest", required=True)
    p_cov.add_argument("--registry", default=_default_registry())
    p_cov.add_argument("--strict", action="store_true",
                       help="Exit 1 unless every required arm is terminal "
                            "(OK or UNSUPPORTED).")

    p_shs = sub.add_parser("check-hidden-states",
                           help="Validate a hidden-state probe record from JSON.")
    p_shs.add_argument("--json", required=True,
                       help="File holding the probe record (all fields of the "
                            "`hidden_state` block).")

    p_pin = sub.add_parser("pin", help="Print the registry's revision for an arm.")
    p_pin.add_argument("--model", required=True)
    p_pin.add_argument("--registry", default=_default_registry())

    p_dl = sub.add_parser("download",
                          help="Download ONE arm, pin its revision, probe hidden "
                               "states, and record it in the manifest.")
    p_dl.add_argument("--model", required=True)
    p_dl.add_argument("--label", default=None)
    p_dl.add_argument("--revision", default=None,
                      help="Pinned sha from the registry; empty = resolve via the "
                           "HF API and pin the returned sha.")
    p_dl.add_argument("--manifest", required=True)
    p_dl.add_argument("--params-b", type=float, default=None)
    p_dl.add_argument("--no-probe", action="store_true")
    p_dl.add_argument("--probe-checkpoint", action="store_true",
                      help="Also probe the real checkpoint (only under "
                           "--max-params-b).")
    p_dl.add_argument("--max-params-b", type=float, default=8.0)

    p_merge = sub.add_parser("merge", help="Union several per-job manifests.")
    p_merge.add_argument("--manifest", nargs="+", required=True)
    p_merge.add_argument("--out", required=True)

    p_pr = sub.add_parser("probe", help="Hidden-state probe for one cached model "
                                        "(no download).")
    p_pr.add_argument("--model", required=True)
    p_pr.add_argument("--snapshot-path", default=None)
    p_pr.add_argument("--layers", type=int, default=2)
    p_pr.add_argument("--json-out", default=None)

    a = ap.parse_args(argv)
    if a.cmd == "arms":
        reg = read_registry(a.registry)
        wanted = set(a.models or [])
        for arm in required_arms(reg):
            if wanted and arm["hf_id"] not in wanted:
                continue
            # 5 columns: hf_id, label, revision, venv, params_b (the worker's bash
            # side sorts ascending on the last one so small arms are banked first)
            print("\t".join([arm["hf_id"], arm["label"], str(arm["revision"]),
                             str(arm["venv"]),
                             "" if arm.get("params_b") is None
                             else str(arm["params_b"])]))
        if wanted:
            missing = wanted - {arm["hf_id"] for arm in required_arms(reg)}
            if missing:
                print("# WARNING: not required arms: %s" % ", ".join(sorted(missing)),
                      file=sys.stderr)
        return 0
    if a.cmd == "merge":
        loaded = []
        for path in a.manifest:
            m = load_manifest(path)
            m["source_path"] = path
            validate_manifest(m)
            loaded.append(m)
        merged = merge_manifests(loaded)
        validate_manifest(merged)
        save_manifest(a.out, merged)
        cov = coverage(merged, read_registry(_default_registry())) \
            if os.path.exists(_default_registry()) else None
        print("merged %d manifests -> %s (%d entries)"
              % (len(loaded), a.out, len(merged["entries"])))
        if cov:
            print("coverage: ok=%d unsupported=%d failed=%d missing=%d complete=%s"
                  % (len(cov["ok"]), len(cov["unsupported"]), len(cov["failed"]),
                     len(cov["missing"]), cov["complete"]))
        return 0
    if a.cmd == "check":
        validate_manifest(load_manifest(a.manifest))
        print("manifest OK: %s" % a.manifest)
        return 0
    if a.cmd == "coverage":
        cov = coverage(load_manifest(a.manifest), read_registry(a.registry))
        print("required=%d ok=%d unsupported=%d failed=%d missing=%d"
              % (len(cov["required"]), len(cov["ok"]), len(cov["unsupported"]),
                 len(cov["failed"]), len(cov["missing"])))
        for tag in ("missing", "failed", "unsupported"):
            for model in cov[tag]:
                print("  %-10s %s" % (tag.upper(), model))
        print("complete=%s" % cov["complete"])
        if a.strict and not cov["complete"]:
            return 1
        return 0
    if a.cmd == "check-hidden-states":
        with open(a.json, "r", encoding="utf-8") as fh:
            rec = json.load(fh)
        if isinstance(rec, dict) and "hidden_states" in rec and \
                isinstance(rec["hidden_states"], list):
            # shapes-only record: re-validate it structurally
            class _T:
                def __init__(self, shape):
                    self.shape = tuple(shape)
            try:
                check_hidden_states([_T(s) for s in rec["hidden_states"]],
                                    int(rec.get("expect_layers", 2)))
            except HiddenStateUnsupported as exc:
                print("UNSUPPORTED: %s" % exc.reason)
                return 1
        elif isinstance(rec, dict):
            if not rec.get("available"):
                print("UNSUPPORTED: hidden states not available: %s"
                      % rec.get("reason", "no reason given"))
                return 1
            if rec.get("pooled_vector_only"):
                print("UNSUPPORTED: pooled vector only")
                return 1
            shapes = rec.get("per_layer_shapes") or []
            for shp in shapes:
                if len(shp) != 3:
                    print("UNSUPPORTED: hidden state is not 3-D: %s" % (shp,))
                    return 1
        else:
            print("probe record must be a JSON object")
            return 2
        print("hidden-state probe OK")
        return 0
    if a.cmd == "pin":
        reg = read_registry(a.registry)
        for arm in required_arms(reg):
            if arm["hf_id"] == a.model:
                print(arm["revision"] or "")
                return 0
        raise SystemExit(f"{a.model} is not a required arm")
    if a.cmd == "download":
        entry = download_and_probe(
            a.model, manifest_path=a.manifest, label=a.label,
            revision=a.revision, probe=not a.no_probe,
            with_checkpoint=a.probe_checkpoint, max_params_b=a.max_params_b,
            params_b=a.params_b)
        print("STATUS=%s MODEL=%s REVISION=%s SIZE=%d REASON=%s"
              % (entry["status"], entry["model"], entry["revision"],
                 entry["size_bytes"], entry["reason"] or "-"))
        return 0 if entry["status"] in ("OK", "UNSUPPORTED") else 1
    if a.cmd == "probe":
        try:
            rec = probe_hidden_states(a.model, a.snapshot_path, a.layers)
        except BaseException as exc:               # noqa: BLE001
            rec = {"available": False, "reason": classify_failure(exc)}
            print("UNSUPPORTED: %s" % rec["reason"])
            if a.json_out:
                with open(a.json_out, "w", encoding="utf-8") as fh:
                    json.dump(rec, fh, indent=2)
            return 1
        print(json.dumps(rec, indent=2))
        if a.json_out:
            with open(a.json_out, "w", encoding="utf-8") as fh:
                json.dump(rec, fh, indent=2)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
