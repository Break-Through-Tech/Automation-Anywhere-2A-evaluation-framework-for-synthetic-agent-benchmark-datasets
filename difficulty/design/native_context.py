"""Read-only native initial-state projections. Never execute fixture/tool code."""
import ast
import json
import re
import tomllib

VERSION = "tau2_source_context_v1"


def load_context(folder):
    path = folder / "db.json"
    if path.exists():
        data = json.loads(path.read_text())
    else:
        path = folder / "db.toml"
        data = tomllib.loads(path.read_text())
    tables, index = {}, {}
    for table, values in data.items():
        if isinstance(values, dict):
            records = list(values.items())
        elif isinstance(values, list):
            records = [(str(i), value) for i, value in enumerate(values)]
        else:
            continue
        tables[table] = dict(records)
        primary = table.rstrip("s") + "_id"
        for key, value in records:
            identifiers = [key] if isinstance(values, dict) else []
            if isinstance(value, dict) and isinstance(value.get(primary), str):
                identifiers.append(value[primary])
            for identifier in identifiers:
                if len(identifier) >= 5:
                    index[identifier] = (table, key)
                    if identifier.startswith("#"):
                        index[identifier[1:]] = (table, key)
    pattern = re.compile(r"(?<!\w)(?:" + "|".join(re.escape(k) for k in sorted(index, key=len, reverse=True)) + r")(?!\w)")
    user_path = folder / "user_db.toml"
    user_data = tomllib.loads(user_path.read_text()) if user_path.exists() else None
    return {"path": path, "data": data, "tables": tables, "index": index,
            "pattern": pattern, "user_path": user_path, "user_data": user_data}


def select_records(task, context):
    """Select explicit IDs/contacts, then relevant foreign-key dependencies.

    Account history is followed only when no explicit order/reservation/line is
    targeted. This avoids charging unrelated customer records to task complexity.
    """
    specification = {k: task.get(k) for k in ("user_scenario", "initial_state", "evaluation_criteria")}
    blob = json.dumps(specification, ensure_ascii=False)
    lower = blob.casefold()
    tables, index = context["tables"], context["index"]
    seeds = {index[m.group()] for m in context["pattern"].finditer(blob)}

    def mentioned(value):
        return isinstance(value, str) and len(value) >= 3 and bool(re.search(
            r"(?<!\w)" + re.escape(value.casefold()) + r"(?!\w)", lower))

    need_name_lookup = not any(t in {"users", "orders", "reservations"} for t, _ in seeds)
    for table in ("users", "customers", "lines"):
        for key, record in tables.get(table, {}).items():
            if not isinstance(record, dict):
                continue
            if any(mentioned(record.get(field)) for field in ("email", "phone_number")):
                seeds.add((table, key))
            if table == "users" and need_name_lookup:
                name, address = record.get("name", {}), record.get("address", {})
                if all(mentioned(v) for v in (name.get("first_name"), name.get("last_name"), address.get("zip"))):
                    seeds.add((table, key))
    focused = {table for table, _ in seeds}
    selected, pending = set(), list(sorted(seeds))

    def strings(value):
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for child in value.values():
                yield from strings(child)
        elif isinstance(value, list):
            for child in value:
                yield from strings(child)

    while pending:
        table, key = pending.pop()
        if (table, key) in selected:
            continue
        selected.add((table, key))
        record = tables[table][key]
        if not isinstance(record, dict):
            continue
        for field, value in record.items():
            if table == "users" and field in {"orders", "reservations"} and field in focused:
                continue
            if table == "customers" and field == "line_ids" and "lines" in focused:
                continue
            for identifier in strings(value):
                target = index.get(identifier)
                if target and target not in selected:
                    pending.append(target)
    dates = set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", blob))
    for table, key in selected:
        if table == "reservations":
            dates.update(f["date"] for f in tables[table][key].get("flights", []) if "date" in f)
    output = []
    for table, key in sorted(selected):
        record = tables[table][key]
        locator = f"#/{table}/{key}"
        if table == "flights" and isinstance(record, dict):
            matching = {d: value for d, value in record.get("dates", {}).items() if d in dates}
            if matching:
                record = {**record, "dates": matching}
                locator += "; dates=" + ",".join(sorted(matching))
        output.append((table, key, record, locator))
    return output


def selected_methods(path, names):
    """Return static definitions for setup/assertion semantics, never call them."""
    if not names or not path.exists():
        return ""
    text = path.read_text()
    definitions = [ast.get_source_segment(text, node) for node in ast.walk(ast.parse(text))
                   if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names]
    return "\n\n".join(filter(None, definitions))
