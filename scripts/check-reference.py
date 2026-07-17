#!/usr/bin/env python3
"""H2A reference implementation gate.

Runs in CI before every site deploy, alongside validate-schemas.py. That gate proves the
static examples match the schemas; this one proves the *running reference* does too — the
artefacts it actually emits, and the fail-closed rule ADR-009 turns on.

Exits non-zero if the reference emits an artefact its own schema rejects, or if a status
list signed by the wrong key is not refused.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas" / "v0"
sys.path.insert(0, str(ROOT / "reference"))

from h2a_ref.issue import make_status_list  # noqa: E402
from h2a_ref.verify import Use, signing_bytes, verify  # noqa: E402

ISS = "https://equity.example.org/h2a/issuer"


def load(p):
    return json.loads(Path(p).read_text())


def check(errors, label, schema_file, instance):
    v = Draft202012Validator(load(SCHEMA_DIR / schema_file))
    errs = sorted(v.iter_errors(instance), key=lambda e: e.path)
    if errs:
        errors.append(f"{label} FAILED {schema_file}: {errs[0].message}")
    else:
        print(f"[schema ok]   {label}")


def build_grant(now, subject_priv, issuer_priv):
    iso = lambda dt: dt.isoformat().replace("+00:00", "Z")  # noqa: E731
    from h2a_ref.demo import _sign

    grant = {
        "h2a_version": "0.1",
        "grant_id": "3f2a1c40-0d1e-4b2a-9c33-8a1b2c3d4e5f",
        "iss": ISS,
        "subject_ref": "urn:h2a:subject:jane-actor-001",
        "grantee_ref": "urn:h2a:grantee:truly-imagined",
        "scope": {"purposes": ["promotional-video"], "media_types": ["video"],
                  "territories": ["GB", "US"], "exclusions": ["political", "adult"]},
        "profiles": ["h2a-media"],
        "lease": {"cap": 500, "unit": "usd", "provider_agnostic": True,
                  "nbf": iso(now), "exp": iso(now + timedelta(days=90))},
        "status": {"uri": f"{ISS}/status/2026-q3.json", "mirrors": [], "index": 42},
        "revocation_horizon": "PT30M",
        "delegation": {"parent": None, "depth": 0,
                       "effective_chain_horizon": "PT30M", "max_chain_horizon": "PT1H"},
        "alg": "ES256",
        "iat": iso(now), "nbf": iso(now), "exp": iso(now + timedelta(days=90)),
    }
    payload = signing_bytes(grant)
    grant["signatures"] = [
        {"role": "consent", "kid": "subject-key-1", "value": _sign(subject_priv, payload)},
        {"role": "issuance", "kid": "issuer-key-1", "value": _sign(issuer_priv, payload)},
    ]
    return grant


def main():
    errors = []
    now = datetime.now(timezone.utc)

    subject_priv = ec.generate_private_key(ec.SECP256R1())
    issuer_priv = ec.generate_private_key(ec.SECP256R1())
    status_priv = ec.generate_private_key(ec.SECP256R1())
    status_pubkey = status_priv.public_key()

    grant = build_grant(now, subject_priv, issuer_priv)
    issuer_keys = {"issuer-key-1": issuer_priv.public_key()}
    consent_keys = {"subject-key-1": subject_priv.public_key()}

    # 1. the grant the reference issues matches the grant schema
    check(errors, "reference grant", "h2a-core.grant.schema.json", grant)

    # 2. the status list the issuer emits matches the status-list schema
    live = make_status_list(status_priv, set(), ISS, now)
    revoked = make_status_list(status_priv, {42}, ISS, now)
    check(errors, "issued status list (live)", "h2a-core.status-list.schema.json", live)
    check(errors, "issued status list (revoked)", "h2a-core.status-list.schema.json", revoked)

    # 3. every decision record the verifier emits matches the decision-record schema,
    #    and each scenario yields the decision SPEC-CORE §4.3 requires
    scenarios = [
        ("in-scope live", live, Use("promotional-video", "GB", 100), "PERMITTED_CONFORMANT", None),
        ("out-of-scope", live, Use("political-ad", "GB", 100), "REFUSED_OUT_OF_SCOPE", None),
        ("revoked", revoked, Use("promotional-video", "GB", 100), "REFUSED_REVOKED", "asset-revoked"),
    ]
    for label, sl, use, want, want_reason in scenarios:
        rec = verify(grant, issuer_keys, consent_keys, sl, status_pubkey, use)
        check(errors, f"decision record ({label})", "h2a-core.decision-record.schema.json", rec)
        if rec["decision"] != want:
            errors.append(f"{label}: expected {want}, got {rec['decision']} ({rec['reason_code']})")
        elif want_reason and rec["reason_code"] != want_reason:
            errors.append(f"{label}: expected reason {want_reason}, got {rec['reason_code']}")
        else:
            print(f"[decision ok] {label} -> {rec['decision']}")

    # 4. ADR-009 fail-closed: a list signed by anyone but the issuer MUST be refused.
    #    This is the check that makes the authority split real rather than declared.
    impostor = ec.generate_private_key(ec.SECP256R1())
    forged = make_status_list(impostor, set(), ISS, now)
    rec = verify(grant, issuer_keys, consent_keys, forged, status_pubkey,
                 Use("promotional-video", "GB", 100))
    if rec["decision"] != "REFUSED_REVOKED" or rec["reason_code"] != "status-signature-invalid-fail-closed":
        errors.append("FAIL-OPEN: wrongly-signed status list was not refused "
                      f"(got {rec['decision']} / {rec['reason_code']})")
    else:
        print("[fail-closed] wrongly-signed status list correctly refused")

    # 5. an unsigned list MUST also be refused (SPEC-CORE §4.3)
    unsigned = {k: v for k, v in live.items() if k != "signature"}
    rec = verify(grant, issuer_keys, consent_keys, unsigned, status_pubkey,
                 Use("promotional-video", "GB", 100))
    if rec["decision"] != "REFUSED_REVOKED":
        errors.append(f"FAIL-OPEN: unsigned status list was not refused (got {rec['decision']})")
    else:
        print("[fail-closed] unsigned status list correctly refused")

    if errors:
        print("\nREFERENCE CHECK FAILED:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 1
    print("\nReference implementation conformant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
