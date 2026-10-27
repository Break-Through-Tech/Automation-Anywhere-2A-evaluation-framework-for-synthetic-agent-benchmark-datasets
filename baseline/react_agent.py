#!/usr/bin/env python3
"""Baseline ReAct agent for tau2-bench (Difficulty metric).

The model writes plain text in a fixed format:

    Thought:
    <one line of reasoning>
    Action:
    {"name": "<tool name or respond>", "arguments": {...}}

We parse the Action. "respond" becomes a message to the user; anything else
becomes a real tool call that tau2 executes. The model never gets native
function calling, so the Thought is always produced before acting. This is
the same ReAct style the original tau-bench used for its baseline.

The prompt below is FIXED. If you change it, bump baseline_version in
baseline_config.yaml so old and new results are never mixed.

How it runs: this file registers the agent as "react_agent" and then hands
off to tau2's normal CLI, so nothing inside tau2-bench is edited. From the
tau2-bench folder:

    uv run python ../baseline/react_agent.py run --domain airline --agent react_agent ...

run_baseline.py does this for you via tau2_cmd in baseline_config.yaml.
Print the exact prompt with:

    uv run python ../baseline/react_agent.py --print-prompt
"""
import json
import re
import sys
from typing import List, Optional

from pydantic import BaseModel

from tau2.agent.base.llm_config import LLMConfigMixin
from tau2.agent.base_agent import HalfDuplexAgent, is_valid_agent_history_message
from tau2.data_model.message import (
    APICompatibleMessage,
    AssistantMessage,
    Message,
    MultiToolMessage,
    SystemMessage,
    ToolCall,
    ToolMessage,
    UserMessage,
)
from tau2.environment.tool import Tool
from tau2.utils.llm_utils import generate

AGENT_NAME = "react_agent"
RESPOND_ACTION = "respond"

REACT_INSTRUCTION = """
You are a customer service agent. Help the user by following the <policy> and using the <tools> below.

At every step, reply in exactly this format and nothing else:

Thought:
<one line of reasoning about what to do next>
Action:
{"name": <tool name or "respond">, "arguments": <arguments as a JSON object>}

Rules:
- Exactly one Action per step. The Action must be valid JSON on a single line.
- To talk to the user, use {"name": "respond", "arguments": {"content": "<your message>"}}.
- To call a tool, use its exact name and the arguments its schema asks for.
- After a tool call you will see its result as "Tool output: ...". Use it in your next Thought.
- Never invent or guess argument values. Ask the user if you are missing something.
- Always follow the policy.
""".strip()

SYSTEM_PROMPT = """
<instructions>
{instruction}
</instructions>
<policy>
{domain_policy}
</policy>
<tools>
{tools}
</tools>
""".strip()

ACTION_RE = re.compile(r"Action:\s*(\{.*\})", re.DOTALL)


def render_prompt(domain_policy: str, tools: List[Tool]) -> str:
    tool_schemas = [t.openai_schema for t in tools]
    return SYSTEM_PROMPT.format(
        instruction=REACT_INSTRUCTION,
        domain_policy=domain_policy,
        tools=json.dumps(tool_schemas, indent=2),
    )


def parse_action(text: str) -> Optional[dict]:
    """Pull the Action JSON out of the model's text. Returns None if it can't."""
    match = ACTION_RE.search(text or "")
    if not match:
        return None
    raw = match.group(1).strip()
    # Models sometimes add text after the JSON; trim back to the last brace that parses.
    for end in range(len(raw), 0, -1):
        if raw[end - 1] != "}":
            continue
        try:
            action = json.loads(raw[:end])
        except json.JSONDecodeError:
            continue
        if isinstance(action, dict) and isinstance(action.get("name"), str):
            if not isinstance(action.get("arguments"), dict):
                action["arguments"] = {}
            return action
    return None


class ReActAgentState(BaseModel):
    system_messages: list[SystemMessage]
    # Text-only transcript the model sees, including its own Thoughts.
    transcript: list[APICompatibleMessage]
    step: int = 0
    parse_failures: int = 0


