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
# example file -> (schema it MUST fail against, substring that MUST appear in the failure, why)
#
# The third element is not documentation, it is the assertion. "It rejected" is a weak claim: a
# negative example that happens to be malformed in some unrelated way also rejects, and then the
# guard you meant to test is untested while the suite stays green. Every schema here has
# additionalProperties:false, so merely adding an explanatory key to one of these files would make
# it reject for that key — which is how a negative example quietly stops testing anything.
#
# Requiring the failure MESSAGE to match pins each example to the defect it exists to catch.
NEGATIVE = {
    "memory.derived.INVALID.json": (
        "h2a-memory.profile.schema.json", None,
        "pre-existing",
    ),
    "decision-record.INVALID.json": (
        "h2a-core.decision-record.schema.json", None,
        "pre-existing",
    ),
    "commercial.INVALID.json": (
        "h2a-commercial.profile.schema.json", None,
        "pre-existing",
    ),
    "grant.two-consent.INVALID.json": (
        # BOTH halves, not either: too many consent signatures AND no issuance signature. Matching
        # only one would let a future schema edit satisfy half the rule and still look tested.
        "h2a-core.grant.schema.json",
        ["Too many items match", "does not contain items matching"],
        "Two consent signatures and no issuance. Before role distinctness was enforced this "
        "VALIDATED: minItems/maxItems counted signatures without constraining their roles, so the "
        "issuer's co-signature could be absent while the grant still looked well-formed. That is "
        "the collapse of consent and issuance into one act which ADR-004 separates them to prevent.",
    ),
    "grant.no-nbf.INVALID.json": (
        "h2a-core.grant.schema.json", "'nbf' is a required property",
        "No nbf. A verifier cannot decide whether the grant is yet in force, so it is schema-valid "
        "and un-evaluable. Implementations already rejected it (bridle packages/core/src/verify.ts); "
        "the schema was the one permitting it.",
    ),
    "attestation.INVALID.json": (
        "h2a-core.attestation.schema.json", "'unit' is a required property",
        "use.spend carries an amount but no unit. A spend with no unit cannot be compared to the "
        "grant's lease cap, so it cannot decide whether the lease was exhausted.",
    ),
    "status-list.INVALID.json": (
        "h2a-core.status-list.schema.json", "'valid_until' is a required property",
        "No valid_until. A status list without an expiry can never be judged stale, so a verifier "
        "caching it has no basis to refetch — freshness becomes unfalsifiable and revocation "
        "silently stops propagating.",
    ),
    "media.INVALID.json": (
        "h2a-media.profile.schema.json", "'content_hash' is a required property",
        "asset.content_hash absent. Nothing binds the profile to the bytes that were produced, so "
        "the asset it describes cannot be identified.",
    ),
    "loss-event.INVALID.json": (
        "h2a-loss-event.schema.json", "is not one of",
        "event_type 'escalated' is outside the enum. Named after the ESCALATED decision value "
        "removed from the decision record in this same change: it had semantics nowhere, and an "
        "undefined value must not be admissible here either.",
    ),
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

    # 3. negative examples MUST reject — and, where declared, FOR THE STATED REASON
    for ex, (sch, expect, _why) in NEGATIVE.items():
        v = Draft202012Validator(load(SCHEMA_DIR / sch))
        errs = sorted(v.iter_errors(load(EX / ex)), key=lambda e: list(e.path))
        if not errs:
            errors.append(f"negative example {ex} was ACCEPTED but must reject")
            continue
        if expect is None:
            print(f"[negative ok] {ex} correctly rejected")
            continue
        messages = [e.message for e in errs]
        wanted = [expect] if isinstance(expect, str) else list(expect)
        missing = [w for w in wanted if not any(w in m for m in messages)]
        if not missing:
            print(f"[negative ok] {ex} rejected for the stated reason")
        else:
            expect = missing
            # Rejected, but not for the reason the example exists to prove — so the guard under
            # test is untested and this would otherwise have passed silently.
            errors.append(
                f"negative example {ex} rejected for the WRONG reason.\n"
                f"      expected the failure to mention: {expect!r}\n"
                f"      actual failures: {messages}"
            )

    # 4. every schema must have at least one negative example (W11.2)
    covered = {sch for sch, _e, _w in NEGATIVE.values()}
    for s in schemas:
        if s.name not in covered:
            errors.append(
                f"schema {s.name} has NO negative example. A schema only tested with objects that "
                f"should pass proves nothing about what it refuses."
            )

    if errors:
        print("\nVALIDATION FAILED:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 1
    print("\nAll schemas and examples valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
