"""Versioned packets, strict evidence validation and an explicitly authorized runner."""
from datetime import datetime, timezone
from importlib import metadata
import json
import os
from pathlib import Path

from jsonschema import Draft202012Validator

from .inputs import ADAPTER_VERSION, file_hash, unique, validate_case, verify_sources
from .rubric import (DIMENSIONS, OUTPUT_VERSION, PROMPT_VERSION, SCHEMA_VERSION, ROOT, STEP_DIMENSIONS,
                     VERSION, digest, response_schema, rubric_text, score, system_prompt)

PROTOCOL = "design_run_v1"
VALIDATOR_VERSION = "design_evidence_validation_v1.3"


def implementation_hashes():
    return {str(p.relative_to(ROOT)): file_hash(p) for p in sorted(Path(__file__).parent.glob("*.py"))}


def write_json(path, value):
    with Path(path).open("x") as handle:
        handle.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def safe_output(path):
    path = Path(path).resolve()
    protected = [ROOT / "data", ROOT / "tau2-bench"]
    if any(path == p.resolve() or path.is_relative_to(p.resolve()) or p.resolve().is_relative_to(path) for p in protected):
        raise ValueError("Output overlaps supplied sources")
    return path


def prepare_packet(rows, out, model, repeats=1, max_output_tokens=10000, reasoning_effort=None):
    """Prepare only; even a real model name never triggers a network call."""
    unique(rows)
    verify_sources(rows)
    if not model.strip() or type(repeats) is not int or not 1 <= repeats <= 5 or type(max_output_tokens) is not int or max_output_tokens < 1000:
        raise ValueError("Explicit model, 1–5 repeats and >=1000 output tokens required")
    out = safe_output(out)
    if out.exists():
        raise ValueError("Use a fresh packet directory")
    schema, prompt = response_schema(), system_prompt()
    config = {"model": model, "max_output_tokens": max_output_tokens, "store": False}
    if reasoning_effort:
        config["reasoning"] = {"effort": reasoning_effort}
    requests = []
    for row in rows:
        for repeat in range(repeats):
            api = {**config, "input": [{"role": "system", "content": prompt},
                                       {"role": "user", "content": json.dumps(row["payload"], ensure_ascii=False)}],
                   "text": {"format": {"type": "json_schema", "name": "design_judgment", "strict": True,
                                       "schema": response_schema([u["unit_id"] for u in row["payload"]["units"]])}}}
            requests.append({"request_id": row["payload"]["case_key"] + f"_r{repeat:02}",
                             "case_key": row["payload"]["case_key"], "repeat": repeat,
                             "input_sha256": row["input_sha256"], "api_request": api,
                             "request_sha256": digest(api), "preflight_errors": row["preflight_errors"]})
    manifest = {"protocol": PROTOCOL, "validator_version": VALIDATOR_VERSION, "schema_version": SCHEMA_VERSION,
                "rubric_version": VERSION, "prompt_version": PROMPT_VERSION,
                "adapter_version": ADAPTER_VERSION, "rubric_sha256": digest(rubric_text()),
                "prompt_sha256": digest(prompt), "schema_sha256": digest(schema),
                "inventory_sha256": digest(rows), "requests_sha256": digest(requests),
                "config": config, "repeats": repeats, "api_calls_during_preparation": 0,
                "n_tasks": len(rows), "n_requests": len(requests),
                "status": "prepared_not_scored", "independent_validation": False,
                "implementation_sha256": implementation_hashes()}
    try:
        manifest["openai_sdk_version"] = metadata.version("openai")
    except metadata.PackageNotFoundError:
        manifest["openai_sdk_version"] = None
    out.mkdir(parents=True)
    write_json(out / "inventory_PRIVATE_COMPARISON.json", rows)
    write_json(out / "requests.json", requests)
    write_json(out / "manifest.json", manifest)
    (out / "README.md").write_text("# Source-only numeric design packet\n\nPrepared offline; no scores or API calls yet. Send only each api_request, never the inventory/comparison labels.\nResults are provisional until paid calibration and held-out checks are reviewed.\n")
    return manifest


