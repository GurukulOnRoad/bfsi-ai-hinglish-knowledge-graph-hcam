#!/usr/bin/env python3
import json
import sys
from pathlib import Path

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
]

# Fields we will cross-check as ID references
REFERENCE_LIST_FIELDS = [
    "related_concepts",
    # you can add more here later if you start using ID lists elsewhere
]


def load_terms_from_file(path: Path):
    """Load JSON and return list of term objects."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"{path}: Invalid JSON – {e}") from e

    # Support either:
    # 1) [ {...}, {...} ]
    # 2) { "terms": [ {...}, {...} ] }
    if isinstance(data, list):
        terms = data
    elif isinstance(data, dict) and "terms" in data and isinstance(data["terms"], list):
        terms = data["terms"]
    else:
        raise ValueError(
            f"{path}: Expected top-level JSON array OR object with 'terms' array."
        )

    # Ensure all elements are dicts
    for i, t in enumerate(terms):
        if not isinstance(t, dict):
            raise ValueError(f"{path}: Term at index {i} is not an object/dict.")

    return terms


def validate_terms(terms, file_label="(unknown)"):
    errors = []
    warnings = []

    id_map = {}
    for term in terms:
        term_id = term.get("id")
        if not term_id:
            errors.append(f"{file_label}: Term missing 'id': {term}")
            continue

        # Duplicate ID check
        if term_id in id_map:
            errors.append(f"{file_label}: Duplicate id '{term_id}' found.")
        else:
            id_map[term_id] = term

        # Required fields check
        for field in REQUIRED_FIELDS:
            if field not in term or term[field] in (None, ""):
                errors.append(
                    f"{file_label}: Term '{term_id}' missing required field '{field}'."
                )

        # Type check: related_concepts should be list if present
        for ref_field in REFERENCE_LIST_FIELDS:
            if ref_field in term and term[ref_field] is not None:
                if not isinstance(term[ref_field], list):
                    errors.append(
                        f"{file_label}: Term '{term_id}' field '{ref_field}' "
                        f"must be a list of IDs."
                    )

    # Reference consistency check AFTER building id_map
    for term in terms:
        term_id = term.get("id", "(no-id)")
        for ref_field in REFERENCE_LIST_FIELDS:
            refs = term.get(ref_field, [])
            if not isinstance(refs, list):
                continue
            for ref_id in refs:
                if ref_id not in id_map:
                    errors.append(
                        f"{file_label}: Term '{term_id}' has {ref_field} "
                        f"reference '{ref_id}' which does NOT exist in this file."
                    )

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_hcam_json.py <file1.json> [file2.json ...]")
        sys.exit(1)

    all_errors = []
    all_warnings = []

    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            all_errors.append(f"{path}: File not found.")
            continue

        try:
            terms = load_terms_from_file(path)
        except ValueError as e:
            all_errors.append(str(e))
            continue

        errors, warnings = validate_terms(terms, file_label=str(path))
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    if all_warnings:
        print("WARNINGS:")
        for w in all_warnings:
            print(f"  - {w}")
        print()

    if all_errors:
        print("ERRORS:")
        for e in all_errors:
            print(f"  - {e}")
        print()
        print(f"Validation FAILED with {len(all_errors)} error(s).")
        sys.exit(1)

    print("✅ HCAM Knowledge Graph JSON validation PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
