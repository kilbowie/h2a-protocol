"""RFC 8785 JSON Canonicalization Scheme + JOSE ES256 signature encoding (ADR-014).

Standard library only, matching the rest of h2a_ref.

WHY THIS IS NOT `json.dumps(sort_keys=True)`
--------------------------------------------
That is what verify.py:28 used, and it is wrong in two ways that a JSON payload of lowercase ASCII
keys and integer values will never reveal:

    json.dumps({"subject_ref": "José"},  sort_keys=True)   -> {"subject_ref":"Jos\\u00e9"}
    json.dumps({"cap": 500.0},           sort_keys=True)   -> {"cap":500.0}
    RFC 8785                                               -> {"subject_ref":"José"}
                                                              {"cap":500}

`ensure_ascii=True` is the default, so every non-ASCII character is escaped; RFC 8785 §3.2.2.2
requires literal UTF-8 above U+001F. And Python's float repr is not ECMAScript's: `500.0` keeps its
trailing `.0`, `-0.0` keeps its sign, `1e2` becomes `100.0`.

Python gets ORDERING right — `sort_keys=True` sorts by code point, which for the BMP agrees with
RFC 8785's UTF-16 code units. That is the mirror image of the TypeScript hand-roll, which ordered
wrongly and serialised correctly. Neither was a subset of the other, and both agreed with JCS on
everything anyone tested, which is why the split survived.

Numbers are the whole of the work here. See _ecmascript_number.
"""
from __future__ import annotations

import math
import re

__all__ = ["jcs", "jcs_bytes", "der_to_raw", "raw_to_der", "looks_like_der"]

P256_COORD_BYTES = 32


def jcs(value: object) -> str:
    """RFC 8785 canonical JSON."""
    out: list[str] = []
    _serialize(value, out)
    return "".join(out)


def jcs_bytes(value: object) -> bytes:
    """The UTF-8 bytes to sign or hash. Signatures are over bytes, not over strings."""
    return jcs(value).encode("utf-8")


def _serialize(v: object, out: list[str]) -> None:
    if v is None:
        out.append("null")
    elif v is True:
        out.append("true")
    elif v is False:
        out.append("false")
    elif isinstance(v, str):
        out.append(_ecmascript_string(v))
    elif isinstance(v, (int, float)):
        out.append(_ecmascript_number(v))
    elif isinstance(v, (list, tuple)):
        out.append("[")
        for i, e in enumerate(v):
            if i:
                out.append(",")
            _serialize(e, out)
        out.append("]")
    elif isinstance(v, dict):
        out.append("{")
        first = True
        # §3.2.3 — sort property names as arrays of UTF-16 code units compared as unsigned
        # integers. Python strings sort by code POINT, which differs from UTF-16 code-unit order
        # only for astral characters (U+10000+), where a surrogate pair's lead unit (0xD800-0xDBFF)
        # sorts below U+E000-U+FFFF. Encoding to UTF-16BE makes the comparison exact rather than
        # nearly-exact — the kind of gap that shows up once, in production, in someone's name.
        for k in sorted(v.keys(), key=lambda s: s.encode("utf-16-be")):
            if not isinstance(k, str):
                raise TypeError(f"jcs: property names must be strings, got {type(k).__name__}")
            if not first:
                out.append(",")
            first = False
            out.append(_ecmascript_string(k))
            out.append(":")
            _serialize(v[k], out)
        out.append("}")
    else:
        raise TypeError(f"jcs: {type(v).__name__} has no JSON representation")


# §3.2.2.2 — the five short forms; every other character below U+0020 is lowercase \uhhhh.
_SHORT_ESCAPES = {0x08: "\\b", 0x09: "\\t", 0x0A: "\\n", 0x0C: "\\f", 0x0D: "\\r"}


