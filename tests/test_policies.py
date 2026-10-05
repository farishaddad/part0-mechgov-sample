from pathlib import Path

POL = Path(__file__).resolve().parents[1] / "policies"


def test_three_policies_two_forbid_one_permit():
    texts = [p.read_text() for p in sorted(POL.glob("*.cedar"))]
    assert len(texts) == 3
    assert sum(t.lstrip().split("\n", 1)[1].lstrip().startswith("permit(") for t in texts) == 1
    assert sum("forbid(" in t for t in texts) == 2


def test_harness_locked_to_decision_writer():
    t = (POL / "02_forbid_harness_other_tools.cedar").read_text()
    assert '"mech-gov-harness"' in t
    assert 'AgentCore::Action::"AuditAPI___emit_decision_record"' in t
