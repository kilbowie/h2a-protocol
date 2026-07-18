# h2a-verify — the standalone verifier

The falsifiability artefact for H2A. Given an evidence **bundle** and a pinned set of trust
**anchors**, it re-derives the decision from first principles and reports whether the implementer's
signed record is an **honest reflection of the evidence**. It has **zero runtime dependencies**, runs
anywhere Node runs, and **imports no implementer code** — that independence is the point: it must be
able to expose a misbehaving implementer, so it cannot borrow the implementer's own verification.

```bash
npm run verify -- bundle.json anchors.json     # exit 0 = honest, 1 = disagreement/bad signature
npm run selftest                               # end-to-end proof with freshly generated keys
```

## What it checks

| Check | Level | What it proves |
|---|---|---|
| `grant.consent_signature` | L1 | the subject really consented (verifies against the subject's pinned key) |
| `grant.issuance_signature` | L1 | the issuer really issued (verifies against the issuer's pinned key) |
| `grant.validity_window` | L1 | now is within the grant's `[nbf, exp]` |
| `status_list.signature` | L2 | the revocation list is the issuer's, unforged |
| `status_list.issuer_match` | L2 | the list belongs to the grant's issuer namespace |
| `status_list.freshness` | L2 | the list is within `valid_until` |
| `status_list.revocation_bit` | L2 | the bit at `status.index` — **fail-closed** if the list is unusable |
| `decision_record.signature` | L2 | the record is the implementer's, unforged (pinned key — it cannot swap keys) |
| `decision.consistency` | L1 | **the record's decision matches an independent re-derivation** — the anti-trust check |
| `anchoring.*` | L3 | `not_evaluated` until eIDAS timestamps + a witness co-signature are in the bundle |

`ok` is true only when **no evaluated check fails**. A *revoked* asset still verifies `ok` when the
record correctly says `REFUSED_REVOKED` — the verifier checks **honesty**, not permission.

## The trust model, and why it survives a change of ownership (ADR-010)

Trust anchors are **pinned by the operator**, keyed by **issuer namespace** (the `iss` URL). The
implementer being checked never supplies them; the verifier fetches the implementer's key only to
check the implementer's *own* signature, and pins the **authority** (issuer/fiduciary) key
externally. Today the namespace and this anchor file are **founder-operated, in a trust domain the
implementer cannot reach**. The mechanism already embodies the separation, so the only future changes
are ownership moves — **no code change**:

1. a rights-holder **fiduciary** takes custody of the issuer signing key at the `iss` endpoint (the
   namespace re-homes / DNS moves); and
2. **`h2a-protocol.org`** — where this verifier and the anchor policy live — passes to **Foundation**
   governance.

The on-wire objects and this binary are unchanged. See `../../spec/adr/ADR-010-trust-anchor-governance.md`.

## Bundle shape

```jsonc
{
  "grant": { /* the H2A grant, with its two detached signatures */ },
  "use": { "purpose": "promotional-video", "territory": "GB", "spend": 100 },
  "decision_record": { /* the implementer's signed decision record */ },
  "status_list": { /* the issuer's signed status list, as fetched at decision time */ },
  "implementer": "bridle"   // optional; else every pinned implementer key is tried
}
```

`anchors.json` — see `anchors.example.json`.
