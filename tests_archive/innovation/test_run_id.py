"""run_id: format, round-trip, uniqueness, and malformed-input rejection."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

from innovation.run_id import make_run_id, parse_run_id, slug  # noqa: E402


def test_round_trip():
    rid = make_run_id("national_ili", "dlinear", "none", "identity", 24, 42,
                      timestamp="20260101T000000Z", gitsha="deadbee")
    # components are slugged (non-alphanumeric -> "-") so "__" stays unambiguous
    assert rid == ("national-ili__dlinear__none__identity__L24__seed42__"
                   "20260101T000000Z__deadbee"), rid
    m = parse_run_id(rid)
    assert m["horizon"] == 24 and m["seed"] == 42 and m["model"] == "dlinear"
    assert m["dataset"] == "national-ili"
    assert m["text_encoder"] == "none" and m["fusion"] == "identity"
    assert m["gitsha"] == "deadbee"


def test_slug_and_unique():
    assert slug("cross_attention") == "cross-attention"
    a = make_run_id("d", "m", "e", "f", 24, 42, timestamp="T1", gitsha="g")
    b = make_run_id("d", "m", "e", "f", 24, 42, timestamp="T2", gitsha="g")
    assert a != b, "timestamps must make run ids unique"


def test_malformed_rejected():
    try:
        parse_run_id("too__few__fields")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


if __name__ == "__main__":
    test_round_trip()
    test_slug_and_unique()
    test_malformed_rejected()
    print("[test_run_id] OK")
