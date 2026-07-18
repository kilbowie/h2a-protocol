"""H2A architecture & process-flow diagrams — themed inline HTML, generated at build time.

Same spirit as schema_doc.py: one source of truth, rendered by the build, never a client-side
dependency. Each diagram is a small HTML fragment built from the shared node/connector/legend
vocabulary below. Diagrams reference ONLY the site's CSS variables (--ink/--paper/--rule/--mut/
--ok/--bad/--info), so they follow the light/dark theme toggle automatically and speak the exact
GREEN=pass / RED=fail / BLUE=info language — no baked colours, no JS.

build.py owns the CSS (the .dg-* classes) and substitutes `<!--DIAGRAM:name-->` markers in any
markdown page with render(name). Add a diagram by writing a renderer and registering it in RENDERERS;
an unknown name raises, so a typo fails the build (same fail-fast intent as the schema coverage guard).
"""
from __future__ import annotations

import html


def esc(s) -> str:
    return html.escape(str(s), quote=True)


# ---------------------------------------------------------------- shared vocabulary

def _node(title: str, sub: str | None = None, cls: str = "", tag: str | None = None) -> str:
    """One card. `title` is the bold line, `sub` the muted line under it (both may hold safe HTML),
    `cls` adds accent variants (dg-ok / dg-bad / dg-info / dg-strong), `tag` is a small corner label."""
    tag_html = f'<span class="dg-tag">{tag}</span>' if tag else ""
    sub_html = f'<span class="s">{sub}</span>' if sub else ""
    return f'<div class="dg-node {cls}">{tag_html}<span class="t">{title}</span>{sub_html}</div>'


def _conn(kind: str = "", label: str | None = None) -> str:
    """A downward connector arrow. kind ∈ {'', 'ok', 'info', 'bad'} sets the colour; optional side label."""
    lbl = f'<span class="lbl">{label}</span>' if label else ""
    return f'<div class="dg-conn {kind}">{lbl}</div>'


def legend() -> str:
    """The shared colour key — green=pass, red=fail, blue=info. Also embeddable on its own."""
    return (
        '<div class="dg-legend" role="img" aria-label="Colour key: green means pass or permitted, '
        'red means fail or refused, blue means informational or neutral">'
        '<span class="dg-key"><i class="sw sw-ok"></i>pass / permitted</span>'
        '<span class="dg-key"><i class="sw sw-bad"></i>fail / refused</span>'
        '<span class="dg-key"><i class="sw sw-info"></i>info / neutral</span>'
        "</div>"
    )


def _fig(inner: str, caption: str, wide: bool = False, aria: str | None = None) -> str:
    """Wrap a diagram body in a <figure> with a caption. Diagrams fit the prose column and shrink to
    any width (flex-wrap + min-width:0), so they never trigger the body-level horizontal scroll the
    `.wide` breakout can cause on narrow screens; `wide` is accepted for call-site intent but the
    layout is width-safe without it."""
    label = f' aria-label="{esc(aria)}"' if aria else ""
    return (f'<figure class="diagram"><div class="dg-body" role="img"{label}>{inner}</div>'
            f"<figcaption>{caption}</figcaption></figure>")


# ---------------------------------------------------------------- 1. verification flow

