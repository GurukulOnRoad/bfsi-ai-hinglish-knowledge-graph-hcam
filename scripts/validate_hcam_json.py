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

DATA_DIR = BASE_DIR  # adjust if you move files into /data, /json etc.

# How strict do you want? For now: only structural issues = errors.
STRICT_MODE = False


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_core_fields(
    term: Dict[str, Any],
    filename: str,
    errors: List[str],
    warnings: List[str],
):
    tid = term.get("id")
    if not isinstance(tid, str) or not tid.strip():
        errors.append(f"[{filename}] Term has missing/invalid 'id': {tid!r}")

    # Minimum semantics for a glossary term
    if "label_en" not in term or not isinstance(term.get("label_en"), str):
        errors.append(f"[{filename}][id={tid}] Missing or invalid 'label_en'")

    if "def_en" not in term or not isinstance(term.get("def_en"), str):
        errors.append(f"[{filename}][id={tid}] Missing or invalid 'def_en'")

    if "def_hi" not in term or not isinstance(term.get("def_hi"), str):
        errors.append(f"[{filename}][id={tid}] Missing or invalid 'def_hi'")

    # Soft checks → warnings only
    soft_fields = [
        "label_hi",
        "label_hiLatn",
        "def_hiLatn_explainer",
        "mental_anchor",
        "exam_mnemonic",
    ]
    for field in soft_fields:
        if field not in term:
            warnings.append(
                f"[{filename}][id={tid}] (warning) Optional field '{field}' is missing"
            )

    # related_concepts should be a list if present
    if "related_concepts" in term:
        if not isinstance(term["related_concepts"], list):
            errors.append(
                f"[{filename}][id={tid}] 'related_concepts' must be a list if present"
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
            # already reported by core check, but keep going
            continue
        if tid in seen:
            errors.append(
                f"[{filename}] Duplicate id '{tid}' at positions {seen[tid]} and {idx}"
            )
        else:
            seen[tid] = idx


def validate_file(path: Path) -> Tuple[int, int, List[str], List[str]]:
    filename = path.name
    errors: List[str] = []
    warnings: List[str] = []

    try:
        data = load_json(path)
    except Exception as e:
        errors.append(f"[{filename}] JSON parse error: {e}")
        return len(errors), len(warnings), errors, warnings

    if not isinstance(data, list):
        errors.append(f"[{filename}] Root JSON must be a list of term objects.")
        return len(errors), len(warnings), errors, warnings

    for term in data:
        if not isinstance(term, dict):
            errors.append(f"[{filename}] Term is not an object: {term!r}")
            continue
        validate_core_fields(term, filename, errors, warnings)

    # Cross-term check for ids
    validate_unique_ids(filename, data, errors)

    return len(errors), len(warnings), errors, warnings


def main() -> int:
    total_errors = 0
    total_warnings = 0
    all_error_messages: List[str] = []
    all_warning_messages: List[str] = []

    print("=== HCAM-KG JSON Validation (soft mode) ===")

    for fname in FILES_TO_VALIDATE:
        path = DATA_DIR / fname
        if not path.exists():
            total_errors += 1
            all_error_messages.append(
                f"[{fname}] File not found at {path}. Check path or FILES_TO_VALIDATE."
            )
            continue

        print(f"\nValidating {fname} ...")
        err_count, warn_count, errors, warnings = validate_file(path)
        total_errors += err_count
        total_warnings += warn_count
        all_error_messages.extend(errors)
        all_warning_messages.extend(warnings)

        if err_count == 0:
            print(f"✅ {fname}: OK (warnings: {warn_count})")
        else:
            print(f"❌ {fname}: {err_count} error(s), {warn_count} warning(s)")

    if total_errors > 0:
        print("\n--- Validation Errors ---")
        for msg in all_error_messages:
            print(msg)

    if total_warnings > 0:
        print("\n--- Validation Warnings (do not fail CI) ---")
        for msg in all_warning_messages:
            print(msg)

    if total_errors > 0:
        print(f"\nValidation FAILED with {total_errors} error(s).")
        return 1

    print("\nAll files validated successfully. ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
