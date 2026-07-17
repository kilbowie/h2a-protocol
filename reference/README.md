# H2A reference verifier (v0)

A small, self-contained verifier that runs the conformance check sequence and emits a decision
record. It is **fail-closed** and runs entirely outside any operator's infrastructure — this is
what "the check is free" looks like in code. It is a reference, not Bridle.

```bash
pip install -r requirements.txt
python -m h2a_ref.demo
```

Check order (see `verify.py`): signatures (consent + issuance) → validity window → status list
(stale = fail-closed; bit set = revoked) → scope (exclusions, purpose, territory) → lease window/cap.
