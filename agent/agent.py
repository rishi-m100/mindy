import json
import os
import anthropic
from agent.tool_schemas import TOOL_SCHEMAS
from agent.tools import execute_tool
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are Mindy, a travel agent. You have tools to search for flights, hotels, and activities. Only use IDs returned by the tools — do not ever invent or create one that doesn't exist.

DATABASE COVERAGE: Flight and hotel data exists from 2021-04-11 through 2026-04-11. When a user gives a date without a year (for example "June 12-15"), infer the most recent past year where data exists - so "June 12-15" means 2025-06-12 to 2025-06-15. Don't assume a future year outside the data range. If the user says "next month" or "this summer" relative to today (2026-04-11), use the closest matching dates that fall within the data range (default to 2025 for summer months).

OUTPUT RULE - STRICT: Your very last action in every response MUST be a `submit_itinerary` tool call. You are not allowed to end your turn with a text message. This applies even when:
- The user only asked for flights (pass empty hotels/activities arrays)
- You want to ask a clarifying question (put it in the 'message' field, pass empty arrays)
- You found nothing (explain in 'message', pass empty arrays and total_cost 0)
- You want to show multiple options (pick the best one for the structured fields, mention others in 'message')
Never stop with end_turn text. Always finish with submit_itinerary."""

def run_agent(user_message: str, verbose: bool = False) -> str:
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Fallback if agent failed to use submit_itinerary
            text_response = next(b.text for b in response.content if hasattr(b, "text")).strip()
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
                    return json.dumps(block.input, indent=2)

                if verbose:
                    print(f"Tool call: {block.name}({block.input})")
                result = execute_tool(block.name, block.input)
                if verbose:
                    print(f"Result: {result[:200]}")
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