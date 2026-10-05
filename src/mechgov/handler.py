"""Lambda entry points. Event shapes are kept simple for the demo."""
import os

import boto3

from . import commit, hard_gates, reveal

_s3 = boto3.client("s3")
_bedrock = boto3.client("bedrock-runtime")
BUCKET = os.environ.get("AUDIT_BUCKET", "")
RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "1"))
MODEL_ID = os.environ.get("MODEL_ID", "")
CANDIDATES = ["APPROVE", "DECLINE", "REFER"]


def commit_handler(event, _context):
    """event: {"case": {...}, "policy_text": "..."}"""
    case = event["case"]
    gate = hard_gates.evaluate(case)
    if gate["outcome"] in ("BLOCK", "DEFER"):
        return {"case_id": case.get("case_id"), "gate": gate, "model_called": False}

    result = commit.initial_decision(
        _bedrock, MODEL_ID, hard_gates.mask_pii(case), CANDIDATES, event.get("policy_text", "")
    )
    committed = commit.entropy_commit(_s3, BUCKET, RETENTION_DAYS, MODEL_ID, case["case_id"], result)
    return {"case_id": case["case_id"], "gate": gate, "model_called": True, **committed}


def reveal_handler(event, _context):
    """event: {"commit_key": "...", "payload": "...", "final_decision": "..."}"""
    return reveal.reveal(_s3, BUCKET, RETENTION_DAYS, event["commit_key"], event["payload"], event["final_decision"])
