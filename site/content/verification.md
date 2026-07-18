# How verification works

A conformant verifier runs the same sequence everywhere, failing closed at the first failure. It is
operator-independent by design — nothing in it is specific to who runs it.

<!--DIAGRAM:verification-flow-->

1. **Signatures.** Verify the two detached signatures — *consent* (subject / custodian) and
   *issuance* (issuer) — over the canonical Grant.
2. **Validity window.** The Grant must be within `nbf`…`exp`.
3. **Status.** Fetch the signed status list (or a mirror) and verify its signature against the
   issuer's public key. Unreachable, unsigned, wrongly-signed, or expired ⇒ fail closed. Bit set ⇒
   `REFUSED_REVOKED`. The verifier is **fetch-and-verify only**: it is never the revocation
   authority and serves no status list of its own ([ADR-009](adr-009.html)).
4. **Scope.** Requested purpose in `purposes`, not in `exclusions`; territory permitted.
5. **Lease.** Within the lease window and under the spend cap.

Success yields `PERMITTED_CONFORMANT`; anything else yields the matching `REFUSED_*`. The executable
form of this is `reference/h2a_ref/verify.py` — the demo issues a signed grant and shows permit,
out-of-scope refusal, and post-revocation refusal.
