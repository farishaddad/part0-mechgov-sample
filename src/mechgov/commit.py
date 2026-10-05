"""Entropy commit: hash and lock the initial decision before any counterarguments."""
import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone


def canonical_payload(case_id: str, decision: str, reasoning: str, nonce: str) -> str:
    return json.dumps(
        {"case_id": case_id, "decision": decision, "reasoning": reasoning, "nonce": nonce},
        sort_keys=True, separators=(",", ":"),
    )


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def initial_decision(bedrock, model_id: str, case_fields: dict, candidates: list, policy_text: str) -> dict:
    prompt = (
        f"Policy:\n{policy_text}\n\n"
        f"Case (structured fields, PII masked):\n{json.dumps(case_fields)}\n\n"
        f"Choose exactly one of {candidates}. Reply only with JSON: "
        '{"decision": "...", "reasoning": "..."}'
    )
    resp = bedrock.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"temperature": 0},
    )
    result = json.loads(resp["output"]["message"]["content"][0]["text"])
    if result.get("decision") not in candidates:  # frozen candidate set, checked mechanically
        raise ValueError(f"Decision outside frozen candidate set: {result.get('decision')}")
    return result


def entropy_commit(s3, bucket: str, retention_days: int, model_id: str, case_id: str, result: dict) -> dict:
    nonce = secrets.token_hex(32)
    payload = canonical_payload(case_id, result["decision"], result["reasoning"], nonce)
    commit_hash = sha256_hex(payload)
    now = datetime.now(timezone.utc)
    key = f"commits/{case_id}/{commit_hash}.json"
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps({"case_id": case_id, "commit_hash": commit_hash,
                         "committed_at": now.isoformat(), "model_id": model_id}),
        ContentType="application/json",
        ChecksumAlgorithm="SHA256",  # Object Lock writes need an integrity checksum
        ObjectLockMode="COMPLIANCE",
        ObjectLockRetainUntilDate=now + timedelta(days=retention_days),
    )
    # The commit record holds only the hash. The payload is held by the pipeline until the reveal.
    return {"commit_hash": commit_hash, "commit_key": key, "payload": payload}
