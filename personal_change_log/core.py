"""Pure validation and aggregation. Savings are unmeasured and never inferred."""

from collections import Counter
from datetime import date


class SchemaError(ValueError):
    """An explicit input contract was violated."""


KINDS = ("milestone", "decision", "setback", "improvement")
FIELDS = {"id", "date", "project", "kind", "summary", "meaningful", "synthetic", "entered_by"}


def checked_date(value, field):
    try:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError()
        return date.fromisoformat(value)
    except ValueError:
        raise SchemaError(f"{field}: expected ISO date YYYY-MM-DD") from None


def validate_record(record, as_of):
    if not isinstance(record, dict):
        raise SchemaError("record: expected an object")
    if set(record) != FIELDS:
        raise SchemaError(f"fields: missing {sorted(FIELDS - set(record))}; unknown {sorted(set(record) - FIELDS)}")
    for field, limit in (("id", 128), ("project", 256), ("summary", 20000), ("entered_by", 128)):
        value = record[field]
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise SchemaError(f"{field}: expected nonempty text of at most {limit} characters")
        if "\u2014" in value or any(ord(c) < 32 and c not in "\n\t" for c in value):
            raise SchemaError(f"{field}: unsupported punctuation or control character")
    for field in ("meaningful", "synthetic"):
        if type(record[field]) is not bool:
            raise SchemaError(f"{field}: expected boolean")
    if not isinstance(record["kind"], str) or record["kind"] not in KINDS:
        raise SchemaError(f"kind: expected one of {KINDS}")
    if checked_date(record["date"], "date") > checked_date(as_of, "as_of"):
        raise SchemaError("date: future date beyond input as_of")
    if not record["synthetic"] and record["entered_by"] != "Henry":
        raise SchemaError("entered_by: real data must be entered by Henry")
    return dict(record)


def compute(records, as_of):
    checked_date(as_of, "as_of")
    validated = []
    seen = set()
    for record in records:
        row = validate_record(record, as_of)
        if row["id"] in seen:
            raise SchemaError(f"id: duplicate {row['id']}")
        seen.add(row["id"])
        validated.append(row)
    timeline = sorted((r for r in validated if r["meaningful"]), key=lambda r: (r["date"], r["id"]))
    synthetic = sum(r["synthetic"] for r in validated)
    return {
        "as_of": as_of,
        "total_records": len(validated),
        "meaningful_changes": len(timeline),
        "routine_records": len(validated) - len(timeline),
        "by_kind": {kind: sum(r["kind"] == kind for r in timeline) for kind in KINDS},
        "by_project": dict(sorted(Counter(r["project"] for r in timeline).items())),
        "provenance": {"synthetic_records": synthetic, "real_records_entered_by_Henry": len(validated) - synthetic},
        "savings": {"status": "unmeasured", "note": "Time and money saved are unmeasured; no baseline was supplied."},
        "timeline": timeline,
    }
