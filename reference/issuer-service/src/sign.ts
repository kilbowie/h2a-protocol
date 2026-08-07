import { sign as cryptoSign, verify as cryptoVerify } from "node:crypto";
import { jcsBytes, looksLikeDer } from "./jcs.js";

// ADR-014. Canonicalisation is RFC 8785 JCS (jcs.ts, byte-identical across every reference
// component and checked by scripts/check-jcs.py). Signatures are ES256 as RFC 7518 §3.4 defines it:
// raw fixed-width R‖S, 64 bytes, never DER.
//
// `dsaEncoding: "ieee-p1363"` is what selects raw R‖S. Node's default is DER, which is why every
// signature this repository produced before 2026-08-06 was DER while claiming `alg: "ES256"` — and
// why a conformant counterparty could not verify a single one of them.

/** Sign everything in `obj` except its singular `signature` field. Raw R‖S, base64url. */
export function signObject(privateKeyPem: string, obj: Record<string, unknown>): string {
  const { signature, ...rest } = obj;
  void signature;
  return sign(privateKeyPem, rest);
}

/**
 * Sign a grant over its canonical form MINUS the detached `signatures` array (ADR-004, ADR-014 §3).
 * The member is removed, not emptied. Both the consent and issuance signatures cover this same
 * payload; the signer's key is what differs.
 */
export function signDetached(privateKeyPem: string, obj: Record<string, unknown>): string {
  const { signatures, ...rest } = obj as { signatures?: unknown };
  void signatures;
  return sign(privateKeyPem, rest);
}

export function verifyObject(publicKeyPem: string, obj: Record<string, unknown>): boolean {
  const { signature, ...rest } = obj as { signature?: string };
  if (!signature) return false;
  try {
    const sig = Buffer.from(signature, "base64url");
    // Reject DER outright rather than transparently accepting it. A verifier that quietly takes
    // both encodings cannot tell a conformant signer from a non-conformant one, which is exactly
    // how this repository shipped DER under an ES256 label for months without noticing.
    if (looksLikeDer(sig)) return false;
    return cryptoVerify(
      "sha256",
      jcsBytes(rest),
      { key: publicKeyPem, dsaEncoding: "ieee-p1363" },
      sig,
    );
  } catch {
    return false;
  }
}

function sign(privateKeyPem: string, payload: unknown): string {
  return cryptoSign("sha256", jcsBytes(payload), {
    key: privateKeyPem,
    dsaEncoding: "ieee-p1363",
  }).toString("base64url");
}
