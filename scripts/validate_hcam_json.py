#!/usr/bin/env python
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "schemas" / "hcam_term.schema.json"
REPORT_PATH = REPO_ROOT / "hcam_validation_report.txt"


def load_schema() -> dict:
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found: {SCHEMA_PATH}")
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_file(validator: Draft202012Validator, json_path: Path) -> int:
    errors_found = 0

    if not json_path.exists():
        msg = f"[{json_path.name}] File not found."
        print(msg)
        REPORT_PATH.write_text(msg + "\n", encoding="utf-8")
        return 1

    with json_path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            msg = f"[{json_path.name}] Invalid JSON: {e}"
            print(msg)
            with REPORT_PATH.open("a", encoding="utf-8") as rep:
                rep.write(msg + "\n")
            return 1

    if not isinstance(data, list):
        msg = f"[{json_path.name}] Root JSON must be a list of term objects."
        print(msg)
        with REPORT_PATH.open("a", encoding="utf-8") as rep:
            rep.write(msg + "\n")
        return 1

    for idx, term in enumerate(data):
        term_id = term.get("id", "UNKNOWN")
        for error in sorted(validator.iter_errors(term), key=lambda e: e.path):
            errors_found += 1
            field_path = ".".join(str(p) for p in error.path) or "<root>"
            msg = (
                f"[{json_path.name}][index={idx}][id={term_id}] "
                f"Field '{field_path}': {error.message}"
            )
            print(msg)
            with REPORT_PATH.open("a", encoding="utf-8") as rep:
                rep.write(msg + "\n")

    if errors_found == 0:
        msg = f"[{json_path.name}] ✅ JSON Schema validation PASSED for {len(data)} term(s)."
        print(msg)
        with REPORT_PATH.open("a", encoding="utf-8") as rep:
            rep.write(msg + "\n")

    return errors_found


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(
            "Usage: python scripts/validate_hcam_json.py "
            "bharat-ai-education-hindi-ai-glossary-hcam-knowledge-graph.json "
            "equity-derivatives-hcam-viii.json"
        )
        return 1

    # clear previous report
    if REPORT_PATH.exists():
        REPORT_PATH.unlink()

    schema = load_schema()
    validator = Draft202012Validator(schema)

    total_errors = 0
    for file_arg in argv[1:]:
        json_path = REPO_ROOT / file_arg
        total_errors += validate_file(validator, json_path)

    if total_errors == 0:
        print("HCAM JSON validation SUCCESS.")
        return 0
    else:
        print(f"HCAM JSON validation FAILED with {total_errors} error(s).")
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