def _ecmascript_string(s: str) -> str:
    out = ['"']
    for ch in s:
        o = ord(ch)
        if ch == '"':
            out.append('\\"')
        elif ch == "\\":
            out.append("\\\\")
        elif o < 0x20:
            out.append(_SHORT_ESCAPES.get(o) or f"\\u{o:04x}")
        else:
            # Everything above U+001F is emitted literally, including all non-ASCII. This is the
            # `ensure_ascii=False` behaviour, made explicit so it cannot be un-set by a caller.
            out.append(ch)
    out.append('"')
    return "".join(out)


_REPR_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?$")


def _ecmascript_number(x: "int | float") -> str:
    """Serialise per ECMAScript Number::toString (RFC 8785 §3.2.2.3, ECMA-262 §7.1.12.1).

    Every value goes through float() first. That is deliberate rather than lossy-by-accident:
    RFC 8785 defines JSON numbers as IEEE 754 doubles, so an integer too large for a double must
    canonicalise the way JavaScript would canonicalise it, precision loss included. Python's
    arbitrary-precision ints would otherwise produce bytes no JavaScript implementation can match.
    """
    if isinstance(x, bool):  # bool is an int subclass; it must never reach here
        raise TypeError("jcs: bool is not a number")
    f = float(x)
    if math.isnan(f) or math.isinf(f):
        raise ValueError(f"jcs: {x} has no JSON representation")
    if f == 0:
        return "0"  # covers -0.0 -> "0", per the spec
    if f < 0:
        return "-" + _ecmascript_number(-f)

    # repr() is the shortest string that round-trips, which is exactly the digit sequence the
    # ECMAScript algorithm calls `s` (with `k` digits, value s x 10^(n-k)). Recover s and n.
    m = _REPR_RE.match(repr(f))
    if not m:  # pragma: no cover - repr of a positive finite float always matches
        raise ValueError(f"jcs: cannot parse repr({f})")
    int_part, frac_part, exp_part = m.group(1), m.group(2) or "", m.group(3)
    digits = (int_part + frac_part).lstrip("0")
    leading_zeros = len(int_part + frac_part) - len(digits)
    n = len(int_part) + (int(exp_part) if exp_part else 0) - leading_zeros
    digits = digits.rstrip("0") or "0"
    k = len(digits)

    if k <= n <= 21:
        return digits + "0" * (n - k)          # 100
    if 0 < n <= 21:
        return digits[:n] + "." + digits[n:]   # 1.5
    if -6 < n <= 0:
        return "0." + "0" * -n + digits        # 0.001
    # Exponential form. ECMAScript writes the exponent sign always, and never pads it.
    e = n - 1
    mantissa = digits if k == 1 else digits[0] + "." + digits[1:]
    return f"{mantissa}e{'+' if e >= 0 else '-'}{abs(e)}"


# ---------------------------------------------------------------------------
# ES256 signature encoding — ADR-014 §2.
#
# `alg: "ES256"` is RFC 7518 §3.4: fixed-width r‖s, each left-padded to 32 bytes, 64 bytes total,
# never DER. `cryptography`'s sign()/verify() speak DER, so convert at that boundary.
# ---------------------------------------------------------------------------


def der_to_raw(der: bytes) -> bytes:
    """DER SEQUENCE{INTEGER r, INTEGER s} -> raw 64-byte r‖s."""
    from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

    r, s = decode_dss_signature(der)
    return r.to_bytes(P256_COORD_BYTES, "big") + s.to_bytes(P256_COORD_BYTES, "big")


def raw_to_der(raw: bytes) -> bytes:
    """Raw 64-byte r‖s -> DER SEQUENCE{INTEGER r, INTEGER s}."""
    from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

    if len(raw) != 2 * P256_COORD_BYTES:
        raise ValueError(f"raw_to_der: expected {2 * P256_COORD_BYTES} bytes, got {len(raw)}")
    r = int.from_bytes(raw[:P256_COORD_BYTES], "big")
    s = int.from_bytes(raw[P256_COORD_BYTES:], "big")
    return encode_dss_signature(r, s)


def looks_like_der(sig: bytes) -> bool:
    """True if the signature is plausibly DER rather than raw r‖s — for a precise error message."""
    return len(sig) != 2 * P256_COORD_BYTES and len(sig) > 0 and sig[0] == 0x30
