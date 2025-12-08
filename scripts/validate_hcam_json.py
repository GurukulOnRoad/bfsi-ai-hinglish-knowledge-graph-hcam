#!/usr/bin/env python3
"""
HCAM™ JSON Validator

Supports:
- A list of DefinedTerm objects (AI glossary)
- A DefinedTermSet with hasDefinedTerm[] (Equity glossary)

Validates:
- Presence of key HCAM fields inside additionalProperty[]
  (def_hi, def_hiLatn_explainer, domain, pillar, topic_cluster)
"""

import json
import sys
from pathlib import Path

# HCAM conceptual fields that must exist in additionalProperty[]
REQUIRED_PROPERTIES = [
    "def_hi",
    "def_hiLatn_explainer",
    "domain",
    "pillar",
    "topic_cluster",
]


def load_json(path_str: str):
    path = Path(path_str)
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def get_prop(term: dict, name: str):
    """
    For a DefinedTerm object, pull value from additionalProperty[]
    where PropertyValue.name == name.
    """
    props = term.get("additionalProperty", [])
    if not isinstance(props, list):
        return None

    for pv in props:
        if not isinstance(pv, dict):
            continue
        if pv.get("name") == name:
            return pv.get("value")
    return None


def term_id(term: dict) -> str:
    # Prefer @id, fall back to name, then UNKNOWN
    return term.get("@id") or term.get("name") or "UNKNOWN"


def validate_defined_term_list(filename: str, terms: list) -> int:
    errors = 0

    for idx, term in enumerate(terms):
        tid = term_id(term)

        # Basic type check
        if term.get("@type") != "DefinedTerm":
            print(
                f"[{filename}][index={idx}][id={tid}] "
                f"@type should be 'DefinedTerm', got {term.get('@type')!r}"
            )
            errors += 1

        # additionalProperty must exist and be a list
        if not isinstance(term.get("additionalProperty"), list):
            print(
                f"[{filename}][index={idx}][id={tid}] "
                "Missing or invalid 'additionalProperty' (expected an array)"
            )
            errors += 1
            # Without additionalProperty, we can't validate the rest
            continue

        # Check required conceptual fields inside additionalProperty
        for field_name in REQUIRED_PROPERTIES:
            val = get_prop(term, field_name)
            if val is None or (isinstance(val, str) and not val.strip()):
                print(
                    f"[{filename}][index={idx}][id={tid}] "
                    f"Missing or empty required field '{field_name}' "
                    f"in additionalProperty"
                )
                errors += 1

    return errors


def main(argv) -> int:
    if len(argv) < 2:
        print(
            "Usage: python scripts/validate_hcam_json.py "
            "<file1.json> [<file2.json> ...]"
        )
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

        # Case 1: file is a list of DefinedTerm objects (AI glossary)
        if isinstance(data, list):
            total_errors += validate_defined_term_list(filename, data)
            continue

        # Case 2: file is a DefinedTermSet with hasDefinedTerm[] (Equity glossary)
        if isinstance(data, dict) and data.get("@type") == "DefinedTermSet":
            terms = data.get("hasDefinedTerm")
            if not isinstance(terms, list):
                print(
                    f"[{filename}] 'hasDefinedTerm' must be a list "
                    "inside DefinedTermSet"
                )
                total_errors += 1
            else:
                total_errors += validate_defined_term_list(filename, terms)
            continue

        # Anything else is invalid root
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
