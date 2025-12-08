#!/usr/bin/env python3
import json
import sys
from pathlib import Path

# HCAM-required fields that must exist inside additionalProperty[]
REQUIRED_FIELDS = [
    "def_hi",
    "def_hiLatn_explainer",
    "domain",
    "pillar",
    "topic_cluster",
]

def load_json(path_str):
    path = Path(path_str)
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def get_prop(term, name):
    """
    For a DefinedTerm object, pull a property from additionalProperty[]
    where PropertyValue.name == name.
    """
    for pv in term.get("additionalProperty", []):
        if isinstance(pv, dict) and pv.get("name") == name:
            return pv.get("value")
    return None

def term_id(term):
    # Prefer @id, fall back to name, then UNKNOWN
    return term.get("@id") or term.get("name") or "UNKNOWN"

def validate_defined_term_list(filename, terms):
    errors = 0
    for idx, term in enumerate(terms):
        tid = term_id(term)

        if term.get("@type") != "DefinedTerm":
            print(
                f"[{filename}][index={idx}][id={tid}] "
                f"@type should be 'DefinedTerm', got {term.get('@type')!r}"
            )
            errors += 1

        # Check that additionalProperty exists and is a list
        if not isinstance(term.get("additionalProperty"), list):
            print(
                f"[{filename}][index={idx}][id={tid}] "
                "Missing or invalid 'additionalProperty' (expected an array)"
            )
            errors += 1
            # If this is wrong, skip the rest for this term
            continue

        # Check each required conceptual field inside additionalProperty[]
        for field in REQUIRED_FIELDS:
            value = get_prop(term, field)
            if value is None or (isinstance(value, str) and not value.strip()):
                print(
                    f"[{filename}][index={idx}][id={tid}] "
                    f"Missing or empty required field '{field}' in additionalProperty"
                )
                errors += 1

    return errors

def main(argv):
    if len(argv) < 2:
        print("Usage: python scripts/validate_hcam_json.py <file1.json> [<file2.json> ...]")
        return 1

    total_errors = 0

    for path_str in argv[1:]:
        filename = Path(path_str).name
        try:
            data = load_json(path_str)
        except Exception as e:
            print(f"[{filename}] Failed to load JSON: {e}")
            total_errors += 1
            continue

        # Case 1: root is a list of DefinedTerm objects (AI glossary file)
        if isinstance(data, list):
            total_errors += validate_defined_term_list(filename, data)
            continue

        # Case 2: root is a DefinedTermSet with hasDefinedTerm[] (Equity glossary file)
        if isinstance(data, dict) and data.get("@type") == "DefinedTermSet":
            terms = data.get("hasDefinedTerm", [])
            if not isinstance(terms, list):
                print(
                    f"[{filename}] 'hasDefinedTerm' must be a list "
                    "inside DefinedTermSet"
                )
                total_errors += 1
            else:
                total_errors += validate_defined_term_list(filename, terms)
            continue

        # Anything else is treated as invalid root structure
        print(
            f"[{filename}] Root JSON must be either:\n"
            "  • a list of DefinedTerm objects, OR\n"
            "  • a DefinedTermSet object with hasDefinedTerm[]"
        )
        total_errors += 1

    if total_errors:
        print(f"HCAM JSON validation FAILED with {total_errors} error(s).")
        return 1

    print("HCAM JSON validation PASSED ✅")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
