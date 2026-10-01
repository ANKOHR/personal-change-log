# Local build evidence

Measured on 2026-10-01 on this Windows machine with Python 3.12.10. These are synthetic acceptance results, not real-use outcomes or savings.

- `python -m pytest -q`: 34 passed in 0.94 seconds.
- Installed entrypoint via local editable install with `--no-index --no-deps --no-build-isolation`; no network calls.
- Installed `pcl fixtures --out demo`, `pcl run --input demo`, and `pcl report --format md --out demo-report.md`: 0.78806 seconds combined, measured with a monotonic Stopwatch including three process launches.
- Output: 200 total, 80 meaningful, 120 routine; each kind and project has 20 meaningful entries. All planted meaningful IDs found, zero additional IDs.
- Saved report: `demo-report.md`, labelled SYNTHETIC in its provenance banner and on each timeline entry.
- The five-record example produces three meaningful entries. Empty input produces zeros. Input mutations change counts; changing the expectations file has no effect on computed results.
- Determinism test compares saved state and report bytes across repeated runs. Failure tests cover malformed JSON, missing input, unknown fields, duplicate IDs, future dates, excessive strings, and atomic report write failure.

Limits: no real-use trial, measured savings, buyer evidence, or daily-use evidence exists in this build. The two-week hook and final verdict remain pending actual use, as recorded in VERDICT.md. Runtime is a local observation, not a guarantee for arbitrary hardware or arbitrarily large input.
