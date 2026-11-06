"""Checkpoint manifest: SHA-256 present and the restore test round-trips."""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

import torch  # noqa: E402
import torch.nn as nn  # noqa: E402

from innovation import run_artifacts as ART  # noqa: E402


class _Tiny(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(4, 2)

    def forward(self, x):
        return self.fc(x)


def test_manifest_and_restore():
    import json

    tmp = tempfile.mkdtemp(prefix="innov_ckpt_")
    run_dir = os.path.join(tmp, "run")
    os.makedirs(os.path.join(run_dir, "checkpoints"))
    ckpt = os.path.join(run_dir, "checkpoints", "best_val_mse.pt")

    torch.manual_seed(0)
    m = _Tiny()
    torch.save(m.state_dict(), ckpt)

    man = ART.write_checkpoint_manifest(run_dir, ckpt_path=ckpt, best_epoch=3,
                                        best_val_mse=1.234,
                                        config={"model": "tiny"})
    assert man["sha256_file"] and man["state_dict_sha256"]
    assert man["best_epoch"] == 3 and abs(man["best_val_mse"] - 1.234) < 1e-9
    # manifest actually on disk and JSON-valid
    with open(os.path.join(run_dir, "checkpoints", "checkpoint_manifest.json"),
              encoding="utf-8") as f:
        assert json.load(f)["state_dict_sha256"] == man["state_dict_sha256"]

    res = ART.restore_test(lambda: _Tiny(), ckpt,
                           expected_state_dict_sha256=man["state_dict_sha256"])
    assert res["ok"] is True, res
    assert not res["missing_keys"] and not res["unexpected_keys"], res


if __name__ == "__main__":
    test_manifest_and_restore()
    print("[test_checkpoint_resume] OK")
