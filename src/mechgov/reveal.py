"""Reveal: publish the committed payload, prove it matches the hash, and record any decision flip."""
import json
from datetime import datetime, timedelta, timezone

from .commit import sha256_hex


def reveal(s3, bucket: str, retention_days: int, commit_key: str, payload: str, final_decision: str) -> dict:
    committed = json.loads(s3.get_object(Bucket=bucket, Key=commit_key)["Body"].read())
    if sha256_hex(payload) != committed["commit_hash"]:
        raise ValueError("Payload does not match the committed hash")

    initial = json.loads(payload)["decision"]
    flipped = final_decision != initial
    now = datetime.now(timezone.utc)
    record = {
        "case_id": committed["case_id"],
        "commit_hash": committed["commit_hash"],
        "payload": payload,
        "initial_decision": initial,
        "final_decision": final_decision,
        "flipped": flipped,  # feeds the Flip-Vote Score (FVS) metric
        "revealed_at": now.isoformat(),
    }
    s3.put_object(
        Bucket=bucket,
        Key=f"reveals/{committed['case_id']}/{committed['commit_hash']}.json",
        Body=json.dumps(record),
        ContentType="application/json",
        ChecksumAlgorithm="SHA256",
        ObjectLockMode="COMPLIANCE",
        ObjectLockRetainUntilDate=now + timedelta(days=retention_days),
    )
    return record
