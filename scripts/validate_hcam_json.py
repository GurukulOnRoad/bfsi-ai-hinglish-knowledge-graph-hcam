import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple

# --------- CONFIG: WHICH FILES TO VALIDATE ---------
BASE_DIR = Path(__file__).resolve().parent.parent

FILES_TO_VALIDATE = [
    "bharat-ai-education-hindi-ai-glossary-hcam-knowledge-graph.json",
    "equity-derivatives-hcam-viii.json",
]

DATA_DIR = BASE_DIR  # files are at repo root; change if in /data


# --------- SCHEMAS FOR EACH FILE TYPE ---------
class Schema:
    def __init__(
        self,
        name: str,
        required_fields: List[str],
        id_prefix: str | None = None,
        domain_field: str | None = None,
        allowed_domains: List[str] | None = None,
        allow_related: bool = True,
    ):
        self.name = name
        self.required_fields = required_fields
        self.id_prefix = id_prefix
        self.domain_field = domain_field
        self.allowed_domains = allowed_domains
        self.allow_related = allow_related


AI_GLOSSARY_SCHEMA = Schema(
    name="AI Glossary (HCAM-KG)",
    required_fields=[
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
        "mental_anchor",
        "exam_mnemonic",
        "use_case_example",
        "exam_mapping",
        "regulatory_reference",
        "ai_use_case",
        "prompt_example",
        "related_concepts",
        "broader_concept",
        "narrower_concept",
        "prerequisite_concept",
    ],
    id_prefix="hacm_bharat_ai_",
    domain_field="domain",
    allowed_domains=["AI Literacy", "AI Ethics"],
    allow_related=True,
)

EQD_GLOSSARY_SCHEMA = Schema(
    name="Equity Derivatives HCAM-KG (NISM VIII)",
    required_fields=[
        "id",
        "bfsieqd_domain",
        "pillar",
        "topic_cluster",
        "label_en",
        "label_hi",
        "label_hiLatn",
        "def_en",
        "def_hi",
        "def_hiLatn_explainer",
        "mental_anchor",
        "exam_mnemonic",
        "use_case_example",
        "exam_mapping",
        "regulatory_reference",
        # NOTE: If later you add ai_use_case/prompt_example to EQD,
        # add them here as required fields.
    ],
    id_prefix="bfsieqd_",
    domain_field="bfsieqd_domain",
    allowed_domains=["BFSI"],
    allow_related=True,
)


SCHEMA_BY_FILENAME: Dict[str, Schema] = {
    "bharat-ai-education-hindi-ai-glossary-hcam-knowledge-graph.json": AI_GLOSSARY_SCHEMA,
    "equity-derivatives-hcam-viii.json": EQD_GLOSSARY_SCHEMA,
}


# --------- VALIDATION HELPERS ---------
def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_required_fields(
    schema: Schema,
    term: Dict[str, Any],
    errors: List[str],
    filename: str,
):
    for field in schema.required_fields:
        if field not in term:
            errors.append(
                f"[{filename}][id={term.get('id')}] Missing required field '{field}'"
            )
        else:
            if field == "related_concepts":
                if not isinstance(term[field], list):
                    errors.append(
                        f"[{filename}][id={term.get('id')}] 'related_concepts' must be a list"
                    )


def validate_id_prefix(
    schema: Schema,
    term: Dict[str, Any],
    errors: List[str],
    filename: str,
):
    if not schema.id_prefix:
        return
    term_id = term.get("id")
    if not isinstance(term_id, str):
        errors.append(f"[{filename}] Term has non-string id: {term_id!r}")
        return
    if not term_id.startswith(schema.id_prefix):
        errors.append(
            f"[{filename}][id={term_id}] Expected id to start with '{schema.id_prefix}'"
        )


def validate_domain(
    schema: Schema,
    term: Dict[str, Any],
    errors: List[str],
    filename: str,
):
    if not schema.domain_field:
        return
    df = schema.domain_field
    if df not in term:
        errors.append(
            f"[{filename}][id={term.get('id')}] Missing domain field '{df}'"
        )
        return
    if schema.allowed_domains:
        val = term[df]
        if val not in schema.allowed_domains:
            errors.append(
                f"[{filename}][id={term.get('id')}] Invalid {df} '{val}'. "
                f"Allowed: {schema.allowed_domains}"
            )


def validate_unique_ids(
    filename: str, terms: List[Dict[str, Any]], errors: List[str]
):
    seen: Dict[str, int] = {}
    for idx, term in enumerate(terms):
        tid = term.get("id")
        if not isinstance(tid, str):
            errors.append(f"[{filename}] Term #{idx} has invalid id: {tid!r}")
            continue
        if tid in seen:
            errors.append(
                f"[{filename}] Duplicate id '{tid}' at positions {seen[tid]} and {idx}"
            )
        else:
            seen[tid] = idx


def validate_related_concepts_exist(
    schema: Schema,
    filename: str,
    terms: List[Dict[str, Any]],
    errors: List[str],
):
    if not schema.allow_related:
        return
    id_set = {t.get("id") for t in terms if isinstance(t.get("id"), str)}
    for term in terms:
        tid = term.get("id")
        rel = term.get("related_concepts", [])
        if not isinstance(rel, list):
            continue
        for r in rel:
            if isinstance(r, str) and r not in id_set:
                # Only warn if clearly an internal reference; if you plan cross-file links,
                # you can later relax this and treat as WARNING instead of error.
                errors.append(
                    f"[{filename}][id={tid}] related_concept '{r}' not found in this file"
                )


def validate_file(path: Path, schema: Schema) -> Tuple[int, List[str]]:
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

    # Per-term checks
    for term in data:
        if not isinstance(term, dict):
            errors.append(f"[{filename}] Term is not an object: {term!r}")
            continue
        validate_required_fields(schema, term, errors, filename)
        validate_id_prefix(schema, term, errors, filename)
        validate_domain(schema, term, errors, filename)

    # Cross-term checks
    validate_unique_ids(filename, data, errors)
    validate_related_concepts_exist(schema, filename, data, errors)

    return len(errors), errors


def main() -> int:
    total_errors = 0
    all_messages: List[str] = []

    print("=== HCAM-KG JSON Validation ===")
    for fname in FILES_TO_VALIDATE:
        schema = SCHEMA_BY_FILENAME.get(fname)
        if not schema:
            print(f"Skipping {fname}: no schema configured.")
            continue

        path = DATA_DIR / fname
        if not path.exists():
            all_messages.append(f"[{fname}] File not found at {path}")
            total_errors += 1
            continue

        print(f"\nValidating {fname} using schema: {schema.name}")
        count, messages = validate_file(path, schema)
        total_errors += count
        all_messages.extend(messages)

        if count == 0:
            print(f"✅ {fname}: OK")
        else:
            print(f"❌ {fname}: {count} error(s)")

    if total_errors > 0:
        print("\n--- Validation Errors ---")
        for msg in all_messages:
            print(msg)

        print(f"\nValidation FAILED with {total_errors} error(s).")
        return 1

    print("\nAll files validated successfully. ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
