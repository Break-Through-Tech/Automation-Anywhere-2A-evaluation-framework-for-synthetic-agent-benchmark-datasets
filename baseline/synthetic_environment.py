"""Local synthetic tools and a deterministic reference-trajectory evaluator.

No model is constructed on import. Ground truth is never supplied to the agent.
The oracle checks reference calls/arguments and structured terminal outcomes;
these fixtures have no database-state evaluator comparable to tau2's.
"""
import contextlib
import copy
import importlib.util
import inspect
import io
import json
import sys
import types
import threading
from pathlib import Path
from typing import Optional

from pydantic import ConfigDict, create_model

ROOT = Path(__file__).resolve().parents[1]
END_TOOLS = {"SUCCESS", "FAILED", "CANCELLED"}
SYSTEM_TOOLS = END_TOOLS | {"HUMAN_IN_THE_LOOP"}
# Natural-language summaries may be paraphrased. IDs, flags, amounts, and
# structured result data are still compared against the reference.
FREE_TEXT = {"message", "ai_message", "content", "description", "rationale", "notes"}
TOOL_LOCK = threading.RLock()


class SyntheticSystemTools:
    def SUCCESS(self, message: str, result_data: Optional[dict] = None) -> dict:
        """Signal completion and provide structured result_data for the workflow."""
        return {"exit_status": "success", "message": message, "data": result_data}

    def FAILED(self, message: str, error_details: Optional[dict] = None) -> dict:
        """Signal that the workflow failed."""
        return {"exit_status": "failed", "message": message, "error": error_details}

    def CANCELLED(self, message: str, reason: Optional[str] = None) -> dict:
        """Signal that the workflow was cancelled."""
        return {"exit_status": "cancelled", "message": message, "reason": reason}

    def HUMAN_IN_THE_LOOP(self, ai_message: str) -> dict:
        """Escalate to a human supervisor; a fixed acknowledgement is returned."""
        return {"exit_status": "escalated", "ai_message": ai_message,
                "human_response": "Request acknowledged and escalated to human supervisor."}


def load_cases(data_dir=ROOT / "data"):
    """Import fixtures with a local system-tool base, avoiding global LLM clients."""
    old = sys.modules.get("system_tools_base")
    stub = types.ModuleType("system_tools_base")
    stub.SystemToolsBaseClass = SyntheticSystemTools
    sys.modules["system_tools_base"] = stub
    cases = []
    try:
        for path in sorted(Path(data_dir).glob("*/test_cases.py")):
            name = f"_synthetic_baseline_{path.parent.name}"
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            for attr, cls in vars(module).items():
                if attr.startswith("TestCase") and inspect.isclass(cls):
                    cases.append((path.parent.name, cls))
    finally:
        if old is None:
            sys.modules.pop("system_tools_base", None)
        else:
            sys.modules["system_tools_base"] = old
    keys = [(domain, cls.test_case_id) for domain, cls in cases]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate synthetic task IDs")
    return sorted(cases, key=lambda pair: (pair[0], pair[1].test_case_id))


def tools_for(instance):
    tools = {}
    schemas = []
    for name, method in inspect.getmembers(instance, inspect.ismethod):
        if name.startswith("_"):
            continue
        fields = {}
        for parameter in inspect.signature(method).parameters.values():
            annotation = parameter.annotation if parameter.annotation is not inspect.Parameter.empty else object
            default = ... if parameter.default is inspect.Parameter.empty else parameter.default
            fields[parameter.name] = (annotation, default)
        # Match the existing LangChain runner's handling of extra nested
        # TypedDict fields. extra="forbid" propagates into nested schemas and
        # incorrectly rejects fields such as returned insurance eligibility.
        model = create_model(f"{name}_arguments", __config__=ConfigDict(extra="ignore"), **fields)
        tools[name] = (method, model)
        # Keep the exposed tool contract byte-identical to the initial run;
        # unknown top-level function arguments are still rejected below.
        schema = dict(sorted({**model.model_json_schema(), "additionalProperties": False}.items()))
        schemas.append({"type": "function", "function": {
            "name": name, "description": inspect.getdoc(method) or f"Execute {name}",
            "parameters": schema}})
    return tools, schemas


def execute(tools, action):
    """Only execute declared mock tools, never eval/exec model-produced code."""
    name, arguments = action["name"], action["arguments"]
    event = {"name": name, "arguments": copy.deepcopy(arguments), "error": False}
    try:
        if name not in tools:
            raise ValueError(f"Unknown tool: {name}")
        method, model = tools[name]
        unknown = set(arguments) - set(model.model_fields)
        if unknown:
            raise ValueError(f"Unknown function arguments: {sorted(unknown)}")
        # Retain nested TypedDict/dict structures rather than converting them to JSON strings.
        validated = model.model_validate(arguments).model_dump()
        with TOOL_LOCK, contextlib.redirect_stdout(io.StringIO()):
            output = method(**validated)
        event["output"] = output
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        event["error"] = True
        event["output"] = {"error": type(exc).__name__, "message": str(exc)}
    return event


def subset_matches(expected, actual):
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all((key in FREE_TEXT and isinstance(value, str)) or
                   (key in actual and subset_matches(value, actual[key]))
                   for key, value in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(expected) == len(actual) and all(
            subset_matches(e, a) for e, a in zip(expected, actual))
    if isinstance(expected, bool):
        return type(actual) is bool and actual == expected
    return expected == actual


def reference_preflight(case):
    """Run the reference against unmodified mocks before spending model tokens."""
    tools, _ = tools_for(case())
    issues = []
    for index, call in enumerate(case.expected_tool_calls):
        event = execute(tools, {"name": call["name"], "arguments": call.get("tool_inputs", {})})
        if event["error"]:
            issues.append({"step": index, "tool": call["name"], **event["output"]})
    return issues


def evaluate_trajectory(case, events, write_tools, reference_issues=None):
    """Return None for an invalid reference, 0/1 for an evaluable attempt.

    Required calls must occur in order with expected structured arguments.
    Extra reads are allowed; extra successful writes are rejected. A bare
    SUCCESS call cannot pass. Descriptive text fields may be paraphrased.
    """
    if reference_issues:
        return {"reward": None, "status": "invalid_reference", "issues": reference_issues}
    expected = case.expected_tool_calls
    successful = [event for event in events if not event["error"]]
    matched = []
    cursor = 0
    for call in expected:
        found = None
        for index in range(cursor, len(successful)):
            event = successful[index]
            if call["name"] == event["name"] and subset_matches(call.get("tool_inputs", {}), event["arguments"]):
                found = index
                break
        if found is None:
            return {"reward": 0, "status": "failed_reference", "missing_tool": call["name"],
                    "matched_calls": len(matched), "required_calls": len(expected)}
        matched.append(found)
        cursor = found + 1
    extra_writes = [e["name"] for i, e in enumerate(successful)
                    if e["name"] in write_tools and i not in matched]
    if extra_writes:
        return {"reward": 0, "status": "unexpected_write", "tools": extra_writes}
    return {"reward": 1, "status": "passed_reference", "matched_calls": len(matched)}
