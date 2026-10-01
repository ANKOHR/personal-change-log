"""Local-only CLI. No clock, network, database, or inferred measurements."""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from .core import SchemaError, compute, checked_date, validate_record
from .fixtures import generate
from .report import render, banner


class InputError(ValueError):
    pass


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InputError(f"ParseError: {path.name}: line {exc.lineno}: {exc.msg}") from None


def load_input(directory):
    directory = Path(directory)
    if not directory.is_dir():
        raise InputError(f"MissingInput: {directory}: use pcl fixtures --out <dir> or create an input directory")
    files = sorted(directory.iterdir())
    allowed = {"metadata.json", "records.jsonl", "expectations.json"}
    for path in files:
        if path.name not in allowed:
            raise InputError(f"SchemaError: {path.name}: line 1: unsupported input file; use records.jsonl and metadata.json")
    if not files:
        return compute([], "1970-01-01"), []
    if not (directory / "metadata.json").is_file() or not (directory / "records.jsonl").is_file():
        raise InputError("MissingInput: metadata.json and records.jsonl are required; see pcl run --help")
    meta = read_json(directory / "metadata.json")
    if not isinstance(meta, dict) or set(meta) != {"as_of", "synthetic", "label"} or type(meta.get("synthetic")) is not bool or not isinstance(meta.get("label"), str):
        raise InputError("SchemaError: metadata.json: line 1: fields must be as_of, synthetic, label")
    try:
        checked_date(meta["as_of"], "as_of")
    except SchemaError as exc:
        raise InputError(f"SchemaError: metadata.json: line 1: {exc}") from None
    rows, seen = [], set()
    path = directory / "records.jsonl"
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InputError(f"ParseError: {path.name}: line {line_number}: {exc.msg}") from None
        try:
            validate_record(row, meta["as_of"])
            if meta["synthetic"] and not row["synthetic"]:
                raise SchemaError("synthetic: fixture metadata requires synthetic records")
            if row["id"] in seen:
                raise SchemaError(f"id: duplicate {row['id']}")
        except SchemaError as exc:
            raise InputError(f"SchemaError: {path.name}: line {line_number}: {exc}") from None
        seen.add(row["id"])
        rows.append(row)
    return compute(rows, meta["as_of"]), rows


def atomic_write(path, text):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def parser():
    p = argparse.ArgumentParser(description="Personal Change Log: explicit changes from local files.")
    sub = p.add_subparsers(dest="command", required=True)
    fixtures = sub.add_parser("fixtures", help="Generate 200 labelled synthetic records", epilog="Example: pcl fixtures --out demo")
    fixtures.add_argument("--out", required=True)
    run = sub.add_parser("run", help="Validate inputs and compute the timeline", epilog="Example: pcl run --input demo --state .pcl/result.json")
    run.add_argument("--input", required=True)
    run.add_argument("--state", default=".pcl/result.json")
    report = sub.add_parser("report", help="Render the last computed result with provenance", epilog="Example: pcl report --format md --out report.md")
    report.add_argument("--format", choices=("md", "json"), default="md")
    report.add_argument("--state", default=".pcl/result.json")
    report.add_argument("--out")
    timeline = sub.add_parser("timeline", help="Filter meaningful changes by project and date", epilog="Example: pcl timeline --input demo --project school --since 2026-09-10")
    timeline.add_argument("--input", required=True)
    timeline.add_argument("--project")
    timeline.add_argument("--since")
    timeline.add_argument("--format", choices=("md", "json"), default="md")
    compare = sub.add_parser("compare", help="Compare meaningful counts in two inclusive periods", epilog="Example: pcl compare --input demo --before 2026-09-01 2026-09-10 --after 2026-09-11 2026-09-20")
    compare.add_argument("--input", required=True)
    compare.add_argument("--before", nargs=2, required=True, metavar=("START", "END"))
    compare.add_argument("--after", nargs=2, required=True, metavar=("START", "END"))
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "fixtures":
            generate(args.out)
            print("Generated 200 SYNTHETIC records and labelled hand-computed expectations.")
        elif args.command == "run":
            result, rows = load_input(args.input)
            Path(args.state).parent.mkdir(parents=True, exist_ok=True)
            atomic_write(args.state, json.dumps({"as_of": result["as_of"], "records": rows}, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            print(f"Computed {result['meaningful_changes']} meaningful changes from {result['total_records']} records. " + banner(result))
        elif args.command == "report":
            if not Path(args.state).is_file():
                raise InputError("MissingInput: result state missing; run pcl run --input <dir> first")
            saved = read_json(Path(args.state))
            # Recompute from cached explicit inputs; never trust stored totals.
            result = compute(saved["records"], saved["as_of"])
            output = render(result, args.format)
            if args.out:
                atomic_write(args.out, output)
            else:
                print(output, end="")
        elif args.command == "timeline":
            result, rows = load_input(args.input)
            if args.since:
                checked_date(args.since, "since")
            filtered = [r for r in rows if (not args.project or r["project"] == args.project) and (not args.since or r["date"] >= args.since)]
            print(render(compute(filtered, result["as_of"]), args.format), end="")
        elif args.command == "compare":
            result, _ = load_input(args.input)
            counts = []
            for name, bounds in (("before", args.before), ("after", args.after)):
                start, end = bounds
                checked_date(start, name + ".start")
                checked_date(end, name + ".end")
                if start > end:
                    raise SchemaError(f"{name}: start exceeds end")
                counts.append(sum(start <= r["date"] <= end for r in result["timeline"]))
            print(json.dumps({"provenance_banner": banner(result), "before_count": counts[0], "after_count": counts[1], "change_in_count": counts[1] - counts[0], "measurement": "Counts of explicitly meaningful input records; no causal inference or savings estimate."}, sort_keys=True, indent=2))
        return 0
    except (InputError, SchemaError) as exc:
        message = str(exc) if isinstance(exc, InputError) else f"SchemaError: {exc}"
    except (OSError, UnicodeError) as exc:
        message = f"FileError: {exc}"
    except (KeyError, TypeError, ValueError) as exc:
        message = f"SchemaError: saved result fields invalid: {exc}"
    print(message.replace("\u2014", "-"), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
