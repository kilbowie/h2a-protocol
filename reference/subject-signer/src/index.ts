import { sign as cryptoSign, generateKeyPairSync } from "node:crypto";
import { jcsBytes } from "./jcs.js";

// Reference "subject signer" — stands in for the performer's own device during a consent ceremony.
// It is deliberately self-contained: a subject does NOT depend on the issuer's code or keys. It holds
// its OWN private key and produces only the `consent` half of a grant's two detached signatures
// (ADR-004). The real consent-capture ceremony (ADR-007) is a Sprint 6 concern; this is the crypto.

// ADR-014. Canonicalisation is RFC 8785 JCS (jcs.ts, byte-identical across every reference
// component) and signatures are ES256 as RFC 7518 §3.4 defines it — raw R‖S, never DER.
//
// This matters more here than anywhere else in the repo. A consent signature is the performer
// saying yes, and it is the one signature no one else can reproduce. If the subject's device
// canonicalises differently from the issuer, the consent signature fails to verify against the
// grant it was given for — and the failure looks identical to a forged consent.

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
  const value = cryptoSign("sha256", jcsBytes(rest), {
    key: key.privateKeyPem,
    dsaEncoding: "ieee-p1363",
  }).toString("base64url");
  return { role: "consent", kid: key.kid, value };
}
