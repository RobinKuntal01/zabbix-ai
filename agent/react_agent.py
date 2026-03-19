"""
react_agent.py — A verbose ReAct (Reason + Act) agent.

Loop:  Thought → Action → Observation  (repeat up to MAX_STEPS)
       → Final Answer

The LLM decides at each step which tool to call (or to stop).
Tools are simple stubs with predefined output for now.
"""

import json
import re
import requests
from config import OLLAMA_CHAT_URL

# ──────────────────────────────────────────────
# 1.  TOOL REGISTRY
#     Each tool is a plain Python function.
#     add_tool() registers it with a name + description
#     that the LLM sees in its system prompt.
# ──────────────────────────────────────────────

TOOL_REGISTRY: dict[str, dict] = {}

def add_tool(name: str, description: str, param_schema: str):
    """Decorator that registers a function as an agent tool."""
    def decorator(fn):
        TOOL_REGISTRY[name] = {
            "fn": fn,
            "description": description,
            "param_schema": param_schema,
        }
        return fn
    return decorator


# ── Stub tools (predefined outputs) ────────────

@add_tool(
    name="get_server_cpu",
    description="Returns the current CPU usage % for a named server.",
    param_schema='{"server_name": "<string>"}',
)
def get_server_cpu(server_name: str) -> dict:
    # Stub — replace with real Zabbix call later
    data = {
        "NM1":   {"cpu_pct": 72, "cores": 16, "status": "warning"},
        "PROD1": {"cpu_pct": 14, "cores": 32, "status": "ok"},
        "PROD2": {"cpu_pct": 91, "cores": 32, "status": "critical"},
    }
    return data.get(server_name.upper(), {"error": f"Server {server_name!r} not found"})


@add_tool(
    name="get_rack_power",
    description="Returns the current power draw (watts) for a named rack.",
    param_schema='{"rack_id": "<string>"}',
)
def get_rack_power(rack_id: str) -> dict:
    data = {
        "RACK-A1": {"watts": 4200, "capacity_watts": 5000, "utilisation_pct": 84},
        "RACK-B3": {"watts": 1800, "capacity_watts": 5000, "utilisation_pct": 36},
        "RACK-C2": {"watts": 4950, "capacity_watts": 5000, "utilisation_pct": 99},
    }
    return data.get(rack_id.upper(), {"error": f"Rack {rack_id!r} not found"})


@add_tool(
    name="list_servers_in_rack",
    description="Returns the list of servers physically installed in a given rack.",
    param_schema='{"rack_id": "<string>"}',
)
def list_servers_in_rack(rack_id: str) -> dict:
    data = {
        "RACK-A1": {"servers": ["NM1", "NM2", "NM3"]},
        "RACK-B3": {"servers": ["PROD1"]},
        "RACK-C2": {"servers": ["PROD2", "PROD3"]},
    }
    return data.get(rack_id.upper(), {"error": f"Rack {rack_id!r} not found"})


@add_tool(
    name="list_available_racks",
    description="Returns the list of all rack IDs known to the system. Call this first when the user asks about 'all racks' or when you don't know which rack IDs exist.",
    param_schema='{}',
)
def list_available_racks() -> dict:
    return {"racks": ["RACK-A1", "RACK-B3", "RACK-C2"]}


@add_tool(
    name="get_cooling_status",
    description="Returns the current inlet temperature (°C) and cooling mode for a rack.",
    param_schema='{"rack_id": "<string>"}',
)
def get_cooling_status(rack_id: str) -> dict:
    data = {
        "RACK-A1": {"inlet_temp_c": 21.4, "cooling_mode": "active", "status": "ok"},
        "RACK-B3": {"inlet_temp_c": 19.1, "cooling_mode": "passive", "status": "ok"},
        "RACK-C2": {"inlet_temp_c": 27.8, "cooling_mode": "active", "status": "warning"},
    }
    return data.get(rack_id.upper(), {"error": f"Rack {rack_id!r} not found"})


# ──────────────────────────────────────────────
# 2.  SYSTEM PROMPT BUILDER
#     Tells the LLM which tools exist and
#     exactly what JSON format to use.
# ──────────────────────────────────────────────

def _build_system_prompt() -> str:
    tool_lines = "\n".join(
        f'  • {name}: {meta["description"]}\n'
        f'    params: {meta["param_schema"]}'
        for name, meta in TOOL_REGISTRY.items()
    )

    # Pull the valid IDs directly from the stub data so they stay in sync
    known_racks   = ["RACK-A1", "RACK-B3", "RACK-C2"]
    known_servers = ["NM1", "NM2", "NM3", "PROD1", "PROD2", "PROD3"]

    return f"""You are a data center infrastructure assistant running in a ReAct loop.
At each step you MUST respond with EXACTLY ONE of these two JSON formats — nothing else.
 
FORMAT A — when you need to call a tool:
{{
  "thought": "<your reasoning about what to do next>",
  "action": "<tool_name>",
  "action_input": {{ <params matching the tool schema> }}
}}
 
FORMAT B — when you have enough information to answer:
{{
  "thought": "<final reasoning>",
  "final_answer": "<clear, concise answer for the user>"
}}
 
Available tools:
{tool_lines}
 
Known entities (use these exact IDs — do not guess or invent others):
  Racks:   {known_racks}
  Servers: {known_servers}
 
Rules:
- Use FORMAT A to call tools. Use FORMAT B only when you can fully answer the user.
- Always fill in "thought" with your reasoning — be explicit.
- ONLY call tools listed above. Never invent tool names.
- ONLY use rack/server IDs from the Known entities list above.
- If a tool returns an error, do NOT retry with a different invented name — use FORMAT B to report the error.
- Never call a tool you have already called with identical inputs.
- Respond ONLY with valid JSON. No markdown, no preamble, no trailing text.
- Plan the minimum number of tool calls needed before acting. Only call tools whose
  results are directly required to answer the question. Do not gather extra context
  that is not needed (e.g. do not list servers when the question is only about power).
"""


