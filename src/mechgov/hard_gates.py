"""Deterministic pre-LLM gates. No model involved; same input always gives the same outcome."""
import re

BLOCK_RISK = 0.8
FLAG_RISK = 0.6
BLOCKING_FLAGS = {"KYC_FAIL", "AML_ALERT", "PEP", "SANCTIONS_HIT"}
REQUIRED_FIELDS = ("case_id", "risk_score", "regulatory_flags", "exposure_amount")
_PII_KEYS = {"name", "full_name", "email", "phone", "address", "ni_number", "date_of_birth", "account_number", "sort_code"}


def evaluate(case: dict) -> dict:
    """Return {"outcome": PASS|FLAG|DEFER|BLOCK, "reasons": [...]}."""
    missing = [f for f in REQUIRED_FIELDS if case.get(f) is None]
    if missing:
        return {"outcome": "DEFER", "reasons": [f"missing required field: {m}" for m in missing]}

    hits = sorted(BLOCKING_FLAGS & set(case["regulatory_flags"]))
    if hits:
        return {"outcome": "BLOCK", "reasons": [f"regulatory flag: {h}" for h in hits]}

    score = float(case["risk_score"])
    if not 0.0 <= score <= 1.0:
        return {"outcome": "DEFER", "reasons": [f"risk_score out of range: {score}"]}
    if score > BLOCK_RISK:
        return {"outcome": "BLOCK", "reasons": [f"risk_score {score} > {BLOCK_RISK}"]}
    if score > FLAG_RISK:
        return {"outcome": "FLAG", "reasons": [f"risk_score {score} > {FLAG_RISK}"]}
    return {"outcome": "PASS", "reasons": []}


def mask_pii(case: dict) -> dict:
    """Privacy gate: drop direct identifiers and mask long digit runs before the model sees anything."""
    masked = {}
    for k, v in case.items():
        if k.lower() in _PII_KEYS:
            continue
        if isinstance(v, str):
            v = re.sub(r"\d{6,}", "[REDACTED]", v)
        masked[k] = v
    return masked
