import json
import time
import pytest
from personal_change_log.cli import main, load_input


def test_run_completes_on_fixture(fixture_dir, tmp_path, capsys):
    state = tmp_path / "state.json"
    start = time.perf_counter()
    assert main(["run", "--input", str(fixture_dir), "--state", str(state)]) == 0
    assert main(["report", "--state", str(state), "--format", "md"]) == 0
    assert time.perf_counter() - start < 5
    assert "SYNTHETIC" in capsys.readouterr().out


def test_empty_input_renders_without_traceback(tmp_path, capsys):
    directory = tmp_path / "empty"
    directory.mkdir()
    state = tmp_path / "state.json"
    assert main(["run", "--input", str(directory), "--state", str(state)]) == 0
    capsys.readouterr()
    assert main(["report", "--state", str(state), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["total_records"] == 0


def test_malformed_input_named_error(fixture_dir, capsys):
    (fixture_dir / "records.jsonl").write_text("# SYNTHETIC\n{broken\n")
    assert main(["run", "--input", str(fixture_dir)]) == 2
    error = capsys.readouterr().err
    assert "ParseError" in error and "records.jsonl: line 2" in error
    assert "Traceback" not in error


def test_determinism_byte_identical(fixture_dir, tmp_path):
    state = tmp_path / "state.json"
    output = tmp_path / "report.json"
    args = ["run", "--input", str(fixture_dir), "--state", str(state)]
    report = ["report", "--state", str(state), "--format", "json", "--out", str(output)]
    assert main(args) == main(report) == 0
    first = state.read_bytes(), output.read_bytes()
    assert main(args) == main(report) == 0
    assert first == (state.read_bytes(), output.read_bytes())


def test_cli_smoke_all_subcommands(tmp_path, capsys):
    directory, state = tmp_path / "fixture", tmp_path / "state.json"
    commands = [["fixtures", "--out", str(directory)],
                ["run", "--input", str(directory), "--state", str(state)],
                ["report", "--state", str(state)],
                ["timeline", "--input", str(directory), "--project", "school", "--since", "2026-09-10"],
                ["compare", "--input", str(directory), "--before", "2026-09-01", "2026-09-10", "--after", "2026-09-11", "2026-09-20"]]
    for command in commands:
        assert main(command) == 0
        assert chr(0x2014) not in capsys.readouterr().out
    for command in ("fixtures", "run", "report", "timeline", "compare"):
        with pytest.raises(SystemExit) as exc:
            main([command, "--help"])
        assert exc.value.code == 0
        assert "Example:" in capsys.readouterr().out


def test_missing_input_named_error(tmp_path, capsys):
    assert main(["run", "--input", str(tmp_path / "missing")]) == 2
    assert "MissingInput" in capsys.readouterr().err


def test_report_write_failure_no_partial_files(fixture_dir, tmp_path, capsys):
    state = tmp_path / "state.json"
    assert main(["run", "--input", str(fixture_dir), "--state", str(state)]) == 0
    before = sorted(p.name for p in tmp_path.iterdir())
    assert main(["report", "--state", str(state), "--out", str(tmp_path)]) == 2
    assert sorted(p.name for p in tmp_path.iterdir()) == before
    assert "FileError" in capsys.readouterr().err


def test_schema_error_lists_field_and_line(fixture_dir, capsys):
    lines = (fixture_dir / "records.jsonl").read_text().splitlines()
    row = json.loads(lines[1])
    row["amount"] = -1
    lines[1] = json.dumps(row)
    (fixture_dir / "records.jsonl").write_text("\n".join(lines))
    assert main(["run", "--input", str(fixture_dir)]) == 2
    error = capsys.readouterr().err
    assert "SchemaError" in error and "amount" in error and "line 2" in error


def test_real_provenance_and_five_record_example():
    from pathlib import Path
    result, rows = load_input(Path(__file__).parent.parent / "examples" / "five-records")
    assert len(rows) == 5
    assert result["meaningful_changes"] == 3
    assert result["provenance"]["synthetic_records"] == 5


def test_report_recomputes_cached_records(fixture_dir, tmp_path, capsys):
    state = tmp_path / "state.json"
    main(["run", "--input", str(fixture_dir), "--state", str(state)])
    saved = json.loads(state.read_text())
    saved["records"][100]["meaningful"] = True
    state.write_text(json.dumps(saved))
    capsys.readouterr()
    assert main(["report", "--state", str(state), "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["meaningful_changes"] == 81


def test_mixed_real_and_synthetic_provenance(fixture_dir, capsys):
    from personal_change_log.core import compute
    from personal_change_log.report import render
    _, rows = load_input(fixture_dir)
    rows[0].update(synthetic=False, entered_by="Henry")
    result = compute(rows, "2026-09-30")
    assert "1 real records entered by Henry" in render(result)
    assert "199 SYNTHETIC fixture records" in render(result)


def test_compare_exact_counts(fixture_dir, capsys):
    assert main(["compare", "--input", str(fixture_dir), "--before", "2026-09-01", "2026-09-10", "--after", "2026-09-11", "2026-09-20"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert (output["before_count"], output["after_count"], output["change_in_count"]) == (40, 40, 0)


def test_timeline_exact_filter(fixture_dir, capsys):
    assert main(["timeline", "--input", str(fixture_dir), "--project", "school", "--since", "2026-09-10", "--format", "json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["meaningful_changes"] == 8
    assert all(r["project"] == "school" and r["date"] >= "2026-09-10" for r in output["timeline"])


def test_corrupt_expectations_not_used(fixture_dir):
    (fixture_dir / "expectations.json").write_text('{"synthetic":true,"meaningful_changes":999}')
    assert load_input(fixture_dir)[0]["meaningful_changes"] == 80


def test_actual_module_entrypoint(tmp_path):
    import subprocess
    import sys
    process = subprocess.run([sys.executable, "-m", "personal_change_log.cli", "fixtures", "--out", str(tmp_path / "module")], capture_output=True, text=True)
    assert process.returncode == 0
    assert "SYNTHETIC" in process.stdout
