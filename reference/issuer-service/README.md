# Reference issuer / status service

This service is the **revocation authority**. It holds the status-list **signing key** and is the
only component that can revoke — revocation is: set the bit, re-sign the list, publish it.

It represents the **fiduciary / rights-holder trust domain** (ADR-001, ADR-009). In production it is
operated by the fiduciary (a union or CMO) with its own key custody, in a trust domain separate from
any implementer. An implementer holds only this service's **public key** and can only
**fetch and verify** the signed list — it cannot produce one, and has no revoke endpoint.

Zero runtime dependencies (Node built-ins only).

## Endpoints
- `GET /pubkey` — the issuer public key (PEM). This is the trust anchor an implementer is configured with.
- `GET /status/:id` — the current **signed** status-list artefact (short-TTL, mirrorable, static-shaped).
- `POST /revoke` — **fiduciary authority.** `{ "index": <n> }` with `Authorization: Bearer <FIDUCIARY_TOKEN>`. Sets the bit, re-signs, returns the signed list.

- `POST /sign-grant` — **issuer authority.** Signs the issuance half of a grant (ADR-004); same Bearer token.

## Run
Requires Node 18+. `npm install` fetches `tsx` — the service itself pulls in nothing at runtime.
```bash
npm install
FIDUCIARY_TOKEN=dev-secret npm start      # :8790  (ephemeral key — a local demo)
```

## Durable custody (for a hosted deployment)
By default the signing key and list id are generated **per process** (a restart → new trust anchor; old
`/status/:id` 404s). That is fine for a driven local demo. For anything left running, set:
- **`ISSUER_SIGNING_KEY`** — a durable EC P-256 **PKCS8 PEM**
  (`openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256`). Boot log then reads
  `key custody: DURABLE`.
- **`ISSUER_LIST_ID`** — a stable status-list id (any UUID), so published `status.uri`s survive restarts.
- **`ISSUER_ISS`** — the issuer namespace (default is the example namespace; override in production).
- **`ISSUER_REVOKED_PATH`** *(optional)* — a JSON file on a persistent volume so live revokes survive a
  restart (else the revoked set is in-memory).

> This env-loaded key is the **interim** stand-in. Genuine fiduciary custody — a KMS key policy the
> implementer cannot reach, held in the fiduciary's own trust domain (ADR-001) — is the follow-on. The
> authority is the key, not the code; that is the point. A container image lives in `./Dockerfile`, and
> the full hosted topology is in `bridle/deploy/RUNBOOK.md`.
