"""Ablated agent — identical to agent.py but with the feasibility evaluator removed.

submit_itinerary is accepted immediately without calling verify_constraints(),
so the agent never receives constraint-violation feedback and cannot self-correct.
Used for ablation comparisons against the full agent.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
import anthropic
from pathlib import Path
from agent.tool_schemas import TOOL_SCHEMAS, CONSTRAINT_PARSER_TOOL
from agent.tools import execute_tool
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

DB_PATH = Path(__file__).parent.parent / "data" / "mindy_dataset.db"

MAX_AGENT_TURNS = 10

_CONSTRAINT_PARSER_SYSTEM = (
    "You are a constraint extraction assistant. Given a user travel request, "
    "call the extract_constraints tool to return every requirement broken into "
    "three categories: hard (non-negotiable), soft (preferences), and "
    "assumptions (inferred but not stated). Be thorough."
)


def parse_constraints(user_message: str) -> dict:
    """Make a forced-tool-use LLM call to extract structured constraints."""
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        temperature=0,
        system=_CONSTRAINT_PARSER_SYSTEM,
        tools=[CONSTRAINT_PARSER_TOOL],
        tool_choice={"type": "any"},
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "extract_constraints":
            return block.input

    return {"hard": [], "soft": [], "assumptions": []}

SYSTEM_PROMPT = """You are Mindy, a travel agent. You have tools to search for flights, hotels, and activities. Only use IDs returned by the tools — do not ever invent or create one that doesn't exist.

DATABASE COVERAGE: Flight and hotel data exists from 2021-04-11 through 2026-04-11. When a user gives a date without a year (for example "June 12-15"), infer the most recent past year where data exists - so "June 12-15" means 2025-06-12 to 2025-06-15. Don't assume a future year outside the data range. If the user says "next month" or "this summer" relative to today (2026-04-11), use the closest matching dates that fall within the data range (default to 2025 for summer months).

OUTPUT RULE - STRICT: Your very last action in every response MUST be a `submit_itinerary` tool call. You are not allowed to end your turn with a text message. This applies even when:
- The user only asked for flights (pass empty hotels/activities arrays)
- You want to ask a clarifying question (put it in the 'message' field, pass empty arrays)
- You found nothing (explain in 'message', pass empty arrays and total_cost 0)
- You want to show multiple options (pick the best one for the structured fields, mention others in 'message')
Never stop with end_turn text. Always finish with submit_itinerary.

REASONING RULE: For every flight, hotel, and activity you select in submit_itinerary, you MUST include a brief 'reason' explaining why you chose it — e.g. price, timing, rating, proximity, user preference match. This helps the user understand your recommendations."""

_OUTPUT_FIELDS = ("flights", "hotels", "activities", "total_cost",
                  "check_in", "check_out", "hotel_nights")


def _build_response(itinerary: dict, *, trace: list[dict],
                    message: str | None = None,
                    error: str | None = None) -> str:
    """Build the final JSON response with eval fields nested under 'output'."""
    output = {k: itinerary.get(k) for k in _OUTPUT_FIELDS
              if itinerary.get(k) is not None}
    for arr_key in ("flights", "hotels", "activities"):
        output.setdefault(arr_key, [])
    output.setdefault("total_cost", 0)

    resp: dict = {"output": output}
    if message or itinerary.get("message"):
        resp["message"] = message or itinerary.get("message", "")
    if error:
        resp["error"] = error
    resp["trace"] = trace
    return json.dumps(resp, indent=2)


def run_agent(user_message: str, verbose: bool = False) -> str:
    """Run the agentic loop without feasibility checking. Returns JSON string."""

    constraints = parse_constraints(user_message)
    if verbose:
        print(f"[constraints] {json.dumps(constraints, indent=2)}")

    constraints_block = (
        "\n\nPARSED CONSTRAINTS (use these to guide your search):\n"
        f"Hard (non-negotiable): {json.dumps(constraints.get('hard', []))}\n"
        f"Soft (preferences):    {json.dumps(constraints.get('soft', []))}\n"
        f"Assumptions:           {json.dumps(constraints.get('assumptions', []))}\n"
    )
    augmented_system = SYSTEM_PROMPT + constraints_block

    messages = [{"role": "user", "content": user_message}]
    trace: list[dict] = [{"step": "parse_constraints", "output": constraints}]
    turn = 0

    while True:
        turn += 1
        if turn > MAX_AGENT_TURNS:
            if verbose:
                print(f"[agent] Max turns ({MAX_AGENT_TURNS}) exceeded")
            return _build_response(
                {}, trace=trace,
                message="I ran out of planning steps. Please try a simpler query.",
                error="max turns exceeded",
            )

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            temperature=0,
            system=augmented_system,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        token_usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            text_block = next(
                (b.text for b in response.content if hasattr(b, "text")), None
            )
            if text_block is None:
                return _build_response(
                    {}, trace=trace,
                    error="agent ended without text or tool call",
                )

            text_response = text_block.strip()
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            elif text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
            return text_response.strip()

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                if block.name == "submit_itinerary":
                    itinerary = block.input

                    trace.append({
                        "turn": turn,
                        "tool": block.name,
                        "input": itinerary,
                        "output": "PASS (feasibility check skipped — ablated)",
                        "tokens": token_usage,
                    })

                    if verbose:
                        print("[ablated] submit_itinerary accepted without feasibility check")
                    return _build_response(itinerary, trace=trace)

                if verbose:
                    print(f"[tool] {block.name}({json.dumps(block.input)})")
                result = execute_tool(block.name, block.input)
                if verbose:
                    print(f"[result] {result[:200]}")

                trace.append({
                    "turn": turn,
                    "tool": block.name,
                    "input": block.input,
                    "output": json.loads(result) if result else None,
                    "tokens": token_usage,
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})


if __name__ == "__main__":
    response = run_agent(
        "NYC → LA, June 12–15",
        verbose=True
    )
    print("\n=== RESPONSE ===")
    print(response)
