import { createVerify } from "node:crypto";
import { gunzipSync } from "node:zlib";

// The verifier re-implements the H2A crypto conventions from scratch — it depends on NO implementer
// package (that independence is the whole point: it must be able to expose a misbehaving one). The
// conventions are the cross-implementation interop contract: deep-sorted-key JSON, SHA256, ECDSA
// P-256 (ES256), base64url. They are byte-identical to the issuer service, the subject signer, and
// Bridle — by specification, not by shared code.

export function canonical(obj: unknown): string {
  return JSON.stringify(obj, (_k, v) =>
    v && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b)))
      : v,
  );
}

// Verify an object carrying a singular `signature` field (status lists, decision records, attestations).
export function verifyObject(publicKeyPem: string, obj: Record<string, unknown>): boolean {
  const { signature, ...rest } = obj as { signature?: string };
  if (!signature) return false;
  try {
    const v = createVerify("SHA256");
    v.update(canonical(rest));
    v.end();
    return v.verify(publicKeyPem, Buffer.from(signature, "base64url"));
  } catch {
    return false;
  }
}

// Verify one DETACHED grant signature over canonical(grant minus the `signatures` array) (ADR-004).
export function verifyDetached(publicKeyPem: string, obj: Record<string, unknown>, value: string): boolean {
  if (!value) return false;
  const { signatures, ...rest } = obj as { signatures?: unknown };
  void signatures;
  try {
    const v = createVerify("SHA256");
    v.update(canonical(rest));
    v.end();
    return v.verify(publicKeyPem, Buffer.from(value, "base64url"));
  } catch {
    return false;
  }
}

// Read one bit of a base64url gzip bitstring status list (bit set = revoked).
export function isRevoked(listB64u: string, index: number): boolean {
  const raw = gunzipSync(Buffer.from(listB64u, "base64url"));
  const byte = index >> 3;
  if (byte >= raw.length) return false;
  return (raw[byte] & (1 << (index & 7))) !== 0;
}
