# ADR-010 — Trust-anchor governance: pinned by namespace, founder-operated, foundation-bound

**Status:** Accepted (2026-07-18). Builds on ADR-001 (identity namespace root), ADR-009 (revocation
authority), and the standalone verifier (`reference/verifier/`).

## Context
A verifier is only as trustworthy as the set of keys it will honour. If the party being checked also
decides *which keys count*, the check proves nothing — the same trap ADR-009 closes for revocation,
one level up. WebPKI, Certificate Transparency and OIDC all locate real leverage not in signing but in
**trust-anchor curation** (browser root programs, CT log lists). So H2A must answer, out loud: *who
curates the anchor set, and how does that survive a change of ownership?* The neutrality brief
(`bridle/docs/BRIEF-neutrality-page-rewrite.md` §8 Q1) names this the single largest gap between the
claim and the build, and forbids it being **silently** implementer-curated.

Today there is no foundation and no third-party fiduciary — the founder operates everything. The
decision must be honest about that **and** make the eventual hand-off a change of *ownership*, not a
change of *code*.

## Decision
**Trust anchors are pinned by the operator running the verifier, keyed by issuer namespace. The
implementer being checked never supplies them. No anchor set is shipped or curated by the
implementer.**

1. **Pinned by namespace.** Each grant/status-list `iss` is a URL namespace (ADR-001). The verifier
   resolves the key to trust for that issuer from an operator-provided `anchors` set keyed by the `iss`
   string. An unpinned namespace is **untrusted** (the check fails), never trust-on-first-use.
2. **The checked party never supplies its own anchors.** The verifier fetches the implementer's key
   only to test the implementer's *own* signature; the **authority** keys (issuer/fiduciary) are pinned
   externally. The implementer's key is itself pinned, so it cannot swap keys undetected.
3. **No implementer-curated default set.** `reference/verifier/` ships **no** bundled anchors — only
   `anchors.example.json`. There is nothing for the implementer to quietly control.
4. **Independent re-derivation.** The verifier re-derives the decision from first principles and
   compares it to the implementer's record (`decision.consistency`); it imports no implementer code.

### Interim reality (v1, founder-operated) — stated plainly
- The issuer namespace `interim-fiduciary.kilbowieconsulting.com/h2a/issuer` is **founder-operated**,
  in a trust domain the implementer cannot reach (separate process/credentials; ADR-009 v0 caveat).
- The verifier and this anchor policy live at **`h2a-protocol.org`**, **founder-owned** today.
- Anyone can run the verifier against their **own** pinned anchors; the founder curates no set on
  anyone's behalf.

## What the technical design already proves (so hand-off is code-free)
Because identity is a **namespace** and authority is **custody of the key behind that namespace**, the
separation is already real in the bytes on the wire. The migration to genuine independence is therefore
**two ownership moves, zero code changes**:

| Change | Mechanism | Code change? |
|---|---|---|
| Fiduciary takes revocation authority | a rights-holder/CMO takes custody of the issuer signing key and serves it at the `iss` endpoint; the namespace re-homes (DNS / hand-over) | **none** — `iss` is already a URL; grants, status lists, and the verifier are unchanged |
| Anchor policy becomes governed | `h2a-protocol.org` (verifier + anchor policy) transfers to an **H2A Foundation** | **none** — the verifier already ships no curated set; governance is about who publishes the recommended anchors |

The falsifiable claim we can make **today**: *the verifier is open, runs outside our infrastructure,
imports none of our code, honours only anchors the operator pins, and re-derives every decision — so it
would expose us if we lied.* The claim we **cannot** yet make: that an independent party holds the
issuer key or governs the anchors. ADR-009's honesty rule applies unchanged.

## Consequences
- **Promotion trigger (recorded, per BRIEF §8 Q3).** The headline "no single party can suppress a
  revocation, us included" is fully earned when: (a) this verifier is published and reproducible
  outside founder infrastructure ✅ *(shipped here)*; (b) the issuer key is in genuine fiduciary
  custody at its namespace; and (c) `h2a-protocol.org` is Foundation-governed. Until (b) and (c), the
  page says exactly this — founder-operated interim, with the mechanism already proving the split.
- **Mirror architecture** rides on the same namespace pinning: a grant lists multiple `status.mirrors`
  URIs; the list is a static signed artefact, so a suppressed mirror is detectable and a stale one
  fails `status_list.freshness` — no mirror operator can forge or silently withhold a revocation.
- **No trust-on-first-use, ever.** Convenience auto-fetch of authority anchors from the checked party
  is explicitly rejected; it would reintroduce the ADR-009 trap.
