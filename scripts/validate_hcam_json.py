import json
import sys
from pathlib import Path

# Only these 10 fields are treated as REQUIRED
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

def flatten_term(raw_term):
    """
    Convert a JSON-LD DefinedTerm into a flat HCAM dict
    so we can validate required fields consistently.
    Works for both AI & Equity files.
    """
    flat = {}

    # ID: prefer explicit 'id', else derive from '@id'
    if "id" in raw_term and raw_term["id"]:
        flat["id"] = raw_term["id"]
    elif raw_term.get("@id"):
        rid = raw_term["@id"]
        flat["id"] = rid.split("#")[-1] if "#" in rid else rid

    # English label: prefer 'label_en', else 'name'
    if "label_en" in raw_term:
        flat["label_en"] = raw_term["label_en"]
    elif raw_term.get("name"):
        flat["label_en"] = raw_term["name"]

    # Hindi + Hinglish labels from alternateName if needed
    alt = raw_term.get("alternateName")
    if isinstance(alt, list):
        if len(alt) > 0 and "label_hi" not in flat:
            flat["label_hi"] = alt[0]
        if len(alt) > 1 and "label_hiLatn" not in flat:
            flat["label_hiLatn"] = alt[1]
    elif isinstance(alt, str):
        flat.setdefault("label_hi", alt)

    # English definition: prefer 'def_en', else 'description'
    if "def_en" in raw_term:
        flat["def_en"] = raw_term["def_en"]
    elif raw_term.get("description"):
        flat["def_en"] = raw_term["description"]

    # Pull all HCAM props from additionalProperty[]
    for prop in raw_term.get("additionalProperty", []):
        name = prop.get("name")
        value = prop.get("value")
        if name and value is not None:
            flat[name] = value

    # Domain aliasing (Equity uses 'domain' already; this is future-proof)
    if "domain" not in flat and "hacm_bfsieqd_domain" in flat:
        flat["domain"] = flat["hacm_bfsieqd_domain"]

    return flat

def load_terms(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Shape 1: Bharat AI → [ {DefinedTerm}, … ]
    if isinstance(data, list):
        return data

    # Shape 2: Equity → { "@type": "DefinedTermSet", "hasDefinedTerm": [ … ] }
    if isinstance(data, dict) and "hasDefinedTerm" in data:
        return data["hasDefinedTerm"]

    print(f"[{path.name}] Root JSON must be a list of DefinedTerm objects or a DefinedTermSet.hasDefinedTerm array.")
    return None

def validate_file(path: Path):
    terms = load_terms(path)
    if terms is None:
        return 1

    errors = 0
    for raw_term in terms:
        flat = flatten_term(raw_term)
        term_id = flat.get("id", "UNKNOWN")

        for field in REQUIRED_FIELDS:
            # domain is just another required field now (after aliasing above)
            value = flat.get(field)
            if value is None or (isinstance(value, str) and not value.strip()):
                print(f"[{path.name}][id={term_id}] Missing or invalid required field '{field}'")
                errors += 1

    if errors == 0:
        print(f"[{path.name}] ✅ Validation PASSED for {len(terms)} terms.")
    else:
        print(f"[{path.name}] ❌ Validation FAILED with {errors} error(s).")

    return 1 if errors else 0

def main():
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        print("No files passed to validator.")
        sys.exit(1)

    exit_code = 0
    for p in paths:
        exit_code |= validate_file(p)

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
