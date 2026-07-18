# References

H2A builds on established technical standards and legal instruments rather than inventing its own. This
page collects every external reference cited across the specification, with a link to its authoritative
source. Citations elsewhere on the site link here or directly to these sources.

## Normative & informative references

| Reference | Where it applies in H2A | Source |
|---|---|---|
| **RFC 2119** — key words for requirement levels | The MUST / SHOULD / MAY terms throughout the [core spec](spec-core.html) | [rfc-editor.org/rfc/rfc2119](https://www.rfc-editor.org/rfc/rfc2119) |
| **RFC 3161** — Internet X.509 Time-Stamp Protocol (TSP) | Trusted timestamps for [anchoring](spec-core.html#7-anchoring-adr-005) Decision Records (ADR-005) | [rfc-editor.org/rfc/rfc3161](https://www.rfc-editor.org/rfc/rfc3161) |
| **eIDAS** — Regulation (EU) No 910/2014 | Qualified TSA timestamps at [conformance L3](conformance.html) and in anchoring (ADR-005) | [eur-lex.europa.eu](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0910) |
| **GDPR** — Regulation (EU) 2016/679, Art. 7 | The consent-capture artefact demonstrates consent per act (ADR-007) | [eur-lex.europa.eu · Art. 7](https://eur-lex.europa.eu/eli/reg/2016/679/oj#art_7) |
| **C2PA** — Coalition for Content Provenance and Authenticity | Content provenance manifests for media assets ([H2A-Media](spec-media.html)) | [c2pa.org/specifications](https://c2pa.org/specifications/) |
| **FIPS 140-3** — cryptographic module validation | Basis for the mandatory ES256 (ECDSA P-256) signing baseline (ADR-008) | [csrc.nist.gov · FIPS 140-3](https://csrc.nist.gov/pubs/fips/140-3/final) |

## Licensing

| Licence | Applies to | Source |
|---|---|---|
| **CC BY 4.0** | Specification text (`spec/**`) | [creativecommons.org · CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| **Apache-2.0** | Schemas, reference code, scripts, and this site | [apache.org · Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) |
