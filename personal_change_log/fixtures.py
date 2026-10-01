"""Labelled fixtures with an independently enumerated oracle; no randomness."""

import json
from pathlib import Path

SYNTHETIC_HEADER = "# SYNTHETIC fixture data, not Henry's real history\n"


def generate(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    projects = ("school", "outreach", "builds", "applications")
    kinds = ("milestone", "decision", "setback", "improvement")
    for i in range(200):
        rows.append({"id": f"change-{i:03}", "date": f"2026-09-{i % 20 + 1:02}",
                     "project": projects[i % 4], "kind": kinds[(i // 4) % 4],
                     "summary": f"Synthetic recorded change {i}", "meaningful": i < 80,
                     "synthetic": True, "entered_by": "fixture-generator"})
    (out / "records.jsonl").write_text(SYNTHETIC_HEADER + "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    metadata = {"synthetic": True, "label": "SYNTHETIC fixture metadata", "as_of": "2026-09-30"}
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    # Hand computation: 0..79 meaningful, 80..199 routine. Four projects cycle
    # twenty times; four kinds each occupy four slots in five full 16-slot cycles.
    expected = {"synthetic": True, "label": "SYNTHETIC hand-computed expectations",
                "total_records": 200, "meaningful_changes": 80, "routine_records": 120,
                "by_project": {p: 20 for p in projects}, "by_kind": {k: 20 for k in kinds},
                "meaningful_ids": [f"change-{i:03}" for i in range(80)]}
    (out / "expectations.json").write_text(json.dumps(expected, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return expected
