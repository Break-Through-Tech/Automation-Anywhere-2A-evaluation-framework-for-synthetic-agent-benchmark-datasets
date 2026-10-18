"""Label every task with domain, task_type, scenario and tools (for Attribute Diversity).

Design choices (write these in your report):
  * domain   -> taken from the dataset itself (folder name / given field). Not guessed by the LLM.
  * tools    -> extracted deterministically from the ground-truth action list. Not guessed by the LLM.
  * task_type, scenario -> LLM, with temperature 0, a fixed task_type classification list, and a cache
                           so a rerun gives identical labels (reproducibility criterion).

Usage:
  python scripts/label_tasks.py --dataset tau2 --tau2-root external/tau2-bench --no-llm      # free dry run
  python scripts/label_tasks.py --dataset tau2 --tau2-root external/tau2-bench --limit 10    # tiny paid test
  python scripts/label_tasks.py --dataset tau2 --tau2-root external/tau2-bench               # full run
  python scripts/label_tasks.py --dataset synthetic --synthetic-path data/                   # after load_synthetic is filled in
"""
import argparse, hashlib, json, os, re, sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()  # reads OPENAI_API_KEY, BASE_URL, MODEL_NAME from the repo's .env

sys.path.insert(0, str(Path(__file__).parent))
from classification import TASK_TYPES

TAU2_DOMAINS = ["airline", "retail", "telecom", "banking_knowledge"]
CACHE = Path("outputs/cache/labels_cache.jsonl")


# ---------------------------------------------------------------- loaders
def _text(x):
    return x if isinstance(x, str) else json.dumps(x) if x else ""


def load_tau2(root: str, domains=TAU2_DOMAINS, split="base"):
    """Load tau-bench tasks. Uses the official 'base' split so the 2285 auto-generated
    telecom variants (3 distinct purposes x personas) don't swamp everything else."""
    base = Path(root) / "data/tau2/domains"
    rows = []
    for dom in domains:
        tasks = json.load(open(base / dom / "tasks.json"))
        split_file = base / dom / "split_tasks.json"
        if split_file.exists():
            keep = set(json.load(open(split_file))[split])
            tasks = [t for t in tasks if t["id"] in keep]
        for t in tasks:
            ins = (t.get("user_scenario") or {}).get("instructions")
            ins = ins if isinstance(ins, dict) else {"task_instructions": ins}
            acts = (t.get("evaluation_criteria") or {}).get("actions") or []
            purpose = (t.get("description") or {}).get("purpose") or ""
            reason = ins.get("reason_for_call") or ""
            body = ins.get("task_instructions") or ""
            rows.append({
                "dataset": "tau2", "domain": dom, "task_id": f"{dom}:{t['id']}",
                "text": f"PURPOSE: {purpose}\nREASON FOR CALL: {reason}\nINSTRUCTIONS: {_text(body)[:1200]}",
                "tools": sorted({a["name"] for a in acts}),
                "n_actions": len(acts),
            })
    return rows


def _collect_tools(obj, found=None):
    """Find tool names anywhere inside a test case under keys like tool/tools/tool_name/tools_used."""
    found = set() if found is None else found
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() in {"tool", "tools", "tool_name", "tools_used", "expected_tools", "tool_calls"}:
                for item in (v if isinstance(v, list) else [v]):
                    if isinstance(item, str):
                        found.add(item)
                    elif isinstance(item, dict):
                        n = item.get("tool") or item.get("name") or item.get("tool_name")
                        if isinstance(n, str):
                            found.add(n)
            _collect_tools(v, found)
    elif isinstance(obj, list):
        for v in obj:
            _collect_tools(v, found)
    return found