def load_packet(packet, check_sources=True):
    packet = Path(packet)
    manifest = json.loads((packet / "manifest.json").read_text())
    rows = json.loads((packet / "inventory_PRIVATE_COMPARISON.json").read_text())
    requests = json.loads((packet / "requests.json").read_text())
    if (manifest.get("protocol") != PROTOCOL or manifest.get("validator_version") != VALIDATOR_VERSION or
        manifest.get("schema_version") != SCHEMA_VERSION or manifest.get("rubric_version") != VERSION or
        manifest.get("prompt_version") != PROMPT_VERSION or manifest.get("adapter_version") != ADAPTER_VERSION or
        manifest.get("implementation_sha256") != implementation_hashes() or
        manifest.get("rubric_sha256") != digest(rubric_text()) or
        manifest.get("prompt_sha256") != digest(system_prompt()) or manifest.get("schema_sha256") != digest(response_schema()) or
        manifest.get("inventory_sha256") != digest(rows) or manifest.get("requests_sha256") != digest(requests)):
        raise ValueError("Frozen packet, rubric, prompt, schema or inventory changed")
    unique(rows)
    if check_sources:
        verify_sources(rows)
    else:
        for row in rows:
            validate_case(row)
    by_key = {r["payload"]["case_key"]: r for r in rows}
    if len({r["request_id"] for r in requests}) != len(requests):
        raise ValueError("Duplicate request IDs")
    for request in requests:
        row = by_key.get(request["case_key"])
        if not row or request["input_sha256"] != row["input_sha256"] or digest(request["api_request"]) != request["request_sha256"]:
            raise ValueError("Request identity/fingerprint mismatch")
        if json.loads(request["api_request"]["input"][1]["content"]) != row["payload"]:
            raise ValueError("Judge payload differs from canonical contract")
        if request["api_request"]["text"]["format"]["schema"] != response_schema([u["unit_id"] for u in row["payload"]["units"]]):
            raise ValueError("Response schema differs from task-bound unit contract")
    return manifest, rows, requests


def quotation_match_kind(excerpt, text):
    """Recognize exact text and explicitly defined structured-source renderings."""
    if not excerpt.strip():
        return None
    if excerpt in text:
        return "literal"
    try:
        parsed = json.loads(text)
    except (ValueError, TypeError):
        return None

    def contains(value):
        if isinstance(value, str):
            return "decoded_json_string" if excerpt in value else None
        if isinstance(value, dict):
            # A tool contract stores its argument signature and return annotation
            # separately. Permit only this exact, deterministic Python rendering;
            # never join arbitrary fields or infer an absent return annotation.
            sig, returns = value.get("signature"), value.get("returns")
            if isinstance(sig, str) and isinstance(returns, str) and returns and excerpt == f"{sig} -> {returns}":
                return "rendered_tool_signature"
            return next((kind for v in value.values() if (kind := contains(v))), None)
        if isinstance(value, list):
            return next((kind for v in value if (kind := contains(v))), None)
        return None

    return contains(parsed)


def quotation_in_source(excerpt, text):
    return quotation_match_kind(excerpt, text) is not None


def validate_judgment(value, row):
    Draft202012Validator(response_schema()).validate(value)
    if value["case_key"] != row["payload"]["case_key"] or value["version"] != OUTPUT_VERSION:
        raise ValueError("Response belongs to a different task/version")
    catalog = {s["source_id"]: s["text"] for s in row["payload"]["source_catalog"]}
    units = {u["unit_id"]: u for u in row["payload"]["units"]}

    def evidence(items, required=False):
        if required and not items:
            raise ValueError("Assessment needs source evidence")
        for item in items:
            if item["source_id"] not in catalog or not quotation_in_source(item["excerpt"], catalog[item["source_id"]]):
                raise ValueError("Citation is absent from the named source")

    for dimension in value["dimensions"].values():
        evidence(dimension["evidence"], value["status"] == "scored")
        if not dimension["rationale"].strip():
            raise ValueError("Dimension rationale cannot be empty")
    evidence(value["intended_endpoint"]["evidence"], value["status"] == "scored")
    seen, active = set(), []
    for unit in value["units"]:
        uid = unit["unit_id"]
        if uid in seen or uid not in units:
            raise ValueError("Unknown or duplicate assessed unit")
        seen.add(uid)
        evidence(unit["evidence"], True)
        if not unit["rationale"].strip() or not unit["applicability_rationale"].strip():
            raise ValueError("Unit applicability and difficulty require reasoning")
        if unit["applicability"] in {"required", "selected_conditional"}:
            if any(type(v) is not int for v in unit["levels"].values()):
                raise ValueError("Required-unit levels must be integers")
            active.append(unit)
        elif any(v is not None for v in unit["levels"].values()):
            raise ValueError("Unselected/context/uncertain units must have null levels")
        if unit["applicability"] == "uncertain" and not value["uncertainties"]:
            raise ValueError("Uncertain applicability needs an uncertainty note")
    if not value["score_rationale"].strip() or not value["dependency_reasoning"].strip():
        raise ValueError("Task score/dependencies need reasoning")
    if value["status"] == "scored":
        if row["preflight_errors"]:
            raise ValueError("Preflight-blocked cases cannot be scored")
        if seen != set(units):
            raise ValueError("Every source unit must be assessed")
        levels = {k: d["level"] for k, d in value["dimensions"].items()}
        if value["overall_score"] != score(levels) or type(value["overall_score"]) is not int:
            raise ValueError("Overall score differs from frozen arithmetic")
        if value["unscorable_reason"]:
            raise ValueError("Scored case cannot have an unscorable reason")
        if levels["workload"] and not active:
            raise ValueError("Nonzero workload needs required units")
        for k in STEP_DIMENSIONS:
            if any(levels[k] < u["levels"][k] for u in active):
                raise ValueError("Task dimension is lower than a required unit")
        if not value["intended_endpoint"]["description"].strip():
            raise ValueError("Intended endpoint needs a description")
    elif (value["overall_score"] is not None or any(d["level"] is not None for d in value["dimensions"].values()) or
          not value["unscorable_reason"].strip() or not value["source_quality_flags"]):
        raise ValueError("Unscorable cases need null scores and explicit source reasons")
    return value