# ──────────────────────────────────────────────
# 3.  TOOL DISPATCHER
# ──────────────────────────────────────────────

def _dispatch(tool_name: str, tool_input: dict) -> str:
    if tool_name not in TOOL_REGISTRY:
        return json.dumps({"error": f"Unknown tool: {tool_name!r}"})
    try:
        result = TOOL_REGISTRY[tool_name]["fn"](**tool_input)
        return json.dumps(result)
    except TypeError as e:
        return json.dumps({"error": f"Bad params for {tool_name!r}: {e}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# ──────────────────────────────────────────────
# 4.  LLM CALL (Ollama / Mistral)
# ──────────────────────────────────────────────

def _call_llm(messages: list[dict]) -> str:
    response = requests.post(
        OLLAMA_CHAT_URL,
        json={
            "model": "mistral",
            "messages": messages,
            "format": "json",
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["message"]["content"]


# ──────────────────────────────────────────────
# 5.  MAIN AGENT LOOP
# ──────────────────────────────────────────────

MAX_STEPS = 6   # safety ceiling — prevents infinite loops

def run_react_agent(user_query: str) -> dict:
    """
    Run the ReAct loop for a given user query.

    Returns a dict with:
      - final_answer  (str)
      - steps         (list of verbose step dicts for the UI)
      - total_steps   (int)
    """

    print("\n" + "═" * 60)
    print(f"🤖  ReAct Agent starting")
    print(f"📝  Query: {user_query}")
    print("═" * 60)

    # Build the conversation history.
    # The agent's scratchpad IS the message history.
    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user",   "content": user_query},
    ]

    steps = []         # verbose trace for the UI
    seen_calls = set() # loop-detection: tracks (action, json_input) pairs

    for step_num in range(1, MAX_STEPS + 1):

        print(f"\n── Step {step_num} ──────────────────────────────")

        # ── LLM call ──────────────────────────────
        raw = _call_llm(messages)
        print(f"🧠  LLM raw output:\n{raw}")

        # ── Parse JSON ────────────────────────────
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            # Try to salvage JSON from inside a code block
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
            else:
                error_msg = f"LLM returned non-JSON output at step {step_num}."
                print(f"❌  {error_msg}")
                steps.append({"step": step_num, "type": "error", "content": error_msg})
                break

        thought = parsed.get("thought", "")
        print(f"💭  Thought: {thought}")

        # ── FORMAT B: final answer ─────────────────
        if "final_answer" in parsed:
            answer = parsed["final_answer"]
            print(f"\n✅  Final answer reached at step {step_num}")
            print(f"📣  {answer}")
            steps.append({
                "step":    step_num,
                "type":    "final_answer",
                "thought": thought,
                "content": answer,
            })
            return {
                "final_answer": answer,
                "steps":        steps,
                "total_steps":  step_num,
            }

        # ── FORMAT A: tool call ────────────────────
        action       = parsed.get("action", "")
        action_input = parsed.get("action_input", {})

        if not action:
            msg = "LLM produced neither 'action' nor 'final_answer'. Aborting."
            print(f"❌  {msg}")
            steps.append({"step": step_num, "type": "error", "content": msg})
            break

        print(f"🔧  Action:  {action}")
        print(f"📥  Input:   {json.dumps(action_input)}")

        # ── Loop detection ─────────────────────────
        call_key = (action, json.dumps(action_input, sort_keys=True))
        if call_key in seen_calls:
            msg = (
                f"Loop detected: '{action}' with {action_input} was already called. "
                "Stopping to avoid an infinite loop."
            )
            print(f"🔁  {msg}")
            steps.append({"step": step_num, "type": "error", "content": msg})
            break
        seen_calls.add(call_key)

        observation = _dispatch(action, action_input)
        print(f"👁️   Observation: {observation}")

        steps.append({
            "step":        step_num,
            "type":        "tool_call",
            "thought":     thought,
            "action":      action,
            "action_input": action_input,
            "observation": observation,
        })

        # ── Append to conversation so LLM sees the result ──
        # Assistant turn: the LLM's FORMAT A response
        messages.append({"role": "assistant", "content": raw})
        # User turn: we inject the tool result as a "user" message
        # (Mistral via Ollama doesn't support tool role — this is the standard workaround)
        messages.append({
            "role": "user",
            "content": (
                f"Observation from tool '{action}':\n{observation}\n\n"
                "Continue reasoning. Use FORMAT A if you need another tool, "
                "FORMAT B if you can now answer."
            ),
        })

    # ── Exhausted MAX_STEPS without a final answer ──
    fallback = (
        f"I was unable to reach a confident answer within {MAX_STEPS} steps. "
        "Here is what I found so far: "
        + "; ".join(
            f"[{s['action']} → {s['observation']}]"
            for s in steps if s["type"] == "tool_call"
        )
    )
    print(f"\n⚠️  Max steps reached. Returning partial answer.")
    steps.append({"step": MAX_STEPS + 1, "type": "max_steps", "content": fallback})
    return {"final_answer": fallback, "steps": steps, "total_steps": MAX_STEPS}