def _parse_test_case_file(py_path: Path):
    """Read test_cases.py by PARSING it (ast), not importing it, so none of its code is run.
    Each test case is a class named TestCase<N>_..._W<k>_<easy|medium|hard> with class attributes
    test_case_id, title, workflow, input_data and expected_tool_calls (the ground-truth tool list)."""
    import ast, re
    src = py_path.read_text()
    cases = []
    for node in ast.parse(src).body:
        if not (isinstance(node, ast.ClassDef) and node.name.startswith("TestCase")):
            continue
        attrs = {}
        for stmt in node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                attrs[stmt.targets[0].id] = stmt.value

        def lit(name):
            try:
                return ast.literal_eval(attrs[name])
            except Exception:
                return None

        tools_seq = []
        calls = attrs.get("expected_tool_calls")
        if isinstance(calls, ast.List):
            for elt in calls.elts:  # only top-level "name" keys, so nested data like a customer "name" is ignored
                if isinstance(elt, ast.Dict):
                    for k, v in zip(elt.keys, elt.values):
                        if isinstance(k, ast.Constant) and k.value == "name" and isinstance(v, ast.Constant):
                            tools_seq.append(v.value)
        m = re.search(r"_(easy|medium|hard)$", node.name)
        cases.append({
            "class_name": node.name, "test_case_id": lit("test_case_id"), "title": lit("title"),
            "workflow": lit("workflow"), "input_data": lit("input_data"),
            "doc": ast.get_docstring(node) or "", "tools_seq": tools_seq,
            "source_difficulty": m.group(1) if m else "",
        })
    return cases


def _wf_id(raw):
    """'W2 - Pediatric Patient Onboarding' -> 'W2'; plain 'W2' stays 'W2'."""
    m = re.match(r"\s*(W\d+)", raw or "")
    return m.group(1) if m else (raw or "")


def _wf_name(raw):
    """'W2 - Pediatric Patient Onboarding' -> 'Pediatric Patient Onboarding'; plain 'W2' -> ''."""
    m = re.match(r"\s*W\d+\s*[-:\u2013\u2014]?\s*(.*)$", raw or "")
    return m.group(1).strip() if m else ""


def load_synthetic(path: str = "data/"):
    """Load the 64 synthetic cases from data/<agent_folder>/test_cases.py (+ test_cases.json for extra text).

    Folder name = <domain>_<category>, e.g. banking_fraud_monitoring.
    Row shape matches load_tau2, plus given_category, workflow, source_difficulty, n_tool_calls.
    tools = names in each case's expected_tool_calls (ground truth), like tau-bench's actions."""
    rows = []
    for folder in sorted(Path(path).iterdir()):
        if not (folder / "test_cases.py").exists():
            continue
        domain, _, category = folder.name.partition("_")
        json_cases = {}
        if (folder / "test_cases.json").exists():
            for wf in json.load(open(folder / "test_cases.json")).get("workflows", []):
                for tc in wf.get("test_cases", []):
                    json_cases[tc.get("test_case_id", "")] = tc
        for c in _parse_test_case_file(folder / "test_cases.py"):
            # the .json ids are the tail of the class ids, e.g. BankingFraud_W1_TC1
            jt = next((v for k, v in json_cases.items() if k and (c["test_case_id"] or "").endswith(k)), {})
            outcome = (jt.get("expected_success_outcome") or {}).get("final_status", "")
            text = (
                f"TITLE: {c['title'] or ''}\n"
                f"DESCRIPTION: {c['doc']}\n"
                f"INPUT CONDITIONS: {'; '.join(map(str, jt.get('input_conditions') or []))}\n"
                f"EXPECTED OUTCOME: {outcome}\n"
                f"INPUT DATA: {json.dumps(c['input_data'])[:500] if c['input_data'] else ''}"
            )
            # ALL_CAPS names (SUCCESS, HUMAN_IN_THE_LOOP, ...) are end-of-case outcome markers, not tools
            real = [n for n in c["tools_seq"] if not re.fullmatch(r"[A-Z][A-Z0-9_]*", n)]
            marks = [n for n in c["tools_seq"] if re.fullmatch(r"[A-Z][A-Z0-9_]*", n)]
            rows.append({
                "dataset": "synthetic", "domain": domain,
                "task_id": c["test_case_id"] or c["class_name"],
                "text": text,
                "tools": sorted(set(real)),
                "outcome_marker": "|".join(sorted(set(marks))),
                "n_actions": len(real),
                "given_category": folder.name,
                "workflow": _wf_id(c["workflow"]),
                "workflow_name": _wf_name(c["workflow"]),
                "source_difficulty": c["source_difficulty"],
            })
    return rows


