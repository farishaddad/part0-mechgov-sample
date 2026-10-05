from mechgov import hard_gates

BASE = {"case_id": "C1", "risk_score": 0.3, "regulatory_flags": [], "exposure_amount": 120000}


def case(**kw):
    return {**BASE, **kw}


def test_pass():
    assert hard_gates.evaluate(case())["outcome"] == "PASS"


def test_flag_and_block_thresholds():
    assert hard_gates.evaluate(case(risk_score=0.7))["outcome"] == "FLAG"
    assert hard_gates.evaluate(case(risk_score=0.81))["outcome"] == "BLOCK"
    assert hard_gates.evaluate(case(risk_score=0.8))["outcome"] == "FLAG"  # boundary: > not >=


def test_regulatory_flag_blocks_even_with_low_risk():
    out = hard_gates.evaluate(case(risk_score=0.1, regulatory_flags=["SANCTIONS_HIT"]))
    assert out["outcome"] == "BLOCK"


def test_missing_field_defers():
    out = hard_gates.evaluate({k: v for k, v in BASE.items() if k != "risk_score"})
    assert out["outcome"] == "DEFER"


def test_bad_score_defers():
    assert hard_gates.evaluate(case(risk_score=1.7))["outcome"] == "DEFER"


def test_mask_pii():
    masked = hard_gates.mask_pii(case(full_name="Jane Doe", note="acct 12345678 paid"))
    assert "full_name" not in masked
    assert "12345678" not in masked["note"]
