"""Stable report serialization with provenance and measurement boundaries."""

import json


def banner(result):
    p = result["provenance"]
    return (f"Data provenance: {p['real_records_entered_by_Henry']} real records entered by Henry; "
            f"{p['synthetic_records']} SYNTHETIC fixture records. Significance is explicitly entered, not inferred.")


def render(result, format="md"):
    if format == "json":
        return json.dumps({"provenance_banner": banner(result), **result}, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if format != "md":
        raise ValueError("format: expected md or json")
    lines = ["# Personal Change Log", "", banner(result), "", f"As of: {result['as_of']}",
             f"Total records: {result['total_records']}", f"Meaningful changes: {result['meaningful_changes']}",
             f"Routine records: {result['routine_records']}", "", result["savings"]["note"],
             "No hypothetical savings are presented as measured.", "", "## Counts by kind"]
    lines += [f"- {k}: {v}" for k, v in result["by_kind"].items()]
    lines += ["", "## Counts by project"]
    lines += [f"- {json.dumps(k, ensure_ascii=False)}: {v}" for k, v in result["by_project"].items()]
    lines += ["", "## Timeline"]
    # JSON quoting preserves long text, newlines, and Markdown metacharacters literally.
    lines += [f"- {r['date']} [{r['id']}] {r['kind']} | " + json.dumps(r['project'], ensure_ascii=False) + " | " + json.dumps(r['summary'], ensure_ascii=False) + (" (SYNTHETIC)" if r['synthetic'] else " (real, entered by Henry)") for r in result["timeline"]]
    return "\n".join(lines) + "\n"
