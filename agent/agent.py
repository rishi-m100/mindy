import json
import os
import anthropic
from agent.tool_schemas import TOOL_SCHEMAS
from agent.tools import execute_tool
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = "You are Mindy, a travel agent. You have tools to search for flights. Only use flight_ids returned by the tools — do not ever invent or create one that doesn't exist. If you find a valid flight, summarize it for the user using the resultant data fields."

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
            return next(b.text for b in response.content if hasattr(b, "text"))

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
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
        "Find me the cheapest flight from New York to Los Angeles on June 12, 2025.",
        verbose=True
    )
    print("\n=== RESPONSE ===")
    print(response)