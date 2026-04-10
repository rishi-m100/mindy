✈️ Overview
Mindy is an AI travel-planning agent that takes user specifications and constraints into account when planning an itinerary
Mindy-Bench is a synthetic benchmark designed to evaluate AI travel-planning agents. Unlike existing benchmarks that rely on live web data—which suffers from price fluctuations and "link rot"—Mindy-Bench provides a deterministic environment. This ensures that agent performance can be measured consistently and reproducibly against a verified ground-truth dataset of flights, hotels, and activities.

📊 Benchmark Key Features
Static Dataset: Includes 200,000+ flight records, 1,000+ hotels, and ~3,000 activities across 50+ US cities.

Multi-Tier Tasks: 10+ tasks ranging from Easy (single-objective retrieval) to Hard (long-horizon planning and multi-turn reasoning).

Scoring Metrics: * TSR (Task Success Rate): Binary pass/fail for valid itineraries.

CS (Constraint Satisfaction): Percentage of user requirements met.

BE (Budget Efficiency): Proximity to the optimal cost.

LS (Logistics Score): Penalties for logical inconsistencies or hallucinations.

🤖 Agent Implementation
The repository contains an autonomous agent capable of:

Natural Language Processing: Parsing user prompts into formal constraints.

Tool Calling: Dynamically executing SQL queries against a .db formatted synthetic database.

Constraint Optimization: Balancing trade-offs between budget, timing, and preferences (e.g., "cheapest flight" vs. "specific amenities").

🛠️ Tech Stack
Language: Python

Database: SQLite (.db format for reproducibility)

LLM Integration: Tool-calling and orchestration for agentic workflows.

Frameworks: Loosely based on principles from TravelBench and WebArena.

🚀 Getting Started
Clone the Repository:

Bash

git clone https://github.com/rishi-m100/mindy.git
Database Setup: Ensure the synthetic travel database is initialized in the /data directory.

Run Evaluation: Execute the evaluation script to test the agent against the 10 defined benchmark tasks.
