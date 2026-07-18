import { createSign, generateKeyPairSync } from "node:crypto";

// Reference "subject signer" — stands in for the performer's own device during a consent ceremony.
// It is deliberately self-contained: a subject does NOT depend on the issuer's code or keys. It holds
// its OWN private key and produces only the `consent` half of a grant's two detached signatures
// (ADR-004). The real consent-capture ceremony (ADR-007) is a Sprint 6 concern; this is the crypto.

// Deterministic stable stringify (deep-sorted keys) — the cross-implementation interop convention,
// byte-identical to the issuer service and to Bridle's verifier.
function canonical(obj: unknown): string {
  return JSON.stringify(obj, (_k, v) =>
    v && typeof v === "object" && !Array.isArray(v)
      ? Object.fromEntries(Object.entries(v).sort(([a], [b]) => a.localeCompare(b)))
      : v,
  );
}

export interface SubjectKeypair {
  privateKeyPem: string;
  publicKeyPem: string;
  kid: string;
}

// Generate a fresh EC P-256 keypair for a subject. `handle` seeds a stable, human-readable kid.
export function newSubjectKeypair(handle: string): SubjectKeypair {
  const { privateKey, publicKey } = generateKeyPairSync("ec", { namedCurve: "P-256" });
  return {
    privateKeyPem: privateKey.export({ type: "pkcs8", format: "pem" }).toString(),
    publicKeyPem: publicKey.export({ type: "spki", format: "pem" }).toString(),
    kid: `urn:h2a:subject:${handle}#consent`,
  };
}

// Produce the `consent` signature over the grant's canonical form MINUS the `signatures` array —
// the same payload the issuer signs for issuance, so a verifier checks both against one canonicalisation.
export function signConsent(
  key: SubjectKeypair,
  grant: Record<string, unknown>,
): { role: "consent"; kid: string; value: string } {
  const { signatures, ...rest } = grant as { signatures?: unknown };
  void signatures;
  const s = createSign("SHA256");
  s.update(canonical(rest));
  s.end();
  return { role: "consent", kid: key.kid, value: s.sign(key.privateKeyPem).toString("base64url") };
}
