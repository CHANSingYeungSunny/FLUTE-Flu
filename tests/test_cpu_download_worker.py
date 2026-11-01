"""test_cpu_download_worker.py — the weights fetcher's manifest contract (CPU only).

No network and no model download: everything here is the manifest schema, the
arm selection, the coverage report and the hidden-state probe contract, which is
what `hpc_experiments/cpu_download_worker.sh` relies on to decide what is
`OK`, what is `UNSUPPORTED` (with a reason) and what it must try again.

What is tested
--------------
1. **Arm selection** — exactly the 10 `tencent/*` arms plus
   `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B`, in a deterministic order.
2. **Revision pinning** — a branch name (`main`) is not a pinned revision; a
   40-char lowercase sha is.
3. **Manifest schema** — an `OK` entry needs a pinned sha, a positive size and a
   hidden-state record; a non-`OK` entry needs a reason; duplicates and unknown
   statuses are rejected.
4. **Parser/resume** — `upsert_entry` replaces rather than duplicates, and
   `save_manifest` is atomic (no `.tmp` left behind).
5. **Coverage** — missing vs OK vs UNSUPPORTED vs FAILED, and `complete` is only
   true when nothing is missing or failed.
6. **Hidden-state contract** — 3-D per-layer states pass; a pooled 2-D vector, a
   `None`, and a layer-count shortfall each fail with a machine-readable reason;
   `classify_failure` maps the usual exceptions to greppable reasons.
7. **Import hygiene** — importing the worker must not import
   `huggingface_hub`/`transformers`, so `--check`/`coverage` work on a node (or a
   laptop) without them.

Run:  python -m pytest -q tests/test_cpu_download_worker.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HPC = os.path.join(PROJECT_ROOT, "hpc_experiments")
for _p in (HPC, PROJECT_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import weights_worker as ww                      # noqa: E402

REGISTRY = os.path.join(HPC, "queue", "arms_registry.json")
SHA = "0123456789abcdef0123456789abcdef01234567"
CFG_SHA = "f" * 64


class _T:
    """Stand-in for a torch tensor: the probe only reads `.shape`."""

    def __init__(self, shape):
        self.shape = tuple(shape)


def _ok_entry(model="tencent/Penguin-Encoder", **kw):
    base = dict(model=model, revision=SHA, size_bytes=1234,
                config_sha256=CFG_SHA, status="OK",
                hidden_state={"available": True, "n_layers": 2,
                              "shape": [1, 8, 16]})
    base.update(kw)
    return ww.compact_entry(**base)


# ── 1. arm selection ───────────────────────────────────────────────────────
def test_required_arms_are_the_ten_tencent_models_plus_deepseek_32b():
    reg = ww.read_registry(REGISTRY)
    arms = ww.required_arms(reg)
    ids = [a["hf_id"] for a in arms]
    tencent = [i for i in ids if i.startswith("tencent/")]
    assert len(tencent) == 10, tencent
    assert "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B" in ids
    assert len(ids) == 11
    # deterministic order (registry order, then the extra model)
    assert ids == [a["hf_id"] for a in ww.required_arms(reg)]
    assert arms[0]["hf_id"] == tencent[0]


def test_required_arms_survive_a_registry_without_the_deepseek_entry():
    reg = {"arms": [{"hf_id": "tencent/Penguin-Encoder", "label": "p",
                     "revision": SHA}]}
    ids = [a["hf_id"] for a in ww.required_arms(reg)]
    assert ids == ["tencent/Penguin-Encoder",
                   "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"]


# ── 2. revision pinning ────────────────────────────────────────────────────
@pytest.mark.parametrize("rev,ok", [
    (SHA, True), ("a" * 40, True), ("main", False), ("", False), (None, False),
    ("A" * 40, False), ("abc123", False), (SHA + "0", False),
])
def test_is_pinned_revision(rev, ok):
    assert ww.is_pinned_revision(rev) is ok


# ── 3. manifest schema ─────────────────────────────────────────────────────
def test_valid_manifest_passes():
    m = ww.empty_manifest()
    ww.upsert_entry(m, _ok_entry())
    assert ww.validate_manifest(m) is True


def test_ok_entry_requires_a_pinned_revision():
    m = ww.empty_manifest()
    ww.upsert_entry(m, _ok_entry(revision="main"))
    with pytest.raises(ValueError, match="not a pinned sha"):
        ww.validate_manifest(m)


def test_ok_entry_requires_a_hidden_state_record():
    m = ww.empty_manifest()
    e = ww.compact_entry(model="tencent/WeMM-Embedding-2B", revision=SHA,
                         size_bytes=10, config_sha256=CFG_SHA, status="OK")
    ww.upsert_entry(m, e)
    with pytest.raises(ValueError, match="hidden_state"):
        ww.validate_manifest(m)


def test_ok_entry_requires_a_positive_size():
    m = ww.empty_manifest()
    ww.upsert_entry(m, _ok_entry(size_bytes=0))
    with pytest.raises(ValueError, match="size_bytes"):
        ww.validate_manifest(m)


def test_unsupported_entry_requires_a_reason():
    m = ww.empty_manifest()
    ww.upsert_entry(m, ww.compact_entry(model="tencent/Youtu-HiChunk",
                                        revision=SHA, size_bytes=0,
                                        config_sha256=None,
                                        status="UNSUPPORTED"))
    with pytest.raises(ValueError, match="no `reason`"):
        ww.validate_manifest(m)
    ww.upsert_entry(m, ww.compact_entry(model="tencent/Youtu-HiChunk",
                                        revision=SHA, size_bytes=0,
                                        config_sha256=None,
                                        status="UNSUPPORTED",
                                        reason="architecture_not_supported: x"))
    assert ww.validate_manifest(m) is True


def test_unknown_status_and_duplicates_are_rejected():
    m = ww.empty_manifest()
    ww.upsert_entry(m, _ok_entry())
    m["entries"].append(dict(m["entries"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        ww.validate_manifest(m)
    m2 = ww.empty_manifest()
    ww.upsert_entry(m2, _ok_entry(status="MAYBE"))
    with pytest.raises(ValueError, match="status"):
        ww.validate_manifest(m2)


def test_wrong_schema_version_is_rejected():
    m = ww.empty_manifest()
    m["schema"] = 99
    with pytest.raises(ValueError, match="schema"):
        ww.validate_manifest(m)


# ── 4. parser / resume ─────────────────────────────────────────────────────
def test_upsert_replaces_and_save_is_atomic(tmp_path):
    path = str(tmp_path / "weights_manifest.json")
    m = ww.load_manifest(path)
    assert m["entries"] == []
    ww.upsert_entry(m, _ok_entry())
    ww.upsert_entry(m, _ok_entry(status="UNSUPPORTED", reason="later decision",
                                 size_bytes=0, config_sha256=None,
                                 hidden_state={"available": False}))
    ww.save_manifest(path, m)
    back = ww.load_manifest(path)
    assert len(back["entries"]) == 1
    assert back["entries"][0]["status"] == "UNSUPPORTED"
    assert not os.path.exists(path + ".tmp")
    assert back["updated_utc"]


def test_entry_records_the_four_required_fields():
    e = _ok_entry()
    for key in ("model", "revision", "size_bytes", "config_sha256", "status"):
        assert key in e
    assert e["revision_pinned"] is True
    assert len(e["config_sha256"]) == 64


# ── 5. coverage ────────────────────────────────────────────────────────────
def test_coverage_classifies_every_arm():
    reg = ww.read_registry(REGISTRY)
    req = [a["hf_id"] for a in ww.required_arms(reg)]
    m = ww.empty_manifest()
    ww.upsert_entry(m, _ok_entry(model=req[0]))
    ww.upsert_entry(m, ww.compact_entry(model=req[1], revision=SHA, size_bytes=0,
                                        config_sha256=None, status="UNSUPPORTED",
                                        reason="pooled_vector_only"))
    ww.upsert_entry(m, ww.compact_entry(model=req[2], revision=SHA, size_bytes=0,
                                        config_sha256=None, status="FAILED",
                                        reason="download_failed: 403"))
    cov = ww.coverage(m, reg)
    assert cov["ok"] == [req[0]]
    assert cov["unsupported"] == [req[1]]
    assert cov["failed"] == [req[2]]
    assert len(cov["missing"]) == len(req) - 3
    assert cov["complete"] is False


def test_coverage_is_complete_when_every_arm_is_terminal():
    reg = ww.read_registry(REGISTRY)
    req = [a["hf_id"] for a in ww.required_arms(reg)]
    m = ww.empty_manifest()
    for i, model in enumerate(req):
        if i % 2 == 0:
            ww.upsert_entry(m, _ok_entry(model=model))
        else:
            ww.upsert_entry(m, ww.compact_entry(
                model=model, revision=SHA, size_bytes=0, config_sha256=None,
                status="UNSUPPORTED", reason="pooled_vector_only"))
    cov = ww.coverage(m, reg)
    assert cov["complete"] is True
    assert not cov["missing"] and not cov["failed"]
    assert ww.validate_manifest(m) is True


# ── 6. hidden-state contract ───────────────────────────────────────────────
def test_hidden_states_3d_per_layer_pass():
    rec = ww.check_hidden_states([_T((1, 8, 16)), _T((1, 8, 16)), _T((1, 8, 16))],
                                 expect_layers=2)
    assert rec["available"] is True and rec["n_layers"] == 2
    assert rec["n_layers_checked"] == 2
    assert rec["pooled_vector_only"] is False
    assert rec["shape"] == [1, 8, 16]


def test_pooled_vector_and_none_are_unsupported_with_reasons():
    with pytest.raises(ww.HiddenStateUnsupported) as ei:
        ww.check_hidden_states(None, expect_layers=2)
    assert ei.value.reason.startswith("no_hidden_states")
    with pytest.raises(ww.HiddenStateUnsupported) as ei:
        ww.check_hidden_states([_T((1, 16))], expect_layers=2)
    assert ei.value.reason.startswith("too_few_layers")
    with pytest.raises(ww.HiddenStateUnsupported) as ei:
        ww.check_hidden_states([_T((1, 8, 16)), _T((1, 16)), _T((1, 16))],
                              expect_layers=2)
    assert ei.value.reason.startswith("not_3d")


def test_classify_failure_is_greppable():
    assert ww.classify_failure(ww.HiddenStateUnsupported("no_hidden_states: x")) \
        == "no_hidden_states: x"
    assert ww.classify_failure(RuntimeError("requires trust_remote_code=True")) \
        .startswith("requires_trust_remote_code")
    assert ww.classify_failure(KeyError("Unrecognized architecture Foo")) \
        .startswith("architecture_not_supported")
    assert ww.classify_failure(OSError("Connection timed out")) \
        .startswith("download_failed")
    assert ww.classify_failure(MemoryError("CUDA out of memory")) \
        .startswith("out_of_memory")


# ── 7. CLI + import hygiene ────────────────────────────────────────────────
def test_cli_check_and_coverage(tmp_path, capsys):
    path = str(tmp_path / "weights_manifest.json")
    m = ww.empty_manifest()
    ww.upsert_entry(m, _ok_entry())
    ww.save_manifest(path, m)
    assert ww.main(["check", "--manifest", path]) == 0
    assert "manifest OK" in capsys.readouterr().out
    rc = ww.main(["coverage", "--manifest", path, "--registry", REGISTRY])
    out = capsys.readouterr().out
    assert rc == 0 and "required=11" in out and "missing=10" in out


def test_cli_arms_lists_eleven_lines(capsys):
    assert ww.main(["arms", "--registry", REGISTRY]) == 0
    lines = [l for l in capsys.readouterr().out.splitlines() if l.strip()]
    assert len(lines) == 11
    assert lines[0].split("\t")[0].startswith("tencent/")
    assert lines[0].split("\t")[4] == "0.4"       # params_b drives the sort


def test_cli_arms_can_be_sliced_for_two_parallel_jobs(capsys):
    """Two download jobs must be able to take disjoint model lists."""
    job_a = ["tencent/Penguin-Encoder", "tencent/Hunyuan-1.8B-Instruct",
             "tencent/WeMM-Embedding-2B", "tencent/Youtu-HiChunk",
             "tencent/Hunyuan-4B-Instruct", "tencent/WeMM-Embedding-4B"]
    job_b = ["tencent/ContextPilot-8B", "tencent/Hunyuan-7B-Instruct",
             "tencent/KaLM-Embedding-Gemma3-12B", "tencent/ContextPilot-14B",
             "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"]
    assert not set(job_a) & set(job_b)
    assert len(job_a) + len(job_b) == 11
    for group, n in ((job_a, 6), (job_b, 5)):
        assert ww.main(["arms", "--registry", REGISTRY, "--models"] + group) == 0
        lines = [l for l in capsys.readouterr().out.splitlines() if l.strip()]
        assert len(lines) == n
        assert [l.split("\t")[0] for l in lines] == group   # registry order kept


def test_merge_unions_two_parallel_manifests(tmp_path):
    reg = ww.read_registry(REGISTRY)
    req = [a["hf_id"] for a in ww.required_arms(reg)]
    a, b = ww.empty_manifest(), ww.empty_manifest()
    ww.upsert_entry(a, _ok_entry(model=req[0]))
    ww.upsert_entry(b, ww.compact_entry(model=req[1], revision=SHA, size_bytes=0,
                                        config_sha256=None, status="UNSUPPORTED",
                                        reason="pooled_vector_only"))
    pa, pb = str(tmp_path / "A.json"), str(tmp_path / "B.json")
    ww.save_manifest(pa, a)
    ww.save_manifest(pb, b)
    merged = ww.merge_manifests([ww.load_manifest(pa), ww.load_manifest(pb)])
    assert len(merged["entries"]) == 2
    assert ww.validate_manifest(merged) is True
    out = str(tmp_path / "merged.json")
    assert ww.main(["merge", "--manifest", pa, pb, "--out", out]) == 0
    assert len(ww.load_manifest(out)["entries"]) == 2


def test_merge_never_downgrades_a_banked_arm():
    a = ww.empty_manifest()
    ww.upsert_entry(a, _ok_entry())
    b = ww.empty_manifest()
    ww.upsert_entry(b, ww.compact_entry(model="tencent/Penguin-Encoder",
                                        revision="", size_bytes=0,
                                        config_sha256=None, status="PENDING"))
    merged = ww.merge_manifests([a, b])
    assert merged["entries"][0]["status"] == "OK"


def test_cli_check_hidden_states_rejects_a_pooled_record(tmp_path):
    p = tmp_path / "probe.json"
    p.write_text(json.dumps({"available": False,
                             "reason": "pooled_vector_only"}), encoding="utf-8")
    assert ww.main(["check-hidden-states", "--json", str(p)]) != 0
    p2 = tmp_path / "probe_ok.json"
    p2.write_text(json.dumps({"available": True, "n_layers": 2,
                              "per_layer_shapes": [[1, 8, 16]] * 3}),
                  encoding="utf-8")
    assert ww.main(["check-hidden-states", "--json", str(p2)]) == 0


def test_importing_the_worker_does_not_import_heavy_libraries():
    code = ("import sys; sys.path.insert(0, %r); import weights_worker; "
            "print('huggingface_hub' in sys.modules, 'transformers' in sys.modules)"
            % HPC)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                         text=True, cwd=PROJECT_ROOT)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "False False", out.stdout


def test_the_bash_worker_has_no_gres_line_and_a_sane_memory_request():
    sh = os.path.join(HPC, "cpu_download_worker.sh")
    text = open(sh, encoding="utf-8").read()
    assert text.startswith("#!/bin/bash")
    header = [l for l in text.splitlines() if l.startswith("#SBATCH")]
    assert not any("--gres" in l for l in header), header
    cpus = [l for l in header if l.startswith("#SBATCH --cpus-per-task")][0]
    mem = [l for l in header if l.startswith("#SBATCH --mem")][0]
    n_cpu = int(cpus.split("=")[1])
    n_mem = int(mem.split("=")[1].rstrip("M"))
    assert n_mem <= n_cpu * 1024, (n_mem, n_cpu)
    assert any(l.startswith("#SBATCH --time") for l in header)
    # both caches must be redirected to scratch, and both names must appear
    assert "HF_HOME" in text and "HF_HUB_CACHE" in text
    assert "scontrol requeue" in text
    assert "HTTPS_PROXY" in text
    assert "SLURM_JOB_ID" in text and "REFUSING" in text


if __name__ == "__main__":       # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