def verification_flow() -> str:
    """The normative five-gate verifier (SPEC-CORE §4), fail-closed. Green spine = the pass path;
    each gate branches red to the matching REFUSED_* decision + reason_code (labels taken from
    reference/h2a_ref/verify.py so the picture matches the running code, not just the prose)."""
    gates = [
        ("1 · Signatures", "<code>consent</code> + <code>issuance</code> both verify over the canonical grant",
         "REFUSED_OUT_OF_SCOPE", "malformed-signatures · consent-signature-invalid · issuance-signature-invalid"),
        ("2 · Validity window", "<code>nbf ≤ now ≤ exp</code>",
         "REFUSED_OUT_OF_SCOPE", "grant-outside-validity-window"),
        ("3 · Status", "fetch the signed list, verify its signature, read the bit — fail closed",
         "REFUSED_REVOKED", "status-signature-invalid-fail-closed · status-list-stale-fail-closed · asset-revoked"),
        ("4 · Scope", "purpose in <code>purposes</code>, not in <code>exclusions</code>; territory permitted",
         "REFUSED_OUT_OF_SCOPE", "purpose-not-granted · excluded · territory-not-granted"),
        ("5 · Lease", "within the lease window and under the spend <code>cap</code>",
         "REFUSED_LEASE_EXHAUSTED", "lease-outside-window · lease-cap-exceeded"),
    ]
    rows = [_node("Grant presented at the point of use",
                  "checked fresh every time — never cached (SPEC-CORE §5)", "dg-strong dg-flow-w")]
    for title, sub, decision, reasons in gates:
        rows.append(_conn("ok"))
        branch = (
            '<div class="dg-branch">'
            '<span class="dg-branch-arrow">✗</span>'
            f'<span class="dg-pill bad"><b>{decision}</b><span class="rc">{reasons}</span></span>'
            "</div>"
        )
        rows.append(
            '<div class="dg-gaterow">'
            f'<div class="dg-node dg-gate">{title}<span class="s">{sub}</span></div>'
            f"{branch}"
            "</div>"
        )
    rows.append(_conn("ok", "all gates pass"))
    rows.append(_node("✔ PERMITTED_CONFORMANT",
                      "signed decision record emitted", "dg-ok dg-flow-w"))
    body = f'<div class="dg-flow">{"".join(rows)}</div>{legend()}'
    return _fig(
        body,
        "H2A verification runs the same five gates everywhere, in order, failing closed at the first "
        "failure. Green is the single pass path; any gate can branch to a red <code>REFUSED_*</code> "
        "decision, labelled with the reason code the reference verifier emits.",
        wide=True,
        aria=("Vertical flowchart: a grant enters and passes in order through five gates — signatures, "
              "validity window, status, scope, lease. Passing every gate yields a green "
              "PERMITTED_CONFORMANT result; failing any gate branches to a red REFUSED decision."),
    )


# ---------------------------------------------------------------- 2. four-object map

def object_map() -> str:
    """The four core objects and how they bind. Attestation / Decision Record / Media / Memory all
    reference the Grant by grant_id; the Grant points at its Status List by status.uri + status.index."""
    referencing = (
        '<div class="dg-cols">'
        + _node("Attestation", "receipt of one act of use", "dg-node-sm")
        + _node("Decision Record", "conformant / non-conformant outcome", "dg-node-sm")
        + _node("Media profile", "asset-bound, when granted", "dg-node-sm")
        + _node("Memory profile", "asset-bound, when granted", "dg-node-sm")
        + "</div>"
    )
    body = (
        referencing
        + _conn("", "reference the grant by <code>grant_id</code>")
        + _node("Grant",
                "authority to use a subject within a bounded scope — the object everything else binds to",
                "dg-strong dg-flow-w")
        + _conn("info", "points at its revocation state by <code>status.uri</code> + <code>status.index</code>")
        + _node("Status List", "static, signed revocation artefact — one bit per grant", "dg-info dg-flow-w")
    )
    return _fig(
        f'<div class="dg-flow">{body}</div>',
        "The Grant is the hub: an Attestation, Decision Record, and the Media / Memory profiles each "
        "bind back to it by <code>grant_id</code>, while the Grant itself points at its Status List by "
        "<code>status.uri</code> and <code>status.index</code>.",
        aria=("Relationship map: Attestation, Decision Record, Media profile and Memory profile all "
              "reference the central Grant by grant_id; the Grant references its Status List by "
              "status.uri and status.index."),
    )


# ---------------------------------------------------------------- 3. trust-domain / revocation split

