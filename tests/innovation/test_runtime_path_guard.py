"""
Runtime path guard tests (innov-v2.3)
=====================================

No innovation job may resolve a Python source path under the original
reproduction repository. The check must use RESOLVED paths, not a raw string
prefix comparison.
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation import runtime_guard as RG  # noqa: E402
from innovation.paths import BANNED_RUNTIME_ROOT  # noqa: E402


def test_banned_root_is_declared():
    assert BANNED_RUNTIME_ROOT == "/home/sychan552/scratch/CHATTIME/Chattime"


def test_a_banned_path_is_detected():
    assert RG.is_banned("/home/sychan552/scratch/CHATTIME/Chattime") is True
    assert RG.is_banned("/home/sychan552/scratch/CHATTIME/Chattime/scripts/x.py") is True
    assert RG.is_banned("/home/sychan552/scratch/CHATTIME/Chattime/") is True


def test_a_clean_deployment_root_is_not_flagged():
    assert RG.is_banned(
        "/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/"
        "innov-v2.3_deadbeef") is False


def test_resolution_collapses_dotdot_and_symlinks():
    tmp = tempfile.mkdtemp(prefix="innov_guard_")
    deep = os.path.join(tmp, "a", "b")
    os.makedirs(deep, exist_ok=True)
    assert RG.resolved(os.path.join(deep, "..", "b")) == RG.resolved(deep)
    assert RG.resolved(os.path.join(deep, "..", "..", "a")) == \
        RG.resolved(os.path.join(tmp, "a"))


def test_dotdot_into_a_banned_marker_is_caught():
    """A path that only *reaches* the banned directory via '..' must still be
    caught after resolution."""
    old = RG.BANNED_RUNTIME_MARKERS
    try:
        tmp = tempfile.mkdtemp(prefix="innov_guard_banned_")
        banned = os.path.join(tmp, "CHATTIME", "Chattime")
        os.makedirs(os.path.join(banned, "scripts"), exist_ok=True)
        RG.BANNED_RUNTIME_MARKERS = tuple(old) + ("CHATTIME/Chattime",)
        sneaky = os.path.join(banned, "scripts", "..", "scripts")
        assert RG.is_banned(sneaky) is True
        assert RG.is_banned(os.path.join(banned, "scripts", "x.py")) is True
    finally:
        RG.BANNED_RUNTIME_MARKERS = old


def test_check_is_clean_for_the_current_interpreter():
    res = RG.check(deployment_root=os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(_bootstrap.__file__)))))
    assert res["ok"] is True, res["violations"]
    assert res["failure_code"] is None


def test_assert_clean_raises_the_declared_code():
    old = RG.BANNED_RUNTIME_MARKERS
    try:
        RG.BANNED_RUNTIME_MARKERS = tuple(old) + ("__innov_forbidden__",)
        root = os.path.join(tempfile.mkdtemp(prefix="innov_guard_x_"),
                            "__innov_forbidden__")
        os.makedirs(root, exist_ok=True)
        try:
            RG.assert_clean(deployment_root=root)
        except RuntimeError as e:
            assert RG.FAILURE_CODE in str(e), e
        else:
            raise AssertionError("assert_clean must raise on a banned root")
    finally:
        RG.BANNED_RUNTIME_MARKERS = old


def test_check_reports_violations_not_silence():
    old = RG.BANNED_RUNTIME_MARKERS
    try:
        RG.BANNED_RUNTIME_MARKERS = tuple(old) + ("__innov_forbidden__",)
        root = os.path.join(tempfile.mkdtemp(prefix="innov_guard_y_"),
                            "__innov_forbidden__")
        os.makedirs(root, exist_ok=True)
        res = RG.check(deployment_root=root)
        assert res["ok"] is False
        assert res["failure_code"] == RG.FAILURE_CODE
        assert res["violations"], "violations must be listed"
    finally:
        RG.BANNED_RUNTIME_MARKERS = old


if __name__ == "__main__":
    test_banned_root_is_declared()
    test_a_banned_path_is_detected()
    test_a_clean_deployment_root_is_not_flagged()
    test_resolution_collapses_dotdot_and_symlinks()
    test_dotdot_into_a_banned_marker_is_caught()
    test_check_is_clean_for_the_current_interpreter()
    test_assert_clean_raises_the_declared_code()
    test_check_reports_violations_not_silence()
    print("[test_runtime_path_guard] OK")