# ---------------------------------------------------------------- LLM labeling
SYSTEM = (
    "You label test cases from an AI-agent benchmark. Read the case and return JSON only.\n"
    "task_type must be exactly one key from this list:\n"
    + "\n".join(f"- {k}: {v}" for k, v in TASK_TYPES.items())
    + "\nChoose task_type by the case's MAIN GOAL or outcome, not by how many steps it has; almost every case has several steps. If a case opens, onboards, creates or files something, choose new_creation even when identity, eligibility or risk checks happen along the way; choose verification_or_compliance only when the checking or the approve/deny decision IS the point of the case.\n"
    + "scenario: a short snake_case name (2-4 words) for the specific situation, e.g. "
      "'flight_cancellation', 'mms_not_sending', 'credit_card_selection'. Reuse the same name for the same "
      "kind of situation; do not invent a new name for a near-duplicate.\n"
      'Return: {"task_type": "...", "scenario": "...", "rationale": "one sentence"}'
)


def _key(row, model):
    return hashlib.sha256((model + SYSTEM + row["task_id"] + row["text"]).encode()).hexdigest()


def _load_cache():
    if not CACHE.exists():
        return {}
    return {json.loads(l)["key"]: json.loads(l) for l in open(CACHE)}


def call_llm(text, model):
    from openai import OpenAI
    client = OpenAI(base_url=os.getenv("BASE_URL") or None)  # custom endpoint from .env if set
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": text}]
    # Try the strictest settings first; some models/endpoints reject temperature, seed or JSON mode.
    attempts = [
        dict(temperature=0, seed=0, response_format={"type": "json_object"}),
        dict(response_format={"type": "json_object"}),
        dict(),
    ]
    last = None
    for extra in attempts:
        try:
            r = client.chat.completions.create(model=model, messages=msgs, **extra)
            raw = r.choices[0].message.content
            return json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        except Exception as e:
            last = e
    raise last


def label(rows, model, use_llm):
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    cache, out = _load_cache(), []
    for i, r in enumerate(rows):
        k = _key(r, model)
        if not use_llm:
            lab = {"task_type": "UNLABELED", "scenario": "UNLABELED", "rationale": ""}
        elif k in cache:
            lab = cache[k]
        else:
            try:
                lab = call_llm(r["text"], model)
            except Exception as e:  # keep going; failures show up as NEEDS_RETRY
                print(f"  ! {r['task_id']}: {e}", file=sys.stderr)
                lab = {"task_type": "NEEDS_RETRY", "scenario": "NEEDS_RETRY", "rationale": str(e)[:100]}
            else:
                if lab.get("task_type") not in TASK_TYPES:
                    lab["task_type"] = "NEEDS_RETRY"
                lab["key"] = k
                with open(CACHE, "a") as f:
                    f.write(json.dumps(lab) + "\n")
        # Team decision: scenario = the dataset's own workflow ID (W1..W9) when it has one.
        # The LLM's free-text name is kept as scenario_description. scenario_full makes the ID unique
        # across agents (W1 in fraud monitoring is not W1 in claims intake).
        wf = r.get("workflow") or ""
        out.append({**r, "task_type": lab["task_type"],
                    "scenario": wf or lab["scenario"],
                    "scenario_full": f"{r['given_category']}_{wf}" if wf and r.get("given_category") else (wf or lab["scenario"]),
                    "scenario_description": lab["scenario"],
                    "llm_rationale": lab.get("rationale", ""), "model": model if use_llm else ""})
        if use_llm and (i + 1) % 25 == 0:
            print(f"  labeled {i+1}/{len(rows)}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", choices=["tau2", "synthetic"], required=True)
    ap.add_argument("--tau2-root", default="external/tau2-bench")
    ap.add_argument("--synthetic-path", default="data/")
    ap.add_argument("--domains", nargs="*", default=TAU2_DOMAINS)
    ap.add_argument("--model", default=os.getenv("MODEL_NAME", "gpt-4.1-mini"))  # MODEL_NAME from .env
    ap.add_argument("--limit", type=int)
    ap.add_argument("--no-llm", action="store_true")
    a = ap.parse_args()

    rows = load_tau2(a.tau2_root, a.domains) if a.dataset == "tau2" else load_synthetic(a.synthetic_path)
    if a.limit:
        rows = rows[: a.limit]
    print(f"{len(rows)} tasks loaded")
    df = pd.DataFrame(label(rows, a.model, not a.no_llm))
    df["tools"] = df["tools"].apply(lambda t: "|".join(t))
    out = Path(f"outputs/labels_{a.dataset}.csv")
    df.to_csv(out, index=False)
    print(f"wrote {out}")
    print(df.groupby("domain").size().to_string())


if __name__ == "__main__":
    main()