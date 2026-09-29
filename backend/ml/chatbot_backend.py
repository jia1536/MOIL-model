import os
import json
from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI

from .predict import predict_forecast
from .routes_map import score_zone
from .data_loader import MINES, find_mine_by_name, get_mine_operational_inputs, get_state_reserve_and_production
from .grade_lookup import get_grade_for_mine
from .companies_lookup import get_companies_for_mine
from .state_analysis import compare_states, depletion_report, compare_countries_report

router = APIRouter()
MODEL = "openai/gpt-oss-120b"
_client = None

SYSTEM_PROMPT = (
    "You are the assistant embedded in a prototype manganese exploration and "
    "operations dashboard (SIH26009). You have tools for real prospectivity "
    "scoring, production shortfall forecasts, mine grade/company lookups, "
    "state reserve comparisons, and country reserve comparisons.\n\n"
    "Rules:\n"
    "1. For any question about a specific mine, location, reserve figure, "
    "forecast, or comparison, call the relevant tool rather than answering "
    "from general knowledge. If no tool fits, say so plainly instead of "
    "inventing numbers.\n"
    "2. Do not invent geological detail (deposit geometry, mineral "
    "assemblages, structural history, exploration dates, and so on) that "
    "isn't in a tool result. If asked for that kind of detail, answer only "
    "with what the tools return, and say the rest is outside this "
    "prototype's data.\n"
    "3. Keep answers short: a few sentences for a simple question, at most "
    "a short paragraph plus a few bullet points for something with several "
    "parts. This is a chat bubble, not a report.\n"
    "4. Avoid markdown tables and heavy formatting. Plain sentences and "
    "simple '- ' bullet points only, since the chat UI does not render "
    "markdown tables or headers.\n"
    "5. State reserve, grade and forecast figures plainly as approximate, "
    "since they come from a prototype model rather than a certified survey."
)


def get_client():
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
            "description": "Compare real reserves, remaining resources, 2020-21 production, production trend and "
                "years of reserves left for two or more Indian states.",
            "parameters": {
                "type": "object",
                "properties": {"states": {"type": "array", "items": {"type": "string"}}},
                "required": ["states"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_grade_and_companies",
            "description": (
                "Get real ore grade breakdown (percent Mn content by weight) and "
                "real operating companies for a named known mine, from IBM Yearbook data."
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
            "name": "compare_countries",
            "description": (
                "Compare India's real manganese reserves and production against other "
                "countries (e.g. South Africa, Australia, China, Gabon, Brazil)."
            ),
            "parameters": {
                "type": "object",
                "properties": {"countries": {"type": "array", "items": {"type": "string"}}},
                "required": ["countries"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_reserve_depletion",
            "description": (
                "Years of proven reserves left at the current production rate for Indian states, "
                "most urgent first, with a Critical / Watch / Adequate status. Pass a state name "
                "for one state, or leave it out for all states."
            ),
            "parameters": {
                "type": "object",
                "properties": {"state": {"type": "string"}},
            },
        },
    },
]


def execute_tool(name: str, tool_input: dict) -> dict:
    if name == "get_prospectivity_at_location":
        result = score_zone(tool_input["lat"], tool_input["lng"], use_real_satellite=True)
        return {
            "prospectivity_score": result["prospectivity"]["prospectivity_score"],
            "level": result["level"],
            "confidence": result["prospectivity"]["confidence"],
            "reserve_range_tonnes": [result["prospectivity"]["reserve_min_tonnes"], result["prospectivity"]["reserve_max_tonnes"]],
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
        report = compare_states(tool_input["states"])
        return {
            "states": [
                {k: v for k, v in row.items() if k != "production_history"}
                for row in report["states"]
            ],
            "not_found": report["not_found"],
            "notes": report["notes"],
        }

    if name == "get_reserve_depletion":
        report = depletion_report(tool_input.get("state"))
        if report is None:
            return {"error": f"No reserve data for state '{tool_input.get('state')}'"}
        return report

    if name == "get_grade_and_companies":
        mine = find_mine_by_name(tool_input["mine_name"])
        if not mine:
            return {"error": f"No known mine matching '{tool_input['mine_name']}'"}
        grade = get_grade_for_mine(mine["name"])
        companies = get_companies_for_mine(mine["name"])
        if not grade:
            return {"error": f"No district-level grade/company data mapped for '{mine['name']}' yet"}
        return {"mine": mine["name"], "grade": grade, "companies": companies}

    if name == "compare_countries":
        report = compare_countries_report(tool_input["countries"])
        if not report["countries"]:
            return {"error": "No matching countries. Available: " + ", ".join(
                r["country"] for r in compare_countries_report()["countries"])}
        return report

    return {"error": f"Unknown tool {name}"}


class ChatRequest(BaseModel):
    message: str
    history: list = []  # [{"role": "user"/"assistant", "content": "..."}]


@router.post("/chat")
def chat(req: ChatRequest):
    client = get_client()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + req.history + [{"role": "user", "content": req.message}]

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
