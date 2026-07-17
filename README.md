# H2A Protocol

A neutral, open standard for the **consent, attestation, and revocation** of AI-generated likeness
(H2A-Media) and AI memory (H2A-Memory). H2A **evidences; it does not enforce** — it produces a
signed, externally-anchored record of whether each act of use was conformant.

> **Working draft (v0.x).** The wire format may change before v1.0. Not yet a ratified standard.

## Layout
```
spec/            SPEC-CORE, SPEC-MEDIA, SPEC-MEMORY, CONFORMANCE, THREAT-MODEL
spec/adr/        ADR-001 … ADR-009 (locked decisions)
schemas/v0/      6 JSON Schemas (Draft 2020-12) + examples/ (positive + negative)
reference/       runnable reference verifier (h2a_ref) — the executable spec
  issuer-service/  reference issuer / status service — the revocation authority (ADR-009)
scripts/         validate-schemas.py, check-reference.py (CI gates)
site/            static site generator -> h2a-protocol.org (build.py, content/, CNAME)
.github/         Pages workflow: validate -> check reference -> build -> deploy
```

## Build & verify
```bash
pip install -r requirements.txt -r reference/requirements.txt
python scripts/validate-schemas.py         # schemas + positive/negative examples (CI gate)
python scripts/check-reference.py          # the running reference vs the schemas (CI gate)
python site/build.py                       # -> site/_out
( cd reference && python -m h2a_ref.demo )
```

## Standing it up
1. Create GitHub org `h2a-protocol`; this is the **public** repo. `git init && git add -A && git commit && git push`.
2. DNS for **h2a-protocol.org**: four A records → `185.199.108/109/110/111.153`; `CNAME www → h2a-protocol.github.io`. Optional 301 `hdicr.org → h2a-protocol.org` (hdicr.org is the v0 witness, ADR-005).
3. Settings → Pages → Source: **GitHub Actions**. Push to `main` runs validate → build → deploy. Enforce HTTPS after the cert issues.
4. Branch protection on `main`: require the Pages workflow green.

## Open gates
See `GOVERNANCE.md`: **G1** identity namespace root (pick the interim production namespace before issuing real grants), **G2** licensing (add via GitHub picker), **G4** versioning promise. Licensing: spec = CC BY 4.0, everything else = Apache-2.0.
