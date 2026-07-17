"""H2A reference verifier (v0).

Deliberately small and dependency-light. It demonstrates the check every conformant
verifier performs, in order, and emits a decision record. It is fail-closed: any error,
missing field, or expired artefact yields a REFUSED / non-conformant decision, never a permit.

This is a *reference*, not Bridle. It runs entirely outside any operator's infrastructure.
"""
from __future__ import annotations

import base64
import gzip
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

H2A_VERSION = "0.1"


# ---------- canonicalisation & signatures ----------

def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def signing_bytes(grant: dict) -> bytes:
    """Everything except the signature values is what gets signed."""
    g = json.loads(json.dumps(grant))
    g.pop("signatures", None)
    return canonical(g)


def verify_sig(pub: ec.EllipticCurvePublicKey, payload: bytes, sig_b64u: str) -> bool:
    try:
        sig = base64.urlsafe_b64decode(sig_b64u + "==")
        pub.verify(sig, payload, ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


# ---------- status list (base64url + gzip bitstring) ----------

def bitstring_encode(revoked: set[int], size: int = 1024) -> str:
    ba = bytearray((size + 7) // 8)
    for i in revoked:
        ba[i // 8] |= 1 << (i % 8)
    return base64.urlsafe_b64encode(gzip.compress(bytes(ba))).decode().rstrip("=")


def verify_status_sig(pub, status_list: dict) -> bool:
    """Verify the status list signature over everything except the signature field."""
    sl = {k: v for k, v in status_list.items() if k != "signature"}
    payload = canonical(sl)
    return verify_sig(pub, payload, status_list.get("signature", ""))


def bit_is_revoked(list_b64u: str, index: int) -> bool:
    raw = gzip.decompress(base64.urlsafe_b64decode(list_b64u + "=="))
    byte = index // 8
    if byte >= len(raw):
        return False
    return bool(raw[byte] & (1 << (index % 8)))


# ---------- verification ----------

@dataclass
class Use:
    purpose: str
    territory: str
    spend: float  # cumulative spend in the grant's lease unit


def _now():
    return datetime.now(timezone.utc)


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _record(grant_id: str, decision: str, reason: str, extra: dict | None = None) -> dict:
    rec = {
        "h2a_version": H2A_VERSION,
        "record_id": str(uuid.uuid4()),
        "grant_id": grant_id,
        "decision": decision,
        "reason_code": reason,
        "measured_latency_ms": 0,
        "created_at": _now().isoformat().replace("+00:00", "Z"),
        "alg": "ES256",
        "signature": "REF_UNSIGNED",
    }
    if extra:
        rec.update(extra)
    return rec


def verify(grant: dict, issuer_keys: dict, consent_keys: dict,
           status_list: dict, status_pubkey: ec.EllipticCurvePublicKey, use: Use) -> dict:
    """Return a decision record. issuer_keys/consent_keys map kid -> public key.

    status_pubkey is the issuer's status-list key and is required: a verifier with no
    trust anchor cannot check the list, and SPEC-CORE §4.3 has no path that permits an
    unverified one (ADR-009).
    """
    gid = grant.get("grant_id", "unknown")

    # 1. signatures — both consent and issuance must verify
    payload = signing_bytes(grant)
    sigs = {s["role"]: s for s in grant.get("signatures", [])}
    if set(sigs) != {"consent", "issuance"}:
        return _record(gid, "REFUSED_OUT_OF_SCOPE", "malformed-signatures")
    ck = consent_keys.get(sigs["consent"]["kid"])
    ik = issuer_keys.get(sigs["issuance"]["kid"])
    if not ck or not verify_sig(ck, payload, sigs["consent"]["value"]):
        return _record(gid, "REFUSED_OUT_OF_SCOPE", "consent-signature-invalid")
    if not ik or not verify_sig(ik, payload, sigs["issuance"]["value"]):
        return _record(gid, "REFUSED_OUT_OF_SCOPE", "issuance-signature-invalid")

    # 2. validity window (fail-closed on expiry)
    now = _now()
    if now < _dt(grant["nbf"]) or now > _dt(grant["exp"]):
        return _record(gid, "REFUSED_OUT_OF_SCOPE", "grant-outside-validity-window")

    # 3. status list — fetch-and-verify only (ADR-009). Fail closed on an unsigned,
    #    wrongly-signed, or stale list; the verifier never revokes and serves no list.
    if not status_list.get("signature") or not verify_status_sig(status_pubkey, status_list):
        return _record(gid, "REFUSED_REVOKED", "status-signature-invalid-fail-closed")
    if now > _dt(status_list["valid_until"]):
        return _record(gid, "REFUSED_REVOKED", "status-list-stale-fail-closed")
    if bit_is_revoked(status_list["list"], grant["status"]["index"]):
        return _record(gid, "REFUSED_REVOKED", "asset-revoked")

    # 4. scope
    scope = grant["scope"]
    if use.purpose in scope.get("exclusions", []):
        return _record(gid, "REFUSED_OUT_OF_SCOPE", f"excluded:{use.purpose}")
    if use.purpose not in scope["purposes"]:
        return _record(gid, "REFUSED_OUT_OF_SCOPE", f"purpose-not-granted:{use.purpose}")
    terr = scope.get("territories")
    if terr and "GLOBAL" not in terr and use.territory not in terr:
        return _record(gid, "REFUSED_OUT_OF_SCOPE", f"territory-not-granted:{use.territory}")

    # 5. lease
    lease = grant.get("lease")
    if lease:
        if now < _dt(lease["nbf"]) or now > _dt(lease["exp"]):
            return _record(gid, "REFUSED_LEASE_EXHAUSTED", "lease-outside-window")
        if use.spend > lease["cap"]:
            return _record(gid, "REFUSED_LEASE_EXHAUSTED", "lease-cap-exceeded")

    # all checks passed
    deleg = grant.get("delegation", {})
    return _record(gid, "PERMITTED_CONFORMANT", "in-scope", {
        "non_conformant_transmission": None,
        "effective_chain_horizon": deleg.get("effective_chain_horizon"),
        "max_chain_horizon": deleg.get("max_chain_horizon"),
    })
