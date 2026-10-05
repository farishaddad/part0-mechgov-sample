import io
import json


class FakeBedrock:
    def __init__(self, decision, reasoning="DTI 22% within BR-001"):
        self.decision, self.reasoning, self.calls = decision, reasoning, 0

    def converse(self, **_):
        self.calls += 1
        text = json.dumps({"decision": self.decision, "reasoning": self.reasoning})
        return {"output": {"message": {"content": [{"text": text}]}}}


class FakeS3:
    """Records writes. Object Lock behaviour itself is proven live by scripts/prove_worm.py."""

    def __init__(self):
        self.objects = {}
        self.puts = []

    def put_object(self, **kw):
        self.puts.append(kw)
        self.objects[kw["Key"]] = kw["Body"]

    def get_object(self, Bucket, Key):
        return {"Body": io.BytesIO(self.objects[Key].encode())}