def evidence_diagnostics(value, row):
    """Flag cross-references for review; exact same-task quotations remain mandatory.

    A milestone can legitimately supply task-specific evidence for a shared
    workflow step. Source membership alone cannot establish semantic relevance.
    """
    units = {u["unit_id"]: u for u in row["payload"]["units"]}
    diagnostics = [{"code": "unit_uses_cross_reference", "unit_id": u["unit_id"],
             "cited_source_ids": sorted({e["source_id"] for e in u["evidence"]}),
             "note": "No direct unit-source citation; inspect relevance of same-task evidence."}
            for u in value["units"]
            if not any(e["source_id"] in units[u["unit_id"]]["source_ids"] for e in u["evidence"])]
    catalog = {s["source_id"]: s["text"] for s in row["payload"]["source_catalog"]}
    assessments = [("dimension." + k, d["evidence"]) for k, d in value["dimensions"].items()]
    assessments += [("endpoint", value["intended_endpoint"]["evidence"])]
    assessments += [("unit." + u["unit_id"], u["evidence"]) for u in value["units"]]
    for location, items in assessments:
        for item in items:
            if quotation_match_kind(item["excerpt"], catalog[item["source_id"]]) == "rendered_tool_signature":
                diagnostics.append({"code": "rendered_tool_signature", "assessment": location,
                                    "source_id": item["source_id"], "excerpt": item["excerpt"],
                                    "note": "Exact signature-plus-return rendering from one tool object; not a literal quotation."})
    return diagnostics


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def read_result(packet, request, row):
    path = Path(packet) / "results" / (request["request_id"] + ".json")
    if not path.exists():
        return None
    result = json.loads(path.read_text())
    if result.get("request_sha256") != request["request_sha256"] or result.get("input_sha256") != row["input_sha256"]:
        raise ValueError("Saved result belongs to a different request/input")
    raw = Path(packet) / "raw" / (request["request_id"] + ".json")
    if not raw.exists() or file_hash(raw) != result.get("raw_sha256"):
        raise ValueError("Saved raw response changed or missing")
    if result["status"] == "validated":
        validate_judgment(result["judgment"], row)
        if (result.get("validator_version") != VALIDATOR_VERSION or
            result.get("evidence_diagnostics") != evidence_diagnostics(result["judgment"], row)):
            raise ValueError("Saved validation policy or evidence diagnostics changed")
        raw_value = json.loads(raw.read_text())
        text = "".join(part["text"] for message in raw_value.get("output", [])
                       for part in message.get("content", []) if part.get("type") == "output_text")
        if raw_value.get("status") != "completed" or json.loads(text) != result["judgment"]:
            raise ValueError("Saved judgment differs from raw response")
        if result.get("returned_model") != raw_value.get("model") or not result.get("returned_model"):
            raise ValueError("Missing or inconsistent returned model identity")
    elif result["status"] not in {"api_error", "format_error", "preflight_blocked"}:
        raise ValueError("Unsupported saved result status")
    return result


