import json
from personal_change_log.report import render


def test_report_matches_ground_truth_exact(result):
    report = json.loads(render(result, "json"))
    assert report["total_records"] == 200
    assert report["meaningful_changes"] == 80
    assert report["routine_records"] == 120
    assert report["by_kind"] == dict.fromkeys(("milestone", "decision", "setback", "improvement"), 20)
    assert report["by_project"] == dict.fromkeys(("school", "outreach", "builds", "applications"), 20)


def test_report_zero_false_positives(result):
    report = json.loads(render(result, "json"))
    assert {r["id"] for r in report["timeline"]} == {f"change-{i:03}" for i in range(80)}


def test_report_carries_provenance_banner(result):
    for format in ("md", "json"):
        output = render(result, format)
        assert "200 SYNTHETIC" in output
        assert "0 real records entered by Henry" in output


def test_hypothetical_figures_labelled(result):
    assert "unmeasured" in render(result, "json")
    assert "No hypothetical savings are presented as measured" in render(result)
    assert "unmeasured" in render(result)


def test_no_em_dashes_in_outputs(result):
    for format in ("md", "json"):
        assert chr(0x2014) not in render(result, format)
