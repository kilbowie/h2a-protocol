import { verify as cryptoVerify } from "node:crypto";
import { gunzipSync } from "node:zlib";
import { jcsBytes, looksLikeDer } from "./jcs.js";

// The verifier re-implements the H2A crypto conventions from scratch — it depends on NO implementer
// package (that independence is the whole point: it must be able to expose a misbehaving one), and
// it stays zero-dependency for the same reason.
//
// The conventions are the cross-implementation interop contract, and they are now written down:
// **ADR-014** makes RFC 8785 JCS the normative canonical form and `alg:"ES256"` the JOSE raw R‖S
// encoding, with `interop/vectors/vectors.json` as normative test data. `scripts/check-jcs.py` runs
// this file against those vectors.
//
// The comment this replaced claimed the output was "byte-identical to the issuer service, the
// subject signer, and an independent implementer — by specification, not by shared code". That was
// false when written: there was no specification to be identical by, and measurement on 5 August
// 2026 found four canonicalisers and two signature encodings across the estate. The sentence is now
// true, and — more usefully — it is checked.
//
// `canonical()` is gone; use `jcs()` from ./jcs.js. It sorted with `localeCompare` (locale-collated,
// never conformant) and rebuilt a JavaScript object from the sorted entries, which silently
// re-ordered integer-like keys back to the front. Two defects in eight lines, copied six times
// across the estate.

/** Verify an object carrying a singular `signature` field (status lists, decision records, attestations). */
export function verifyObject(publicKeyPem: string, obj: Record<string, unknown>): boolean {
  const { signature, ...rest } = obj as { signature?: string };
  if (!signature) return false;
  return verifyRaw(publicKeyPem, rest, signature);
}

/** Verify one DETACHED grant signature over jcs(grant minus the `signatures` array) — ADR-004, ADR-014 §3. */
export function verifyDetached(publicKeyPem: string, obj: Record<string, unknown>, value: string): boolean {
  if (!value) return false;
  const { signatures, ...rest } = obj as { signatures?: unknown };
  void signatures;
  return verifyRaw(publicKeyPem, rest, value);
}

function verifyRaw(publicKeyPem: string, payload: unknown, signatureB64u: string): boolean {
  try {
    const sig = Buffer.from(signatureB64u, "base64url");
    // A DER signature is REFUSED, not transparently accepted. Accepting both encodings would make
    // this verifier unable to tell a conformant signer from one that ignored ADR-014 — and exposing
    // exactly that is what the verifier exists for (ADR-006). Fail-closed, and specific.
    if (looksLikeDer(sig)) return false;
    return cryptoVerify(
      "sha256",
      jcsBytes(payload),
      { key: publicKeyPem, dsaEncoding: "ieee-p1363" },
      sig,
    );
  } catch {
    return false;
  }
}

/** Read one bit of a base64url gzip bitstring status list (bit set = revoked). */
export function isRevoked(listB64u: string, index: number): boolean {
  const raw = gunzipSync(Buffer.from(listB64u, "base64url"));
  const byte = index >> 3;
  if (byte >= raw.length) return false;
  return (raw[byte] & (1 << (index & 7))) !== 0;
}
