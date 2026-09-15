"""
chatbot_backend.py
--------------------
Uses Groq's free tier (OpenAI-SDK-compatible, no credit card needed) instead
of the Anthropic API. Same tool-calling PRINCIPLE as before — every tool is a
real function against your actual predict.py/data_loader.py data — but the
request/response SHAPE is OpenAI's function-calling format, which differs
from Anthropic's tool_use format:
  - Tools are declared as {"type": "function", "function": {...}}, not a
    flat dict with "input_schema".
  - The model's tool call comes back as message.tool_calls (a list), not a
    content block.
  - You reply to a tool call with a message of role="tool" carrying a
    tool_call_id, not a "tool_result" content block.

Env var required: GROQ_API_KEY (free, no card — console.groq.com)
pip install openai fastapi --break-system-packages
  (Groq is accessed THROUGH the openai package, just pointed at Groq's server
  via base_url — you don't need OpenAI's own API or a key from them.)
"""

import os
import json
from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI

from predict import predict_forecast
from routes_map import score_zone
from data_loader import MINES, find_mine_by_name, get_mine_operational_inputs, get_state_reserve_and_production

router = APIRouter()
MODEL = "openai/gpt-oss-120b"  # llama-3.3-70b-versatile was decommissioned by Groq Aug 16 2026; this is their recommended replacement
_client = None


def get_client():
    """
    Lazy init — same reasoning as before: if GROQ_API_KEY isn't set yet, this
    only fails when /chat is actually called, not at import time, so an
    unset key doesn't take down your whole FastAPI app on startup.
    """
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=os.environ["GROQ_API_KEY"],
            base_url="https://api.groq.com/openai/v1",
        )
    return _client


# OpenAI/Groq function-calling schema — note the nesting under "function",
# different from Anthropic's flat {"name", "input_schema"} shape.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_prospectivity_at_location",
            "description": (
                "Get manganese prospectivity score, confidence, reserve estimate "
                "range, Mine Viability Index, and top contributing factors for a "
                "specific latitude/longitude."
            ),
            "parameters": {
                "type": "object",
                "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}},
                "required": ["lat", "lng"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_shortfall_risk_for_mine",
            "description": (
                "Get the predicted production shortfall risk for a named mine "
                "from the known mine list (e.g. 'Balaghat', 'Chikla'), using its "
                "real recent production and downtime history."
            ),
            "parameters": {
                "type": "object",
                "properties": {"mine_name": {"type": "string"}},
                "required": ["mine_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rank_high_risk_zones",
            "description": "Rank every known mine with production history by shortfall risk, most urgent first.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_state_reserves",
            "description": "Compare real reserve and 2020-21 production figures for two or more Indian states.",
            "parameters": {
                "type": "object",
                "properties": {"states": {"type": "array", "items": {"type": "string"}}},
                "required": ["states"],
            },
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> dict:
    """Unchanged from the Anthropic version — the tool logic itself doesn't
    care which model is calling it, only the wiring around it changes."""
    if name == "get_prospectivity_at_location":
        result = score_zone(tool_input["lat"], tool_input["lng"], use_real_satellite=True)
        return {
            "prospectivity_score": result["prospectivity"]["prospectivity_score"],
            "level": result["level"],
            "confidence": result["prospectivity"]["confidence"],
            "reserve_range_tonnes": [result["prospectivity"]["reserve_min"], result["prospectivity"]["reserve_max"]],
            "top_contributing_factors": result["top_features"],
            "nearest_known_mine": result["nearest_mine"],
            "viability_index": result["viability"]["viability_index"],
        }

    if name == "get_shortfall_risk_for_mine":
        mine = find_mine_by_name(tool_input["mine_name"])
        if not mine:
            return {"error": f"No known mine matching '{tool_input['mine_name']}'"}
        op_inputs = get_mine_operational_inputs(mine["id"])
        if not op_inputs:
            return {"error": f"'{mine['name']}' has no production history in the mock dataset"}
        return {"mine": mine["name"], **predict_forecast(op_inputs["forecast_input"])}

    if name == "rank_high_risk_zones":
        ranked = []
        for mine in MINES:
            op_inputs = get_mine_operational_inputs(mine["id"])
            if not op_inputs:
                continue
            forecast = predict_forecast(op_inputs["forecast_input"])
            ranked.append({"mine": mine["name"], "state": mine["state"], **forecast})
        ranked.sort(key=lambda r: {"Low": 0, "Medium": 1, "High": 2}.get(r["risk_level"], 1), reverse=True)
        return {"ranked_zones": ranked}

    if name == "compare_state_reserves":
        result = {}
        for state in tool_input["states"]:
            reserve, production = get_state_reserve_and_production(state)
            result[state] = {"remaining_reserve_tonnes": reserve, "annual_production_2020_21_tonnes": production}
        return result

    return {"error": f"Unknown tool {name}"}


class ChatRequest(BaseModel):
    message: str
    history: list = []  # [{"role": "user"/"assistant", "content": "..."}]


@router.post("/chat")
def chat(req: ChatRequest):
    client = get_client()
    messages = req.history + [{"role": "user", "content": req.message}]

    response = client.chat.completions.create(
        model=MODEL, messages=messages, tools=TOOLS, tool_choice="auto"
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        # Handle every tool call the model made in this turn (usually one,
        # but the loop covers a model that decides to call more than one).
        messages.append({"role": "assistant", "content": msg.content, "tool_calls": [
            tc.model_dump() for tc in msg.tool_calls
        ]})

        tool_results = []
        for tool_call in msg.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = execute_tool(tool_call.function.name, args)
            tool_results.append({"name": tool_call.function.name, "result": result})
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result),
            })

        final = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        return {
            "reply": final.choices[0].message.content,
            "tools_used": [r["name"] for r in tool_results],
            "tool_results": tool_results,
        }

    return {"reply": msg.content}
