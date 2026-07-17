#!/usr/bin/env python3
"""Cross-language interop gate: the TypeScript issuer signs, the Python verifier verifies.

ADR-009 makes the status-list signature the proof of the authority split, so it only holds
if *any* conformant implementation can verify what the issuer signed. `interop-emit.ts` drives
the real HTTP service and dumps its signed lists + public key; this script feeds them through
the Python reference verifier and asserts they check out, tamper is caught, and a TS-signed
revoked list drives the verifier to REFUSED_REVOKED.

Usage: python scripts/check-interop.py <dir-with-emitted-artefacts>
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas" / "v0"
sys.path.insert(0, str(ROOT / "reference"))

from h2a_ref.verify import (  # noqa: E402
    Use, bit_is_revoked, signing_bytes, verify, verify_status_sig,
)

ISS = "https://equity.example.org/h2a/issuer"


def build_grant(now):
    """A grant whose only refusal path is the revocation bit at status.index 42."""
    from cryptography.hazmat.primitives import hashes
    iso = lambda dt: dt.isoformat().replace("+00:00", "Z")  # noqa: E731
    subject = ec.generate_private_key(ec.SECP256R1())
    issuer = ec.generate_private_key(ec.SECP256R1())

    def sign(priv, payload):
        import base64
        return base64.urlsafe_b64encode(
            priv.sign(payload, ec.ECDSA(hashes.SHA256()))).decode().rstrip("=")

    grant = {
        "h2a_version": "0.1",
        "grant_id": "3f2a1c40-0d1e-4b2a-9c33-8a1b2c3d4e5f",
        "iss": ISS,
        "subject_ref": "urn:h2a:subject:jane-actor-001",
        "grantee_ref": "urn:h2a:grantee:truly-imagined",
        "scope": {"purposes": ["promotional-video"], "media_types": ["video"],
                  "territories": ["GB", "US"], "exclusions": ["political"]},
        "profiles": ["h2a-media"],
        "lease": {"cap": 500, "unit": "usd", "provider_agnostic": True,
                  "nbf": iso(now), "exp": iso(now + timedelta(days=90))},
        "status": {"uri": f"{ISS}/status/x.json", "mirrors": [], "index": 42},
        "revocation_horizon": "PT30M",
        "delegation": {"parent": None, "depth": 0,
                       "effective_chain_horizon": "PT30M", "max_chain_horizon": "PT1H"},
        "alg": "ES256",
        "iat": iso(now), "nbf": iso(now), "exp": iso(now + timedelta(days=90)),
    }
    payload = signing_bytes(grant)
    grant["signatures"] = [
        {"role": "consent", "kid": "subject-key-1", "value": sign(subject, payload)},
        {"role": "issuance", "kid": "issuer-key-1", "value": sign(issuer, payload)},
    ]
    return grant, {"issuer-key-1": issuer.public_key()}, {"subject-key-1": subject.public_key()}


def main():
    outdir = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    errors = []

    pub = load_pem_public_key(json.loads((outdir / "pubkey.json").read_text())["publicKeyPem"].encode())
    live = json.loads((outdir / "status-live.json").read_text())
    revoked = json.loads((outdir / "status-revoked.json").read_text())

    schema = Draft202012Validator(load_json(SCHEMA_DIR / "h2a-core.status-list.schema.json"))

    # 1. what the TS service emits matches the status-list schema
    for label, sl in [("live", live), ("revoked", revoked)]:
        errs = sorted(schema.iter_errors(sl), key=lambda e: e.path)
        if errs:
            errors.append(f"TS {label} list fails schema: {errs[0].message}")
        else:
            print(f"[schema ok]   TS-issued {label} list")

    # 2. the core interop claim: a TS ES256 signature verifies under the Python verifier
    for label, sl in [("live", live), ("revoked", revoked)]:
        if verify_status_sig(pub, sl):
            print(f"[interop ok]  TS signature verifies in Python ({label})")
        else:
            errors.append(f"TS {label} list signature did NOT verify in Python")

    # 3. the revoked bit the TS service set is the one the Python verifier reads
    if bit_is_revoked(revoked["list"], 42):
        print("[bit ok]      index 42 revoked in TS revoked list")
    else:
        errors.append("index 42 not set in TS revoked list")
    if not bit_is_revoked(live["list"], 42):
        print("[bit ok]      index 42 clear in TS live list")
    else:
        errors.append("index 42 unexpectedly set in TS live list")

    # 4. tamper detection across the boundary — mutate a field, signature must fail
    tampered = dict(live)
    tampered["iss"] = "https://evil.example/issuer"
    if verify_status_sig(pub, tampered):
        errors.append("tampered TS list still verified — forgery not caught")
    else:
        print("[interop ok]  tampered TS list correctly rejected")

    # 5. end-to-end: a TS-signed list drives the Python verifier to the right decision
    now = datetime.now(timezone.utc)
    grant, issuer_keys, consent_keys = build_grant(now)
    r_live = verify(grant, issuer_keys, consent_keys, live, pub, Use("promotional-video", "GB", 100))
    r_rev = verify(grant, issuer_keys, consent_keys, revoked, pub, Use("promotional-video", "GB", 100))
    if r_live["decision"] != "PERMITTED_CONFORMANT":
        errors.append(f"live list: expected PERMITTED_CONFORMANT, got {r_live['decision']} ({r_live['reason_code']})")
    else:
        print("[decision ok] TS live list -> PERMITTED_CONFORMANT")
    if r_rev["decision"] != "REFUSED_REVOKED" or r_rev["reason_code"] != "asset-revoked":
        errors.append(f"revoked list: expected REFUSED_REVOKED/asset-revoked, got {r_rev['decision']}/{r_rev['reason_code']}")
    else:
        print("[decision ok] TS revoked list -> REFUSED_REVOKED")

    if errors:
        print("\nINTEROP CHECK FAILED:", file=sys.stderr)
        for e in errors:
            print("  - " + e, file=sys.stderr)
        return 1
    print("\nCross-language interop conformant.")
    return 0


def load_json(p):
    return json.loads(Path(p).read_text())


if __name__ == "__main__":
    sys.exit(main())
