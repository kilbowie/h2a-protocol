# H2A reference verifier (v0)

A small, self-contained verifier that runs the conformance check sequence and emits a decision
record. It is **fail-closed** and runs entirely outside any operator's infrastructure — this is
what "the check is free" looks like in code. It is a reference, not a production implementation.

```bash
pip install -r requirements.txt
python -m h2a_ref.demo
```

Check order (see `verify.py`): signatures (consent + issuance) → validity window → **status-list
signature** (unsigned / wrongly-signed / stale = fail-closed; bit set = revoked) → scope (exclusions,
purpose, territory) → lease window/cap.

`verify()` takes the issuer's `status_pubkey` as a **required** argument — there is no path that
permits a list it could not verify (SPEC-CORE §4.3).

## The two halves

The verifier here is deliberately not the whole picture. Revocation authority is custody of the
status-list signing key (ADR-009), so the reference is split across two trust domains:

- `h2a_ref/` — the **implementer** side. Fetch-and-verify only: holds the issuer's *public* key,
  reads the bit, fails closed. It cannot revoke, and serves no list.
- `issuer-service/` — the **issuer / fiduciary** side. Holds the *private* key and is the only
  component that can revoke. `h2a_ref/issue.py` is the Python equivalent used by the demo and the
  CI gate; both produce the same artefact shape.

`python scripts/check-reference.py` (from the repo root) enforces that: it validates every artefact
the reference emits against the schemas, and asserts a list signed by the wrong key is refused.

Because the authority is one key and not one language, `scripts/check-interop.py` closes the loop
across the boundary: the TypeScript issuer signs a list (`npm --prefix reference/issuer-service run
emit-interop`), and the Python verifier confirms that signature, reads the revoked bit, and reaches
the right decision. If the two `canonical()` implementations ever drift, that gate fails.
