"""Live proof that the deployed audit bucket refuses tampering.

Usage: python scripts/prove_worm.py <AuditBucketName>
Run in the sandbox account where the stack is deployed. Leaves small objects behind until retention expires.
"""
import hashlib
import sys
import uuid
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError

bucket = sys.argv[1]
s3 = boto3.client("s3")
key = f"commits/worm-proof/{uuid.uuid4()}.json"


def put(body):
    return s3.put_object(Bucket=bucket, Key=key, Body=body, ChecksumAlgorithm="SHA256")["VersionId"]


def expect_denied(label, fn):
    try:
        fn()
        print(f"FAIL  {label}: call succeeded")
        return False
    except ClientError as e:
        print(f"PASS  {label}: refused ({e.response['Error']['Code']})")
        return True


original = b'{"commit_hash": "original"}'
v1 = put(original)
print(f"wrote original version {v1}")
v2 = put(b'{"commit_hash": "tampered"}')
print(f"overwrite created a new version {v2}; the original is not replaced")

kept = s3.get_object(Bucket=bucket, Key=key, VersionId=v1)["Body"].read()
ok = kept == original
print(("PASS" if ok else "FAIL") + f"  original still readable, sha256={hashlib.sha256(kept).hexdigest()[:16]}...")

ok &= expect_denied("delete original version",
                    lambda: s3.delete_object(Bucket=bucket, Key=key, VersionId=v1))
ok &= expect_denied("shorten retention on original",
                    lambda: s3.put_object_retention(
                        Bucket=bucket, Key=key, VersionId=v1,
                        Retention={"Mode": "COMPLIANCE",
                                   "RetainUntilDate": datetime.now(timezone.utc) + timedelta(minutes=1)}))
print("\nWORM proof: " + ("PASSED" if ok else "FAILED"))
sys.exit(0 if ok else 1)
