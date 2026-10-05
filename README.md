# Part 0 sample: mechanical enforcement around an LLM decision

Companion code for *Mechanical Governance for LLM Decisions* (AWS Builder Center).
It shows three controls that sit **outside the model**:

| Control | Where | What it guarantees |
|---|---|---|
| Hard gates | `src/mechgov/hard_gates.py` | Risk score, regulatory flags and completeness decide BLOCK / DEFER / PASS before any model call |
| Entropy commit-reveal | `src/mechgov/commit.py`, `reveal.py` | The model's first decision is hashed and written to S3 Object Lock (COMPLIANCE) before counterarguments; a later change is detectable and provable |
| AgentCore Policy (Cedar) | `policies/*.cedar` | Analysts limited by role and exposure; the harness identity can only call the decision writer; one policy shuts the gateway |

Synthetic data only. This is a teaching sample, not a production system.

## Where the gate inputs come from

The model never produces its own gate inputs. In the reference design:

- `risk_score`: your credit model (e.g. a SageMaker endpoint) and bureau score
- `regulatory_flags`: KYC / AML / PEP / sanctions screening systems
- affordability fields: deterministic code over Open Banking data
- case documents are turned into structured fields upstream; the model sees masked fields only

## Layout

```
app.py, cdk.json          CDK app (Python)
infra/stack.py            Object Lock bucket + commit and reveal Lambdas
src/mechgov/              gates, commit, reveal, Lambda handlers (stdlib + boto3 only)
policies/                 the three Cedar policies from the article
tests/                    offline tests (no AWS needed)
scripts/prove_worm.py     live check against the deployed bucket
```

## Run the offline tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Deploy (sandbox account first)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cdk bootstrap
cdk deploy -c retention_days=1 -c model_id=<your-claude-inference-profile-id>
```

**Retention warning.** COMPLIANCE mode cannot be shortened or removed by anyone, root user included,
until the date passes. The sample defaults to **1 day** so a demo account can be cleaned up.
Use your real retention (e.g. 7 years) only in a governed account. The bucket is kept on `cdk destroy`.

## Prove the bucket is tamper-evident

```bash
python scripts/prove_worm.py <AuditBucketName from the stack outputs>
```

It writes a commit, overwrites it, then tries to delete the original version and shorten its
retention. Expected: the original version survives and both destructive calls are refused.

## Attach the Cedar policies

1. Replace the gateway ARN in `policies/*.cedar` with your AgentCore Gateway ARN.
2. Check the principal type matches how your gateway authenticates (the sample uses `AgentCore::OAuthUser`, as in the article).
3. Attach them through AgentCore Policy in **LOG_ONLY** mode first and review decisions in CloudWatch.
4. Promote to **ENFORCE** after reviewing real traffic. Keep `03_emergency_shutdown.cedar` detached until you need it.

## Not included

I6Q argument scoring, the ambiguity gate, and the AgentCore Managed Harness wiring. See the
[mech-gov framework](https://github.com/SantanderAI/mech-gov-framework) (Apache 2.0, Santander AI Lab).
