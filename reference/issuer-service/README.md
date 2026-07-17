# Reference issuer / status service

This service is the **revocation authority**. It holds the status-list **signing key** and is the
only component that can revoke — revocation is: set the bit, re-sign the list, publish it.

It represents the **fiduciary / rights-holder trust domain** (ADR-001, ADR-009). In production it is
operated by the fiduciary (a union / CMO) with its own key custody, in a trust domain separate from
any implementer. An implementer such as Bridle holds only this service's **public key** and can only
**fetch and verify** the signed list — it cannot produce one, and has no revoke endpoint.

Zero runtime dependencies (Node built-ins only).

## Endpoints
- `GET /pubkey` — the issuer public key (PEM). This is the trust anchor an implementer is configured with.
- `GET /status/:id` — the current **signed** status-list artefact (short-TTL, mirrorable, static-shaped).
- `POST /revoke` — **fiduciary authority.** `{ "index": <n> }` with `Authorization: Bearer <FIDUCIARY_TOKEN>`. Sets the bit, re-signs, returns the signed list.

## Run
Requires Node 18+. `npm install` fetches `tsx` — the service itself pulls in nothing at runtime.
```bash
npm install
FIDUCIARY_TOKEN=dev-secret npm start      # :8790
```

> **Demo-only key custody.** The signing key and list id are generated per process at startup, so a
> restart means a new trust anchor: lists published by the previous process no longer verify and their
> `/status/:id` 404s. A real fiduciary deployment holds a durable key under its own custody (ideally a
> KMS key policy the implementer cannot reach) and a stable list id. Nothing else about the service
> changes — which is the point: the authority is the key, not the code.
