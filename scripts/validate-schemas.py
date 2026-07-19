#!/usr/bin/env python3
"""H2A schema + example validation gate.

Runs in CI before every site deploy. Exits non-zero if any schema is malformed,
any positive example fails, or any negative example is (wrongly) accepted.
"""
import json
import sys
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas" / "v0"
EX = SCHEMA_DIR / "examples"

# example file -> schema file
POSITIVE = {
    "grant.valid.json": "h2a-core.grant.schema.json",
    "attestation.valid.json": "h2a-core.attestation.schema.json",
    "decision-record.conformant.json": "h2a-core.decision-record.schema.json",
    "decision-record.non-conformant.json": "h2a-core.decision-record.schema.json",
    "status-list.valid.json": "h2a-core.status-list.schema.json",
    "media.valid.json": "h2a-media.profile.schema.json",
    "memory.derived.valid.json": "h2a-memory.profile.schema.json",
    "commercial.valid.json": "h2a-commercial.profile.schema.json",
    "loss-event.valid.json": "h2a-loss-event.schema.json",
}
# example file -> schema it MUST fail against
NEGATIVE = {
    "memory.derived.INVALID.json": "h2a-memory.profile.schema.json",
    "decision-record.INVALID.json": "h2a-core.decision-record.schema.json",
    "commercial.INVALID.json": "h2a-commercial.profile.schema.json",
}


def load(p):
    return json.loads(Path(p).read_text())


def main():
    errors = []

    # 1. schemas are themselves valid Draft 2020-12
    schemas = sorted(SCHEMA_DIR.glob("*.json"))
    if not schemas:
        print("no schemas found", file=sys.stderr)
        return 1
    for s in schemas:
        try:
            Draft202012Validator.check_schema(load(s))
            print(f"[schema ok]   {s.name}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"malformed schema {s.name}: {e}")

    # 2. positive examples validate
    for ex, sch in POSITIVE.items():
        v = Draft202012Validator(load(SCHEMA_DIR / sch))
        errs = sorted(v.iter_errors(load(EX / ex)), key=lambda e: e.path)
        if errs:
            errors.append(f"positive example {ex} FAILED: {errs[0].message}")
        else:
            print(f"[positive ok] {ex}")

    # 3. negative examples MUST reject
    for ex, sch in NEGATIVE.items():
        v = Draft202012Validator(load(SCHEMA_DIR / sch))
        if v.is_valid(load(EX / ex)):
            errors.append(f"negative example {ex} was ACCEPTED but must reject")
        else:
            print(f"[negative ok] {ex} correctly rejected")

    if errors:
        print("\nVALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 1
    print("\nAll schemas and examples valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
