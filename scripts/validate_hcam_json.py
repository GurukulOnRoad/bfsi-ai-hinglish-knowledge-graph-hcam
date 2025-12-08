import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent

# Files to validate (repo root)
FILES_TO_VALIDATE = [
    "bharat-ai-education-hindi-ai-glossary-hcam-knowledge-graph.json",
    "equity-derivatives-hcam-viii.json",
]

DATA_DIR = BASE_DIR  # adjust if you move JSON files into /data or /json etc.


# These are the ONLY fields we validate per term
REQUIRED_FIELDS = [
    "id",
    "domain",
    "pillar",
    "topic_cluster",
    "label_en",
    "label_hi",
    "label_hiLatn",
    "def_en",
    "def_hi",
    "def_hiLatn_explainer",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_required_fields(
    term: Dict[str, Any],
    filename: str,
    errors: List[str],
):
    tid = term.get("id")

    # If id missing or not string, still log with repr
    id_for_log = tid if isinstance(tid, str) else "UNKNOWN"

    for field in REQUIRED_FIELDS:
        value = term.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"[{filename}][id={id_for_log}] Missing or invalid required field '{field}'"
            )


def validate_unique_ids(
    filename: str,
    terms: List[Dict[str, Any]],
    errors: List[str],
):
    seen: Dict[str, int] = {}
    for idx, term in enumerate(terms):
        tid = term.get("id")
        if not isinstance(tid, str):
            # already handled as a required-field error; skip from duplicate logic
            continue
        if tid in seen:
            errors.append(
                f"[{filename}] Duplicate id '{tid}' at positions {seen[tid]} and {idx}"
            )
        else:
            seen[tid] = idx


def validate_file(path: Path) -> Tuple[int, List[str]]:
    filename = path.name
    errors: List[str] = []

    try:
        data = load_json(path)
    except Exception as e:
        errors.append(f"[{filename}] JSON parse error: {e}")
        return len(errors), errors

    if not isinstance(data, list):
        errors.append(f"[{filename}] Root JSON must be a list of term objects.")
        return len(errors), errors

    for term in data:
        if not isinstance(term, dict):
            errors.append(f"[{filename}] Term is not an object: {term!r}")
            continue
        validate_required_fields(term, filename, errors)

    # Cross-term check for ids
    validate_unique_ids(filename, data, errors)

    return len(errors), errors


def main() -> int:
    total_errors = 0
    all_error_messages: List[str] = []

    print("=== HCAM-KG JSON Validation (minimal required-fields mode) ===")

    for fname in FILES_TO_VALIDATE:
        path = DATA_DIR / fname
        if not path.exists():
            total_errors += 1
            all_error_messages.append(
                f"[{fname}] File not found at {path}. Check path or FILES_TO_VALIDATE."
            )
            continue

        print(f"\nValidating {fname} ...")
        err_count, errors = validate_file(path)
        total_errors += err_count
        all_error_messages.extend(errors)

        if err_count == 0:
            print(f"✅ {fname}: OK")
        else:
            print(f"❌ {fname}: {err_count} error(s)")

    if total_errors > 0:
        print("\n--- Validation Errors ---")
        for msg in all_error_messages:
            print(msg)

        print(f"\nValidation FAILED with {total_errors} error(s).")
        return 1

    print("\nAll files validated successfully. ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