def trust_domains() -> str:
    """ADR-009: revocation authority = custody of the status-list signing key. Two separate trust
    domains — the issuer/fiduciary signs and revokes; the implementer only fetches and verifies."""
    issuer = _node(
        "Issuer / fiduciary domain",
        '<span class="ok">holds the <b>private</b> signing key</span><br>'
        "revoke = set the bit · re-sign · publish<br>"
        "serves <code>GET /status/:id</code> · <code>GET /pubkey</code><br>"
        "<code>POST /revoke</code> — fiduciary authority required",
        "dg-info",
        tag="revocation authority",
    )
    implementer = _node(
        "Implementer domain",
        'holds the issuer\'s <b>public</b> key as a trust anchor<br>'
        "<span class=\"ok\">fetch → verify signature → read bit</span><br>"
        '<span class="bad">fails closed</span> on unreachable / unsigned / wrongly-signed / stale<br>'
        '<span class="bad">no <code>/revoke</code> · serves no list of its own</span>',
        "",
        tag="fetch-and-verify only",
    )
    body = (
        '<div class="dg-cols dg-cols-wide">' + issuer + implementer + "</div>"
        + _conn("info", "signed status list flows one way →")
        + '<p class="dg-caption-inline">Possession of the key <b>is</b> the authority: whoever can '
          "sign the list can clear the bit. Keeping the key out of the implementer is what makes the "
          "split provable, not just asserted.</p>"
    )
    return _fig(
        body,
        "ADR-009 — revocation authority is custody of the status-list signing key. The issuer signs "
        "and revokes; the implementer only fetches and verifies the signed list and fails closed. "
        "It has no revoke endpoint and serves no list of its own.",
        wide=True,
        aria=("Two separate trust domains. The issuer / fiduciary domain holds the private signing key "
              "and can revoke by re-signing the status list. The implementer domain holds only the "
              "public key, fetches and verifies the signed list, and fails closed; it cannot revoke."),
    )


# ---------------------------------------------------------------- 4. conformance ladder

def conformance_ladder() -> str:
    """L1 → L2 → L3. Each rung adds capability; L3 is the level an underwriter can rely on."""
    rungs = (
        _node("L1 · Verifiable",
              "objects validate · signatures verify · the verification algorithm runs and fails closed",
              "dg-node-rung")
        + _conn("", "adds")
        + _node("L2 · Attested",
              "L1 + point-of-use attestations & decision records for every act, against a resolvable, "
              "short-TTL <b>signed</b> status list the verifier checks (ADR-009)", "dg-node-rung")
        + _conn("", "adds")
        + _node("L3 · Anchored",
              "L2 + external anchoring: eIDAS-qualified TSA timestamps + independent witness "
              "co-signature — the level an underwriter can rely on", "dg-node-rung dg-ok dg-strong")
    )
    return _fig(
        f'<div class="dg-flow dg-ladder">{rungs}</div>',
        "Conformance is honest by construction — each level claims only what it can prove. L1 verifies, "
        "L2 attests against a signed status list, L3 anchors externally. L3 is underwriter-grade.",
        aria="Ascending ladder of three conformance levels: L1 Verifiable, L2 Attested, L3 Anchored.",
    )


# ---------------------------------------------------------------- 5. two-signature grant

def two_signatures() -> str:
    """A grant MUST carry exactly two detached signatures with distinct roles (SPEC-CORE §3)."""
    sigs = (
        '<div class="dg-cols">'
        + _node("consent", "signed by the <b>subject or custodian</b> — authorises the use itself",
                "dg-node-sm", tag="required")
        + _node("issuance", "signed by the <b>issuer</b> — issues the grant", "dg-node-sm", tag="required")
        + "</div>"
    )
    body = _node("Grant", "carries exactly two detached signatures, distinct roles — a verifier "
                          "validates <b>both</b>; neither implies the other", "dg-strong dg-flow-w") \
        + _conn() + sigs
    return _fig(
        f'<div class="dg-flow">{body}</div>',
        "Every grant binds two independent signatures — <code>consent</code> from the subject (or "
        "custodian) and <code>issuance</code> from the issuer. Both are required; a grant missing "
        "either is refused at gate 1.",
        aria=("A Grant carries two detached signatures with distinct roles: consent from the subject "
              "or custodian, and issuance from the issuer. Both are required."),
    )