def run_packet(packet, *, authorize_paid=False, max_calls=3, client=None):
    """No implicit calls/retries. An unresolved intent is never automatically replayed."""
    if not authorize_paid:
        raise PermissionError("Paid API run requires explicit authorization; preparation is offline")
    if type(max_calls) is not int or not 1 <= max_calls <= 3:
        raise ValueError("This pilot runner permits at most three new calls per authorized invocation")
    packet = Path(packet)
    manifest, rows, requests = load_packet(packet)
    log = packet / "run_log.jsonl"
    if log.exists():
        last = json.loads(log.read_text().splitlines()[-1])
        if last["stopped_reason"] != "call_limit_or_complete":
            raise ValueError("Previous stop gate needs diagnosis; prepare a fresh reviewed packet before more paid calls")
    by_key = {r["payload"]["case_key"]: r for r in rows}
    for name in ("raw", "results", "intents"):
        (packet / name).mkdir(exist_ok=True)
    prior = [read_result(packet, req, by_key[req["case_key"]]) for req in requests]
    if any(r and r["status"] in {"api_error", "format_error"} for r in prior):
        raise ValueError("Previous failure requires diagnosis and a fresh reviewed packet; no automatic retry")
    calls, valid_scores = 0, []
    stopped = "call_limit_or_complete"
    for request, previous in zip(requests, prior):
        row = by_key[request["case_key"]]
        if previous:
            if previous["status"] == "validated" and previous["judgment"]["status"] == "scored":
                valid_scores.append(previous["judgment"]["overall_score"])
            continue
        rid = request["request_id"]
        intent = packet / "intents" / (rid + ".json")
        if intent.exists():
            raise ValueError("Interrupted/uncertain request: inspect raw response before any paid replay")
        if calls >= max_calls:
            break
        result = {"validator_version": VALIDATOR_VERSION, "request_sha256": request["request_sha256"], "input_sha256": row["input_sha256"],
                  "requested_model": manifest["config"]["model"], "started_at": utc_now()}
        raw_path = packet / "raw" / (rid + ".json")
        if request["preflight_errors"]:
            raw = {"no_api_call": True, "preflight_errors": request["preflight_errors"]}
            result.update(status="preflight_blocked", error="; ".join(request["preflight_errors"]))
        else:
            # Persist BEFORE calling. A crash must not silently duplicate a charge.
            write_json(intent, {"request_sha256": request["request_sha256"], "started_at": result["started_at"]})
            calls += 1
            try:
                if client is None:
                    from openai import OpenAI
                    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), max_retries=0, timeout=180)
                response = client.responses.create(**request["api_request"])
                raw = response.model_dump(mode="json")
                write_json(raw_path, raw)
                result.update(returned_model=raw.get("model"), response_id=raw.get("id"),
                              usage=raw.get("usage"), decoding_metadata={k: raw.get(k) for k in ("temperature", "top_p", "reasoning", "max_output_tokens")})
                try:
                    if raw.get("status") != "completed":
                        raise ValueError("Response was not completed (refusal/truncation must be inspected)")
                    judgment = json.loads(response.output_text)
                    validate_judgment(judgment, row)
                    result.update(status="validated", judgment=judgment,
                                  evidence_diagnostics=evidence_diagnostics(judgment, row))
                    if judgment["status"] == "scored":
                        valid_scores.append(judgment["overall_score"])
                except Exception as exc:
                    result.update(status="format_error", error=str(exc))
            except Exception as exc:
                # Do not store exception strings that might contain credentials or request data.
                raw = {"error_type": type(exc).__name__, "status_code": getattr(exc, "status_code", None)}
                result.update(status="api_error", error=type(exc).__name__)
        if not raw_path.exists():
            write_json(raw_path, raw)
        result.update(raw_sha256=file_hash(raw_path), finished_at=utc_now())
        write_json(packet / "results" / (rid + ".json"), result)
        if result["status"] in {"api_error", "format_error"}:
            stopped = "failure_requires_diagnosis"
            break
        if len(valid_scores) >= 3 and len(set(valid_scores[-3:])) == 1:
            stopped = "three_identical_scores_require_inspection_not_automatic_failure"
            break
        recent = [read_result(packet, req, by_key[req["case_key"]]) for req in requests[:requests.index(request)+1]]
        if len(recent) >= 2 and all(r and r["status"] == "validated" and r["judgment"]["status"] == "unscorable" for r in recent[-2:]):
            stopped = "repeated_unscorable_requires_source_diagnosis"
            break
    audit = {"new_api_calls": calls, "stopped_reason": stopped, "at": utc_now(),
             "rubric_version": VERSION, "calibration_passed": False}
    with (packet / "run_log.jsonl").open("a") as handle:
        handle.write(json.dumps(audit) + "\n")
    return audit
