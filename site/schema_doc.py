"""Render the JSON Schemas as an HTML reference — generated, never hand-maintained.

The six schemas/v0/*.json files are the single source of truth. This module turns each into
a Field / Type / Required / Description table plus its CI-validated example(s), so the schemas
page can never drift from the schemas themselves. A coverage guard fails the build if any field
would be silently dropped.

build.py owns styling; it injects a `highlight(json_text) -> html` callable so this module stays
free of the Pygments dependency and both the examples and the spec code blocks share one theme.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

# Section order, titles, and the examples each schema owns. The example mapping mirrors
# POSITIVE/NEGATIVE in scripts/validate-schemas.py — both point at the same files.
# examples: (filename, rejection_reason_or_None). None => a positive, validated example.
SCHEMAS = [
    {"slug": "grant", "title": "Grant", "id_code": "h2a-core.grant",
     "file": "h2a-core.grant.schema.json",
     "examples": [("grant.valid.json", None)]},
    {"slug": "attestation", "title": "Attestation", "id_code": "h2a-core.attestation",
     "file": "h2a-core.attestation.schema.json",
     "examples": [("attestation.valid.json", None)]},
    {"slug": "decision-record", "title": "Decision Record", "id_code": "h2a-core.decision-record",
     "file": "h2a-core.decision-record.schema.json",
     "examples": [("decision-record.conformant.json", None),
                  ("decision-record.non-conformant.json", None),
                  ("decision-record.INVALID.json",
                   "TRANSMITTED_NON_CONFORMANT with no non_conformant_transmission block")]},
    {"slug": "status-list", "title": "Status List", "id_code": "h2a-core.status-list",
     "file": "h2a-core.status-list.schema.json",
     "examples": [("status-list.valid.json", None)]},
    {"slug": "media", "title": "Media Profile", "id_code": "h2a-media.profile",
     "file": "h2a-media.profile.schema.json",
     "examples": [("media.valid.json", None)]},
    {"slug": "memory", "title": "Memory Profile", "id_code": "h2a-memory.profile",
     "file": "h2a-memory.profile.schema.json",
     "examples": [("memory.derived.valid.json", None),
                  ("memory.derived.INVALID.json", "derived record carrying no provenance")]},
]

# Regex patterns used across the schemas, mapped to a human label.
PATTERN_LABELS = {
    r"^[0-9a-fA-F-]{36}$": "UUID",
    r"^urn:h2a:subject:[A-Za-z0-9._-]+$": "subject URN",
    r"^urn:h2a:grantee:[A-Za-z0-9._-]+$": "grantee URN",
    r"^sha256:[0-9a-f]{64}$": "sha256",
    r"^P(T)?([0-9]+[HMS])+$": "ISO 8601 duration",
}


def esc(s) -> str:
    return html.escape(str(s), quote=True)


def _code(s) -> str:
    return f"<code>{esc(s)}</code>"


def _chips(values) -> str:
    return " ".join(_code(v) for v in values)


def render_type(prop: dict) -> str:
    """A readable HTML type description for one property schema."""
    if "const" in prop:
        return f'{_code(prop["const"])} <span class="mut">const</span>'

    if "enum" in prop:
        out = _chips(prop["enum"])
        if "default" in prop:
            out += f' <span class="mut">· default {_code(prop["default"])}</span>'
        return out

    t = prop.get("type")

    if isinstance(t, list):  # e.g. ["object", "null"]
        return " &#124; ".join(_code(x) for x in t)

    if t == "array":
        items = prop.get("items", {})
        if "enum" in items:
            return f'array of {_chips(items["enum"])}'
        if items.get("type") == "object":
            return "array of " + _code("object")
        label = items.get("type", "any")
        if items.get("format"):
            label += f' · {items["format"]}'
        return "array of " + _code(label)

    if t == "string":
        if "format" in prop:
            return f'{_code("string")} <span class="mut">· {esc(prop["format"])}</span>'
        if "pattern" in prop:
            lbl = PATTERN_LABELS.get(prop["pattern"], "pattern")
            return f'{_code("string")} <span class="mut">· {esc(lbl)}</span>'
        return _code("string")

    if t in ("integer", "number"):
        bound = ""
        if "exclusiveMinimum" in prop:
            bound = f' <span class="mut">· &gt; {esc(prop["exclusiveMinimum"])}</span>'
        elif "minimum" in prop:
            bound = f' <span class="mut">· &ge; {esc(prop["minimum"])}</span>'
        return f'{_code(t)}{bound}'

    if t == "boolean":
        d = ""
        if "default" in prop:
            d = f' <span class="mut">· default {_code(str(prop["default"]).lower())}</span>'
        return f'{_code("boolean")}{d}'

    return _code(t if t else "any")


def _description(prop: dict) -> str:
    desc = prop.get("description")
    if not desc and prop.get("type") == "array":
        desc = prop.get("items", {}).get("description")
    return esc(desc) if desc else '<span class="mut">—</span>'


def _nested_props(prop: dict):
    """The properties dict of a nested object or array-of-object, else None."""
    t = prop.get("type")
    if (t == "object" or (isinstance(t, list) and "object" in t)) and "properties" in prop:
        return prop["properties"], ""
    if t == "array":
        items = prop.get("items", {})
        if items.get("type") == "object" and "properties" in items:
            return items["properties"], "[]"
    return None, ""


def _expected_paths(properties: dict, prefix: str = "") -> set:
    """Every field path the JSON structure demands — the coverage spec."""
    paths = set()
    for name, prop in properties.items():
        path = f"{prefix}{name}"
        paths.add(path)
        sub, suffix = _nested_props(prop)
        if sub is not None:
            paths |= _expected_paths(sub, f"{path}{suffix}.")
    return paths


def _table(properties: dict, required: list, prefix: str, emitted: set) -> str:
    """One field table; recurses into nested objects as captioned sub-tables."""
    rows, subtables = [], []
    for name, prop in properties.items():
        path = f"{prefix}{name}"
        emitted.add(path)
        req = '<span class="req">✓</span>' if name in required else '<span class="mut">—</span>'
        rows.append(
            f"<tr><td>{_code(name)}</td><td>{render_type(prop)}</td>"
            f"<td class='req-col'>{req}</td><td>{_description(prop)}</td></tr>"
        )
        sub, suffix = _nested_props(prop)
        if sub is not None:
            caption = f"{path}{suffix}" + (" — each item" if suffix else "")
            sub_required = (prop.get("items", prop)).get("required", [])
            subtables.append(
                f'<p class="subcap">{_code(caption)}</p>'
                + _table(sub, sub_required, f"{path}{suffix}.", emitted)
            )
        elif prop.get("type") == "object" and prop.get("additionalProperties") is True:
            subtables.append(f'<p class="subcap">{_code(path)} '
                             f'<span class="mut">— open object (modality-specific keys)</span></p>')

    head = ("<table><thead><tr><th>Field</th><th>Type</th>"
            "<th class='req-col'>Req</th><th>Description</th></tr></thead><tbody>")
    return head + "".join(rows) + "</tbody></table>" + "".join(subtables)


def _conditional_notes(schema: dict) -> str:
    notes = []
    for clause in schema.get("allOf", []):
        path, const = _find_const(clause.get("if", {}).get("properties", {}))
        required = clause.get("then", {}).get("required", [])
        if path and required:
            fields = ", ".join(_code(r) for r in required)
            notes.append(f"{fields} is required when {_code(path)} = {_code(const)}")
    if not notes:
        return ""
    items = "".join(f"<li>{n}</li>" for n in notes)
    return f'<div class="cond"><strong>Conditional.</strong><ul>{items}</ul></div>'


def _find_const(properties: dict, prefix: str = ""):
    for name, prop in properties.items():
        path = f"{prefix}{name}"
        if "const" in prop:
            return path, prop["const"]
        if "properties" in prop:
            found = _find_const(prop["properties"], f"{path}.")
            if found[0]:
                return found
    return None, None


def _example_block(path: Path, reason, highlight) -> str:
    text = path.read_text(encoding="utf-8")
    if reason is None:
        summary = (f'<span class="ok">✓ validated</span> · example · '
                   f'{_code(path.name)}')
    else:
        summary = (f'<span class="bad">✗ rejected</span> · counter-example · '
                   f'{_code(path.name)} <span class="mut">— {esc(reason)}</span>')
    return (f"<details><summary>{summary}</summary>"
            f'<div class="wide">{highlight(text)}</div></details>')


def render_reference(schema_dir: Path, example_dir: Path, highlight) -> str:
    """Full HTML block: on-page nav + one section per schema. Raises on coverage mismatch."""
    toc = " ".join(f'<a href="#{s["slug"]}">{esc(s["title"])}</a>' for s in SCHEMAS)
    parts = [f'<nav class="onthispage" aria-label="On this page">'
             f'<span>On this page</span>{toc}</nav>']

    for meta in SCHEMAS:
        schema = json.loads((schema_dir / meta["file"]).read_text(encoding="utf-8"))
        emitted: set = set()
        table = _table(schema.get("properties", {}), schema.get("required", []), "", emitted)

        expected = _expected_paths(schema.get("properties", {}))
        if emitted != expected:
            missing = expected - emitted
            extra = emitted - expected
            raise AssertionError(
                f"schema {meta['file']} coverage mismatch: "
                f"missing={sorted(missing)} extra={sorted(extra)}")

        examples = "".join(
            _example_block(example_dir / fn, reason, highlight)
            for fn, reason in meta["examples"])

        parts.append(
            f'<section class="schema" id="{meta["slug"]}">'
            f'<h2>{esc(meta["title"])} {_code(meta["id_code"])} '
            f'<a class="raw" href="schemas/v0/{meta["file"]}">raw&#8202;&#8599;</a></h2>'
            f'<p class="lead">{esc(schema.get("description", ""))}</p>'
            f'{_conditional_notes(schema)}'
            f'<div class="wide">{table}</div>'
            f'{examples}'
            f'</section>')

    return "\n".join(parts)
