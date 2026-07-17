"""Issuer-side status-list construction (v0).

This is the *issuer / fiduciary* half of the reference: it holds the signing key and is
therefore the revocation authority (ADR-009). Revocation is one operation — set the bit,
re-sign, publish. A verifier never calls this; it only fetches and verifies the result.

The artefact produced here is the same shape the TypeScript reference issuer
(`reference/issuer-service/`) serves, and it validates against
`schemas/v0/h2a-core.status-list.schema.json`. `scripts/check-reference.py` enforces both.
"""
from __future__ import annotations

import base64
import uuid
from datetime import datetime, timedelta

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from h2a_ref.verify import H2A_VERSION, bitstring_encode, canonical

# Short TTL: a status list is a perishable claim, not a cached document.
DEFAULT_TTL = timedelta(minutes=30)


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def make_status_list(status_priv: ec.EllipticCurvePrivateKey, revoked: set[int], iss: str,
                     now: datetime, ttl: timedelta = DEFAULT_TTL,
                     mirrors: list[str] | None = None) -> dict:
    """Build and sign a conformant status list. `revoked` is the set of set bits."""
    sl = {
        "h2a_version": H2A_VERSION,
        "status_list_id": str(uuid.uuid4()),
        "iss": iss,
        "purpose": "revocation",
        "encoding": "base64url-bitstring",
        "list": bitstring_encode(set(revoked)),
        "valid_from": _iso(now),
        "valid_until": _iso(now + ttl),
        "alg": "ES256",
    }
    if mirrors:
        sl["mirrors"] = mirrors
    # The signature covers every field except itself — see verify.verify_status_sig.
    sig = status_priv.sign(canonical(sl), ec.ECDSA(hashes.SHA256()))
    sl["signature"] = base64.urlsafe_b64encode(sig).decode().rstrip("=")
    return sl
