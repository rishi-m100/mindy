# Mindy-Bench & AI Travel Agent

Mindy is an AI travel-planning agent that takes user specifications and constraints into account when planning an itinerary
Mindy-Bench is a synthetic benchmark designed to evaluate AI travel-planning agents. Unlike existing benchmarks that rely on live web data—which suffers from price fluctuations and "link rot"—Mindy-Bench provides a deterministic environment. This ensures that agent performance can be measured consistently and reproducibly against a verified ground-truth dataset of flights, hotels, and activities.

## ✈️ Project Overview

Current AI travel agents struggle with reproducibility because real-world APIs (flights, hotels) change constantly. **Mindy-Bench** fixes this by providing:
* **Static Dataset:** 200,000+ flight records, 1,000+ hotels, and ~3,000 activities.
* **Verifiable Ground Truth:** 10+ benchmark tasks with pre-calculated optimal itineraries.
* **Multi-Tier Difficulty:** Tasks ranging from simple single-objective retrieval to complex long-horizon planning.

## 📊 Benchmark Framework

### Evaluation Metrics
Performance is evaluated across four independent metrics:
1.  **Task Success Rate (TSR):** Percentage of tasks resulting in a fully valid, grounded itinerary.
2.  **Constraint Satisfaction (CS):** Proportion of explicit and implicit user requirements met.
3.  **Budget Efficiency (BE):** How close the agent's cost is to the verified optimal cost.
4.  **Logistics Score (LS):** Deductions for inconsistencies (e.g., scheduling conflicts or unavailable hotels).

### Task Distribution
| Difficulty | Tasks | Focus |
| :--- | :--- | :--- |
| **Easy** | 4 | Single-objective reasoning (e.g., "Find the cheapest flight"). |
| **Medium** | 4 | Multi-constraint optimization (e.g., "Weekend in Miami under $800"). |
| **Hard** | 2 | Long-horizon planning and multi-turn clarifying questions. |

## 🤖 Agent Implementation

The repository also includes an autonomous agent built to navigate the Mindy-Bench environment.
* **SQL Tool Calling:** The agent translates natural language into SQL queries to interact with the `.db` synthetic database.
* **Constraint Parsing:** Automatically identifies hard and soft constraints from user prompts.
* **Current Status:** Tool calling is functional for flight data; hotel and activity tool integration is in progress.

## 🛠️ Tech Stack
* **Language:** Python
* **Database:** SQLite (`.db` format)
* **Models:** LLM-based agents with tool-calling capabilities.

## 🚀 Getting Started

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/rishi-m100/mindy.git](https://github.com/rishi-m100/mindy.git)
   cd mindy
