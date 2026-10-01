import pytest
from personal_change_log.core import compute, SchemaError
from personal_change_log.cli import load_input


@pytest.mark.parametrize("field,value", [
    ("amount", -1), ("date", "2027-01-01"), ("summary", "x" * 20001),
    ("meaningful", 1), ("kind", []), ("date", "not-a-date"),
    ("summary", "bad\u2014punctuation"), ("entered_by", "Other")])
def test_rejects_adversarial_values(fixture_dir, field, value):
    _, rows = load_input(fixture_dir)
    row = dict(rows[0], synthetic=False, entered_by="Henry")
    row[field] = value
    with pytest.raises(SchemaError, match=field):
        compute([row], "2026-09-30")


def test_duplicate_ids(fixture_dir):
    _, rows = load_input(fixture_dir)
    with pytest.raises(SchemaError, match="duplicate"):
        compute([rows[0], rows[0]], "2026-09-30")


def test_handles_unicode_and_long_inputs(fixture_dir):
    _, rows = load_input(fixture_dir)
    rows[0]["summary"] = "学校 café 🙂 C:\\Users\\Henry\\work\n" + "x" * 15000
    assert compute(rows, "2026-09-30")["timeline"][0]["summary"] == rows[0]["summary"]


def test_ground_truth_corruption_changes_computed_figures(fixture_dir):
    original, rows = load_input(fixture_dir)
    rows[100]["meaningful"] = True
    changed = compute(rows, "2026-09-30")
    assert changed["meaningful_changes"] == original["meaningful_changes"] + 1
    assert "change-100" in [r["id"] for r in changed["timeline"]]
