import json
import os
import sqlite3
import anthropic
from pathlib import Path
from agent.tool_schemas import TOOL_SCHEMAS
from agent.tools import execute_tool
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

DB_PATH = Path(__file__).parent.parent / "data" / "mindy_dataset.db"

MAX_AGENT_TURNS = 10

SYSTEM_PROMPT = """You are Mindy, a travel agent. You have tools to search for flights, hotels, and activities. Only use IDs returned by the tools — do not ever invent or create one that doesn't exist.

DATABASE COVERAGE: Flight and hotel data exists from 2021-04-11 through 2026-04-11. When a user gives a date without a year (for example "June 12-15"), infer the most recent past year where data exists - so "June 12-15" means 2025-06-12 to 2025-06-15. Don't assume a future year outside the data range. If the user says "next month" or "this summer" relative to today (2026-04-11), use the closest matching dates that fall within the data range (default to 2025 for summer months).

OUTPUT RULE - STRICT: Your very last action in every response MUST be a `submit_itinerary` tool call. You are not allowed to end your turn with a text message. This applies even when:
- The user only asked for flights (pass empty hotels/activities arrays)
- You want to ask a clarifying question (put it in the 'message' field, pass empty arrays)
- You found nothing (explain in 'message', pass empty arrays and total_cost 0)
- You want to show multiple options (pick the best one for the structured fields, mention others in 'message')
Never stop with end_turn text. Always finish with submit_itinerary."""

# ---------------------------------------------------------------------------
# Constraint verification layer
# ---------------------------------------------------------------------------

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def verify_constraints(itinerary: dict) -> list[str]:
    """Validate all IDs exist in the DB and the cost is consistent."""
    violations = []

    flight_ids = itinerary.get("flights", [])
    hotel_ids = itinerary.get("hotels", [])
    activity_ids = itinerary.get("activities", [])
    reported_cost = itinerary.get("total_cost", 0)

    computed_cost = 0.0

    with _get_conn() as conn:
        # --- Validate flight IDs ---
        for fid in flight_ids:
            row = conn.execute(
                "SELECT price, seats_available FROM flights WHERE flight_id = ?",
                (fid,),
            ).fetchone()
            if row is None:
                violations.append(f"Flight ID '{fid}' does not exist in the database.")
            else:
                if row["seats_available"] is not None and row["seats_available"] <= 0:
                    violations.append(
                        f"Flight '{fid}' has no available seats."
                    )
                computed_cost += row["price"]

        # --- Validate hotel IDs ---
        for hid in hotel_ids:
            row = conn.execute(
                "SELECT price_per_night FROM hotels WHERE hotel_id = ?",
                (hid,),
            ).fetchone()
            if row is None:
                violations.append(f"Hotel ID '{hid}' does not exist in the database.")
            else:
                computed_cost += row["price_per_night"]

        # --- Validate activity IDs ---
        for aid in activity_ids:
            row = conn.execute(
                "SELECT cost FROM activities WHERE activity_id = ?",
                (aid,),
            ).fetchone()
            if row is None:
                violations.append(
                    f"Activity ID '{aid}' does not exist in the database."
                )
            else:
                computed_cost += row["cost"]

    # --- Cost sanity check (allow small float tolerance) ---
    if (flight_ids or hotel_ids or activity_ids) and reported_cost > 0:
        if abs(computed_cost - reported_cost) > 1.0:
            violations.append(
                f"Reported total_cost (${reported_cost:.2f}) does not match "
                f"computed cost (${computed_cost:.2f}). Please recalculate."
            )

    return violations


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

def run_agent(user_message: str, verbose: bool = False) -> str:
    """Run the agentic loop. Returns JSON string of the final itinerary."""
    messages = [{"role": "user", "content": user_message}]
    trace: list[dict] = []
    turn = 0

    while True:
        turn += 1
        if turn > MAX_AGENT_TURNS:
            timeout_response = {
                "error": "max turns exceeded",
                "message": "I ran out of planning steps. Please try a simpler query.",
                "flights": [],
                "hotels": [],
                "activities": [],
                "total_cost": 0,
            }
            if verbose:
                print(f"[agent] Max turns ({MAX_AGENT_TURNS}) exceeded")
            return json.dumps({"result": timeout_response, "trace": trace}, indent=2)

        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            temperature=0,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # Record token usage for this turn
        token_usage = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }

        messages.append({"role": "assistant", "content": response.content})

        # --- end_turn fallback (fragile-safe) ---
        if response.stop_reason == "end_turn":
            text_block = next(
                (b.text for b in response.content if hasattr(b, "text")), None
            )
            if text_block is None:
                fallback = {
                    "error": "agent ended without text or tool call",
                    "message": "",
                    "flights": [],
                    "hotels": [],
                    "activities": [],
                    "total_cost": 0,
                }
                return json.dumps({"result": fallback, "trace": trace}, indent=2)

            text_response = text_block.strip()
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            elif text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]
            return text_response.strip()

        # --- tool_use handling ---
        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                # ---------- submit_itinerary with constraint check ----------
                if block.name == "submit_itinerary":
                    itinerary = block.input
                    violations = verify_constraints(itinerary)

                    trace.append({
                        "turn": turn,
                        "tool": block.name,
                        "input": itinerary,
                        "output": (
                            "PASS" if not violations else violations
                        ),
                        "tokens": token_usage,
                    })

                    if violations:
                        if verbose:
                            print(
                                f"[constraint] Violations found: {violations}"
                            )
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": (
                                f"Constraint violations found: {json.dumps(violations)}. "
                                "Please fix and resubmit."
                            ),
                        })
                        # Don't return — continue the loop so the agent can fix
                    else:
                        if verbose:
                            print("[constraint] All constraints passed ✓")
                        return json.dumps(
                            {"result": itinerary, "trace": trace}, indent=2
                        )
                    continue

                # ---------- normal tool calls ----------
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