"""Deterministic, source-bound quote options; never paraphrase or fabricate text."""
import json
from copy import deepcopy


def source_choices(source):
    text, values = source["text"], []

    def add_lines(value):
        for line in value.splitlines():
            line = line.strip()
            if line:
                values.extend([line] if len(line) <= 600 else
                              [line[i:i+600] for i in range(0, len(line), 450)])

    def walk(value):
        if isinstance(value, str):
            if len(value) >= 12:
                add_lines(value)
        elif isinstance(value, dict):
            for child in value.values():
                walk(child)
            signature, returns = value.get("signature"), value.get("returns")
            if isinstance(signature, str) and isinstance(returns, str) and returns:
                # A partial window spanning the artificial arrow would not itself
                # be a faithful literal or full canonical signature rendering.
                values.append(f"{signature} -> {returns}")
        elif isinstance(value, list):
            for child in value:
                walk(child)

    if source.get("kind") == "type_definitions":
        # Overlapping exact windows preserve the complete code text without
        # spending an enum value on every isolated annotation/import line.
        values.extend(text[i:i+600] for i in range(0, len(text), 450))
    else:
        add_lines(text)
        try:
            walk(json.loads(text))
        except ValueError:
            pass
    return list(dict.fromkeys(v for v in values if v.strip()))


def check_schema_limits(schema):
    """Fail offline rather than send oversized Structured Outputs enums."""
    enums, characters = 0, 0

    def walk(value):
        nonlocal enums, characters
        if isinstance(value, dict):
            if "enum" in value:
                items = value["enum"]
                enums += len(items)
                size = sum(len(s) for s in items if isinstance(s, str))
                characters += size
                if len(items) > 250 and size > 15000:
                    raise ValueError("An evidence enum exceeds the string-size limit")
            for key in ("properties", "$defs"):
                characters += sum(map(len, value.get(key, {})))
            if isinstance(value.get("const"), str):
                characters += len(value["const"])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(schema)
    if enums > 1000 or characters > 120000:
        raise ValueError("Evidence schema exceeds Structured Outputs limits")
    return {"enum_values": enums, "schema_string_characters": characters}


def evidence_index(sources):
    return [{"citation_id": f"E{i:04d}", "source_id": sid, "excerpt": excerpt}
            for i, (sid, excerpt) in enumerate((s["source_id"], q)
                for s in sources for q in source_choices(s))]


def request_payload(row, source_bound=False):
    payload = deepcopy(row["payload"])
    if source_bound:
        payload["evidence_index"] = evidence_index(payload["source_catalog"])
    return payload


def resolve_evidence(value, row):
    """Expand IDs only; scores, levels, rationales and applicability stay untouched."""
    lookup = {e["citation_id"]: e for e in evidence_index(row["payload"]["source_catalog"])}
    resolved = deepcopy(value)
    assessments = [*resolved["dimensions"].values(), resolved["intended_endpoint"], *resolved["units"]]
    for assessment in assessments:
        entries = []
        for item in assessment["evidence"]:
            if set(item) != {"citation_id"} or item["citation_id"] not in lookup:
                raise ValueError("Unknown or malformed source evidence reference")
            entry = lookup[item["citation_id"]]
            entries.append({"source_id": entry["source_id"], "excerpt": entry["excerpt"]})
        assessment["evidence"] = entries
    return resolved
