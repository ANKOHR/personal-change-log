import json
from personal_change_log.cli import load_input
from personal_change_log.fixtures import generate


def test_fixtures_labelled_synthetic(fixture_dir):
    assert (fixture_dir / "records.jsonl").read_text().startswith("# SYNTHETIC")
    for path in fixture_dir.glob("*.json"):
        assert json.loads(path.read_text())["synthetic"] is True
    assert all(r["synthetic"] for r in load_input(fixture_dir)[1])


def test_fixture_ground_truth_matches_hand_computed(fixture_dir, result):
    expected = json.loads((fixture_dir / "expectations.json").read_text())
    for key in ("total_records", "meaningful_changes", "routine_records", "by_kind", "by_project"):
        assert result[key] == expected[key]
    assert sorted(r["id"] for r in result["timeline"]) == expected["meaningful_ids"]


def test_fixture_generation_deterministic(fixture_dir, tmp_path):
    other = tmp_path / "other"
    generate(other)
    for path in fixture_dir.iterdir():
        assert path.read_bytes() == (other / path.name).read_bytes()
