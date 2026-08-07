import { sign as cryptoSign } from "node:crypto";
import { jcsBytes } from "./jcs.js";

// ADR-014. Canonicalisation is RFC 8785 JCS and signatures are ES256 as RFC 7518 §3.4 defines it —
// raw fixed-width R‖S, 64 bytes, never DER.
//
// The witness shares no code with the issuer or the implementer beyond this convention, and that
// independence is the point (ADR-005). But "shares only a convention" is a claim, and until
// 2026-08-06 it was a false one: the convention was written down nowhere, so four implementations
// drifted apart while each believed it was the reference. ADR-014 is the convention, and
// interop/vectors/ is how the witness proves it still follows it — see scripts/check-jcs.py.

/** Sign an object over its canonical form minus its singular `signature` field. */
export function signObject(privateKeyPem: string, obj: Record<string, unknown>): string {
  const { signature, ...rest } = obj as { signature?: unknown };
  void signature;
  return cryptoSign("sha256", jcsBytes(rest), {
    key: privateKeyPem,
    dsaEncoding: "ieee-p1363",
  }).toString("base64url");
}
