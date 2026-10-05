import json

import pytest

from fakes import FakeBedrock, FakeS3
from mechgov import commit, reveal

CANDS = ["APPROVE", "DECLINE", "REFER"]


def _commit(s3, decision="APPROVE"):
    result = commit.initial_decision(FakeBedrock(decision), "m", {"dti": 0.22}, CANDS, "BR-001")
    return commit.entropy_commit(s3, "b", 1, "m", "C1", result)


def test_commit_uses_compliance_lock_and_hides_decision():
    s3 = FakeS3()
    out = _commit(s3)
    put = s3.puts[0]
    assert put["ObjectLockMode"] == "COMPLIANCE"
    assert put["ChecksumAlgorithm"] == "SHA256"
    assert "decision" not in json.loads(put["Body"])  # only the hash is public before reveal
    assert commit.sha256_hex(out["payload"]) == out["commit_hash"]


def test_off_list_decision_rejected_before_any_write():
    s3 = FakeS3()
    with pytest.raises(ValueError):
        commit.initial_decision(FakeBedrock("MAYBE"), "m", {}, CANDS, "p")
    assert s3.puts == []


def test_reveal_detects_flip():
    s3 = FakeS3()
    c = _commit(s3, "APPROVE")
    rec = reveal.reveal(s3, "b", 1, c["commit_key"], c["payload"], "DECLINE")
    assert rec["flipped"] is True and rec["initial_decision"] == "APPROVE"


def test_reveal_rejects_tampered_payload():
    s3 = FakeS3()
    c = _commit(s3, "APPROVE")
    tampered = c["payload"].replace("APPROVE", "DECLINE")
    with pytest.raises(ValueError):
        reveal.reveal(s3, "b", 1, c["commit_key"], tampered, "DECLINE")
