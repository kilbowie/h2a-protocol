"""End-to-end reference demo.

Generates keys, issues and double-signs a grant, builds a status list, then runs three
checks through the reference verifier and prints the resulting decision records:

  1. in-scope, not revoked   -> PERMITTED_CONFORMANT
  2. out-of-scope purpose     -> REFUSED_OUT_OF_SCOPE
  3. after revocation         -> REFUSED_REVOKED

Run: python -m h2a_ref.demo   (from the reference/ directory)
"""
from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes

from h2a_ref.issue import make_status_list
from h2a_ref.verify import Use, signing_bytes, verify


def _sign(priv, payload: bytes) -> str:
    sig = priv.sign(payload, ec.ECDSA(hashes.SHA256()))
    return base64.urlsafe_b64encode(sig).decode().rstrip("=")


def main() -> None:
    now = datetime.now(timezone.utc)
    iso = lambda dt: dt.isoformat().replace("+00:00", "Z")

    subject_priv = ec.generate_private_key(ec.SECP256R1())
    issuer_priv = ec.generate_private_key(ec.SECP256R1())
    status_priv = ec.generate_private_key(ec.SECP256R1())  # the issuer's status-list signing key

    grant = {
        "h2a_version": "0.1",
        "grant_id": "3f2a1c40-0d1e-4b2a-9c33-8a1b2c3d4e5f",
        "iss": "https://issuer.example.org/h2a/issuer",
        "subject_ref": "urn:h2a:subject:jane-actor-001",
        "grantee_ref": "urn:h2a:grantee:example-operator",
        "scope": {
            "purposes": ["promotional-video"],
            "media_types": ["video"],
            "territories": ["GB", "US"],
            "exclusions": ["political", "adult", "defamatory"],
        },
        "profiles": ["h2a-media"],
        "lease": {"cap": 500, "unit": "usd", "provider_agnostic": True,
                  "nbf": iso(now), "exp": iso(now + timedelta(days=90))},
        "status": {"uri": "https://issuer.example.org/h2a/status/2026-q3.json",
                   "mirrors": [], "index": 42},
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

    issuer_keys = {"issuer-key-1": issuer_priv.public_key()}
    consent_keys = {"subject-key-1": subject_priv.public_key()}

    # the issuer signs the list — the only component that can revoke (ADR-009)
    status_pubkey = status_priv.public_key()
    live = make_status_list(status_priv, set(), grant["iss"], now)       # nothing revoked
    revoked = make_status_list(status_priv, {42}, grant["iss"], now)     # this grant revoked

    print("=== 1. in-scope, live ===")
    r = verify(grant, issuer_keys, consent_keys, live, status_pubkey,
               Use("promotional-video", "GB", 100))
    print(json.dumps({"decision": r["decision"], "reason": r["reason_code"]}, indent=2))

    print("\n=== 2. out-of-scope purpose ===")
    r = verify(grant, issuer_keys, consent_keys, live, status_pubkey,
               Use("political-ad", "GB", 100))
    print(json.dumps({"decision": r["decision"], "reason": r["reason_code"]}, indent=2))

    print("\n=== 3. after revocation ===")
    r = verify(grant, issuer_keys, consent_keys, revoked, status_pubkey,
               Use("promotional-video", "GB", 100))
    print(json.dumps({"decision": r["decision"], "reason": r["reason_code"]}, indent=2))


if __name__ == "__main__":
    main()
