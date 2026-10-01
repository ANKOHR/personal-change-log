# Personal Change Log

A local Python CLI that turns explicitly recorded changes in projects and life into a chronological timeline. For Henry's school, outreach, builds, and applications. It computes counts from input records and never discovers changes or decides what matters.

## Quickstart

Python 3.10 or newer, CPU only. No runtime dependencies, network calls, models, GPU packages, or database server.

```powershell
python -m pip install --no-deps --no-build-isolation -e .
pcl fixtures --out demo
pcl run --input demo
pcl report --format md
python -m pytest -q
```

If Python's scripts directory is outside PATH, use `python -m personal_change_log.cli` in place of `pcl`, or add the user scripts directory reported by pip to PATH. Installation above uses only the local package and already installed setuptools; add `--no-index` to prohibit package index access explicitly.

The fixture has 200 SYNTHETIC records: 80 meaningful changes and 120 routine records. Each of four projects and four kinds has 20 meaningful changes. The expectations file documents the manual calculation. Expectations are never read by the engine. Generation uses no randomness, so no seed is needed.

For the smallest hand-written example:

```powershell
pcl run --input examples/five-records
pcl report --format json
```

It contains five SYNTHETIC records, three meaningful and two routine. Nothing in the repository represents a real trial with Henry.

## Input format reference

An input directory contains `metadata.json`, `records.jsonl`, and optionally `expectations.json` (an ignored test oracle). Other files are rejected to avoid silently missing unsupported formats. UTF-8 is required. Blank lines and lines starting with `#` in JSONL are ignored. Each data line is exactly one JSON object. This is a documented JSONL extension for fixture header comments.

Metadata has exactly three fields:

```json
{"as_of":"2026-09-30","synthetic":false,"label":"Henry's manually entered data"}
```

`as_of` is an explicit ISO date, not the machine's clock. Dates after it are rejected. `synthetic` is a boolean; true requires every record to be synthetic. False allows real records or a mixed input, with provenance counted separately per record. `label` is a descriptive string and is not proof of origin.

A real record entered by Henry would have this shape (this documentation example is illustrative, not a shipped real record):

```json
{"id":"unique-id","date":"2026-09-30","project":"builds","kind":"milestone","summary":"Henry enters the actual change here","meaningful":true,"synthetic":false,"entered_by":"Henry"}
```

| Field | Rule |
| --- | --- |
| id | Nonempty string, at most 128 characters, unique across input |
| date | ISO YYYY-MM-DD, no later than metadata as_of |
| project | Nonempty string, at most 256 characters |
| kind | milestone, decision, setback, or improvement |
| summary | Nonempty string, at most 20,000 characters |
| meaningful | Strict boolean; true includes the record in the timeline |
| synthetic | Strict boolean; labelled individually in the timeline |
| entered_by | Nonempty string, at most 128 characters; real records require Henry |

Every field is required. Unknown fields, including amounts or claimed savings, are rejected. Negative monetary values therefore cannot become reported totals. Duplicate IDs, invalid dates, extreme strings, forbidden punctuation, and control characters are rejected, never dropped. Unicode and Windows paths are supported. No em dash character is accepted in input text; use a plain hyphen. The only allowed control characters within text are newline and tab.

An entirely empty directory is valid: zero counts and an explicit sentinel as_of of 1970-01-01. This sentinel is not a measurement or a trial date. A nonempty directory missing either required file is an error. Timeline ordering is ascending date then ID. Kind counts and project counts concern meaningful records only; meaningful plus routine reconciles to total records.

## Subcommand catalogue

All subcommands have `--help` and examples.

```powershell
pcl fixtures --out demo
pcl run --input demo --state .pcl/result.json
pcl report --format md --out report.md
pcl report --format json
pcl timeline --input demo --project school --since 2026-09-10 --format json
pcl compare --input demo --before 2026-09-01 2026-09-10 --after 2026-09-11 2026-09-20
```

`fixtures` creates or replaces the three named fixture files in the supplied directory. Use a dedicated directory. `run` validates all records before atomically replacing the saved snapshot. `report` validates and recomputes from that snapshot and renders markdown or JSON. Changing original files requires another `run`. State is local and contains the entered records. `timeline` filters by exact project and inclusive starting date, with totals and provenance scoped to the selected records. `compare` counts meaningful records in two inclusive date ranges and their difference; overlapping periods are allowed and count their shared records in each period. Counts are not causal claims about improvement.

Outputs are byte-identical for identical input and options. There are no timestamps or absolute paths in successful computed output. Output files use UTF-8 and LF. Markdown quotes user text as JSON to preserve its literal characters; reports are plain text, not trusted HTML.

## Architecture

```text
fixtures.py -> labelled JSONL + metadata + independent expectations
local JSONL + metadata -> cli.load_input -> core.validate_record
                                       -> core.compute
                                       -> atomic local snapshot
snapshot -> core.compute -> report.render -> stdout or atomic output file
tests -> ground truth, mutation checks, failures, determinism, CLI
```

Core functions have no I/O. Reports do not load expectations. The CLI uses only Python standard library filesystem operations. `ParseError` names the file and line for bad JSON. `SchemaError` names the offending field and record line. `MissingInput` gives a usage hint and exit code 2. `FileError` covers unreadable inputs, encoding failures, and unwritable report paths. Failed output replacement removes the temporary file and preserves an existing destination. Invalid saved snapshots produce a named error. Argument errors use argparse's named usage errors. No failure intentionally emits a traceback.

## Honesty boundary and fixture policy

Significance is supplied, never inferred. `synthetic: false` and `entered_by: Henry` are user attestations; the CLI cannot independently verify them. Reports state the number of records declared real and entered by Henry and the number declared SYNTHETIC. Every synthetic record is labelled in the timeline. All JSON fixture files contain `synthetic: true` and an explicit label; JSON does not permit header comments. Every fixture JSONL file has a SYNTHETIC header and a boolean on every record. Synthetic examples are illustrative, not evidence of real usefulness.

No savings figure is produced. Time or money saved remains explicitly unmeasured because no baseline is supplied. No hypothetical number appears as measured. Benchmark runtime is a measurement of the synthetic workflow only, not a claim of time saved for Henry. The tool does not predict, discover, estimate, or call a model. A syntactically valid record can still be factually wrong; hand-checking matters.

## Acceptance and evidence

The hypothesis is that a deterministic tested timeline can be trusted to compute the recorded facts. Tests compare all 80 planted meaningful IDs, all counts, provenance, and mutated records with independently stated expectations, and require fixture run plus report to complete below five seconds. See `EVIDENCE.md` for local results. This validates arithmetic and parsing, not real-use value or human judgements of significance.

## Two-week improvement hook and verdict

Start the evidence window when Henry first uses real data. For 14 days record each actual use, then hand-check a sample of meaningful classifications against his original notes. Primary metric: incorrect classifications divided by hand-checked records. Record numerator, denominator, sampling method, use count, and window dates locally in a trial file, not in shipped synthetic fixtures. If error rate exceeds 10 percent, fix the largest demonstrated cause and retest or kill with the reason recorded. If there is no actual use, kill with the reason recorded. No sample means accuracy is unmeasured, never zero errors by assumption.

Verdict is PENDING until the two-week real-use evidence window ends. Then write a reasoned verdict: expand if daily use or revenue earns it; integrate if it overlaps heavily with a sibling; commercialise if a buyer would pay as-is; maintain as portfolio evidence otherwise; kill if never used or acceptance criteria cannot be met. This build cannot honestly claim that the future evidence window has occurred. See `VERDICT.md`.