class ReActAgent(LLMConfigMixin, HalfDuplexAgent[ReActAgentState]):
    def __init__(self, tools: List[Tool], domain_policy: str, llm: str, llm_args: Optional[dict] = None):
        super().__init__(tools=tools, domain_policy=domain_policy, llm=llm, llm_args=llm_args)

    @property
    def system_prompt(self) -> str:
        return render_prompt(self.domain_policy, self.tools)

    def get_init_state(self, message_history: Optional[list[Message]] = None) -> ReActAgentState:
        message_history = message_history or []
        assert all(is_valid_agent_history_message(m) for m in message_history), (
            "Message history must contain only AssistantMessage, UserMessage, or ToolMessage."
        )
        transcript = []
        for m in message_history:
            transcript.extend(self._to_transcript(m))
        return ReActAgentState(
            system_messages=[SystemMessage(role="system", content=self.system_prompt)],
            transcript=transcript,
        )

    @staticmethod
    def _to_transcript(message: Message) -> list[APICompatibleMessage]:
        """Turn an incoming tau2 message into text-only messages for the model."""
        if isinstance(message, MultiToolMessage):
            return [m for tm in message.tool_messages for m in ReActAgent._to_transcript(tm)]
        if isinstance(message, ToolMessage):
            prefix = "Tool error: " if message.error else "Tool output: "
            return [UserMessage(role="user", content=prefix + (message.content or ""))]
        if isinstance(message, UserMessage):
            return [UserMessage(role="user", content=f"User: {message.content or ''}")]
        if isinstance(message, AssistantMessage):
            # Only used when resuming from history; we no longer have the Thought.
            if message.is_tool_call():
                tc = message.tool_calls[0]
                text = "Action:\n" + json.dumps({"name": tc.name, "arguments": tc.arguments})
            else:
                text = "Action:\n" + json.dumps(
                    {"name": RESPOND_ACTION, "arguments": {"content": message.content or ""}}
                )
            return [AssistantMessage(role="assistant", content=text)]
        return []

    def generate_next_message(self, message, state: ReActAgentState):
        if isinstance(message, UserMessage) and message.is_audio:
            raise ValueError("ReActAgent only supports text.")
        state.transcript.extend(self._to_transcript(message))

        llm_reply = generate(
            model=self.llm,
            messages=state.system_messages + state.transcript,
            tools=None,
            call_name="react_agent_response",
            **self.llm_args,
        )
        text = llm_reply.content or ""
        # The model sees its own full Thought + Action next turn.
        state.transcript.append(AssistantMessage(role="assistant", content=text or "(empty)"))

        action = parse_action(text)
        meta = dict(
            cost=llm_reply.cost,
            usage=llm_reply.usage,
            raw_data=llm_reply.raw_data,
            generation_time_seconds=llm_reply.generation_time_seconds,
        )
        state.step += 1

        if action is None:
            # Couldn't parse an Action: send the raw text to the user so the run continues.
            state.parse_failures += 1
            content = text.strip() or "Sorry, could you repeat that?"
            out = AssistantMessage(role="assistant", content=content, **meta)
        elif action["name"] == RESPOND_ACTION:
            content = str(action["arguments"].get("content", "")).strip() or text.strip()
            out = AssistantMessage(role="assistant", content=content or "...", **meta)
        else:
            call = ToolCall(
                id=f"react_{state.step}",
                name=action["name"],
                arguments=action["arguments"],
                requestor="assistant",
            )
            out = AssistantMessage(role="assistant", content=None, tool_calls=[call], **meta)
        return out, state


def create_react_agent(tools, domain_policy, **kwargs):
    return ReActAgent(
        tools=tools,
        domain_policy=domain_policy,
        llm=kwargs.get("llm"),
        llm_args=kwargs.get("llm_args"),
    )


def register():
    from tau2.registry import registry

    if registry.get_agent_factory(AGENT_NAME) is None:
        registry.register_agent_factory(create_react_agent, AGENT_NAME)


def main():
    if "--print-prompt" in sys.argv:
        # Prompt template with placeholders; policy and tools are filled per domain.
        print(SYSTEM_PROMPT.format(instruction=REACT_INSTRUCTION, domain_policy="{domain_policy}", tools="{tools}"))
        return
    register()
    from tau2.cli import main as tau2_main

    tau2_main()


if __name__ == "__main__":
    main()