# ---------------------------------------------------------------- 6. delegation attenuation

def delegation_chain() -> str:
    """Delegation is attenuation-only: a child never widens scope, extends validity, or raises the
    cap. The effective chain horizon is the max over all links."""
    chain = (
        '<div class="dg-chain">'
        + _node("Parent grant", "widest scope · longest validity · highest cap", "dg-node-sm")
        + '<span class="dg-arrow-h" aria-hidden="true">→</span>'
        + _node("Child grant", "⊆ parent · narrower or equal", "dg-node-sm")
        + '<span class="dg-arrow-h" aria-hidden="true">→</span>'
        + _node("Grandchild grant", "⊆ child · narrower or equal", "dg-node-sm")
        + "</div>"
    )
    body = chain + (
        '<p class="dg-caption-inline"><b>Attenuation-only:</b> a child grant MUST NOT widen scope, '
        "extend the validity window, or raise the lease cap beyond its parent. The <b>effective chain "
        "horizon = the maximum over all links</b> — a chain is only as revocable as its slowest link.</p>"
    )
    return _fig(
        f'<div class="dg-flow">{body}</div>',
        "Delegation only narrows. Each child grant is a subset of its parent; revocation responsiveness "
        "of the whole chain is bounded by its slowest link.",
        wide=True,
        aria=("A delegation chain of three grants, each a subset of the one before: parent, child, "
              "grandchild. Scope only narrows down the chain."),
    )


# ---------------------------------------------------------------- 7. evidence / anchoring

def anchoring_pipeline() -> str:
    """Evidence, not enforcement (ADR-006/005). A non-conformant transmission is recorded, then the
    decision record is anchored off the critical path with a TSA timestamp + witness co-signature."""
    body = (
        _node("Transmission occurs outside conformance", "H2A does not stop a third-party executor",
              "dg-flow-w")
        + _conn("bad", "recorded, not blocked")
        + _node("Decision Record — TRANSMITTED_NON_CONFORMANT",
                "with a populated <code>non_conformant_transmission</code> "
                "(<code>downstream_ref</code>, <code>why</code>) — the standard's primary output", "dg-bad dg-flow-w")
        + _conn("info", "anchored off the runtime critical path")
        + _node("RFC 3161 TSA timestamp + independent witness co-signature",
                "eIDAS-qualified · no blockchain (ADR-005)", "dg-info dg-flow-w")
        + _conn("info")
        + _node("Append-only chain head", "signed, externally anchored, admissible evidence", "dg-info dg-flow-w")
    )
    return _fig(
        f'<div class="dg-flow">{body}</div>',
        "H2A evidences; it does not enforce. A transmission outside conformance is recorded explicitly "
        "as a signed Decision Record, then anchored with a qualified timestamp "
        '(<a href="references.html">RFC 3161 / eIDAS</a>) and an independent witness co-signature so it '
        "stands as admissible evidence.",
        aria=("Pipeline: a non-conformant transmission is recorded as a Decision Record marked "
              "TRANSMITTED_NON_CONFORMANT, then anchored with an RFC 3161 timestamp and a witness "
              "co-signature onto an append-only chain head."),
    )


# ---------------------------------------------------------------- registry

RENDERERS = {
    "verification-flow": verification_flow,
    "object-map": object_map,
    "trust-domains": trust_domains,
    "conformance-ladder": conformance_ladder,
    "two-signatures": two_signatures,
    "delegation-chain": delegation_chain,
    "anchoring-pipeline": anchoring_pipeline,
    "legend": lambda: legend(),
}


def render(name: str) -> str:
    """Render one registered diagram; raise on an unknown name so a typo fails the build."""
    try:
        return RENDERERS[name]()
    except KeyError:
        raise KeyError(
            f"unknown diagram '{name}'; known: {', '.join(sorted(RENDERERS))}"
        ) from None
