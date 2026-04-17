#!/usr/bin/env python3
"""
Mindy Bench - Benchmarking script for Mindy AI Travel Agent
3 metrics are covered
- Constraint Satisfaction (CS): 0.0 - 1.0
- Budget Efficiency (BE): 0.0 - 1.0
- Logistics Score (LS): 0.0 - 1.0
"""

from __future__ import annotations

import json
import sqlite3
import os
from pathlib import Path
from typing import Any
from dataclasses import dataclass, asdict
import sys

# Set the database path for benchmarking BEFORE importing agent modules
# This ensures the agent only queries the benchmark database
BENCHMARK_DB_PATH = Path(__file__).parent.parent / "data" / "mindy_dataset_v3.db"
os.environ["MINDY_DB_PATH"] = str(BENCHMARK_DB_PATH)

# Add parent directory to path to import agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.agent import run_agent
from agent.tools import DB_PATH


@dataclass
class BenchmarkTask:
    """Defines a benchmark task with expected criteria."""
    task_id: str
    name: str
    user_prompt: str
    constraints: dict[str, Any]
    ground_truth: dict[str, Any]
    success_criteria: dict[str, Any]


@dataclass
class TaskScore:
    """Scores for a single task evaluation."""
    task_id: str
    task_name: str
    constraint_satisfaction: float  # 0.0 - 1.0
    budget_efficiency: float        # 0.0 - 1.0
    logistics_score: float          # 0.0 - 1.0
    details: dict[str, Any]
    agent_response: dict[str, Any] | None = None  # Full agent JSON response



# EASY BENCHMARK TASKS (3 tasks)


EASY_TASKS = [
    BenchmarkTask(
        task_id="easy_01",
        name="Find Cheapest Flight in Time Period",
        user_prompt="Find the cheapest flight from Chicago (ORD) to Seattle (SEA) on June 10th, 2025.",
        constraints={
            "origin": "ORD",
            "destination": "SEA",
            "depart_date": "2025-07-01",
            "optimization": "min_price"
        },
        ground_truth={
            "type": "flight",
            "origin_city": "Chicago",
            "destination_city": "Seattle",
            "date": "2025-06-10"
        },
        success_criteria={
            "must_have_flight": True,
            "correct_route": True,
            "correct_date": True,
            "is_cheapest": True,
            "has_availability": True
        }
    ),

    BenchmarkTask(
        task_id="easy_02",
        name="Find Hotel with 1 Amenity Requirement",
        user_prompt="I need a hotel in New York for June 10th, 2025 that has a gym",
        constraints={
            "city": "New York",
            "check_in_date": "2025-10-05",
            "required_amenities": ["gym"]
        },
        ground_truth={
            "type": "hotel",
            "city": "New York",
            "check_in": "2025-06-10",
            "required_amenity": "gym"
        },
        success_criteria={
            "must_have_hotel": True,
            "correct_city": True,
            "correct_date": True,
            "has_gym": True,
            "has_availability": True
        }
    ),

    BenchmarkTask(
        task_id="easy_03",
        name="Find Flight within Specific Time Constraint",
        user_prompt="Find a flight from New York (JFK) to Los Angeles (LAX) on June 11th, 2025 that arrives before 4:00 PM.",
        constraints={
            "origin": "JFK",
            "destination": "LAX",
            "depart_date": "2025-09-15",
            "arrive_before": "14:00"
        },
        ground_truth={
            "type": "flight",
            "origin_city": "New York",
            "destination_city": "Los Angeles",
            "date": "2025-06-11",
            "max_arrival_time": "14:00"
        },
        success_criteria={
            "must_have_flight": True,
            "correct_route": True,
            "correct_date": True,
            "arrives_on_time": True,
            "has_availability": True
        }
    ),
]

# SCORING FUNCTIONS
def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def calculate_constraint_satisfaction(
    task: BenchmarkTask,
    agent_output: dict
) -> tuple[float, dict]:
    """
    Calculate Constraint Satisfaction score (0.0 - 1.0).
    Returns (score, details_dict).
    """
    output = agent_output.get("output", {})
    criteria = task.success_criteria
    details = {}

    total_constraints = len(criteria)
    met_constraints = 0

    with _get_conn() as conn:
        if task.ground_truth["type"] == "flight":
            flights = output.get("flights", [])

            # Must have flight
            if criteria.get("must_have_flight"):
                if flights:
                    met_constraints += 1
                    details["has_flight"] = True
                else:
                    details["has_flight"] = False

            if flights:
                flight_id = flights[0]["id"] if isinstance(flights[0], dict) else flights[0]
                flight_row = conn.execute(
                    """SELECT f.*, ao.city as origin_city, ad.city as destination_city
                       FROM flights f
                       JOIN airports ao ON f.origin = ao.iata
                       JOIN airports ad ON f.destination = ad.iata
                       WHERE f.flight_id = ?""",
                    (flight_id,)
                ).fetchone()

                if flight_row:
                    # Correct route
                    if criteria.get("correct_route"):
                        origin_match = (
                            flight_row["origin_city"] == task.ground_truth.get("origin_city") or
                            flight_row["origin"] == task.constraints.get("origin")
                        )
                        dest_match = (
                            flight_row["destination_city"] == task.ground_truth.get("destination_city") or
                            flight_row["destination"] == task.constraints.get("destination")
                        )
                        if origin_match and dest_match:
                            met_constraints += 1
                            details["correct_route"] = True
                        else:
                            details["correct_route"] = False

                    # Correct date
                    if criteria.get("correct_date"):
                        if flight_row["depart_date"] == task.ground_truth.get("date"):
                            met_constraints += 1
                            details["correct_date"] = True
                        else:
                            details["correct_date"] = False

                    # Cheapest check
                    if criteria.get("is_cheapest"):
                        cheapest = conn.execute(
                            """SELECT MIN(price) as min_price FROM flights f
                               JOIN airports ao ON f.origin = ao.iata
                               JOIN airports ad ON f.destination = ad.iata
                               WHERE (LOWER(ao.city) = LOWER(?) OR f.origin = ?)
                                 AND (LOWER(ad.city) = LOWER(?) OR f.destination = ?)
                                 AND f.depart_date = ?
                                 AND f.seats_available > 0""",
                            (
                                task.ground_truth.get("origin_city"),
                                task.constraints.get("origin"),
                                task.ground_truth.get("destination_city"),
                                task.constraints.get("destination"),
                                task.ground_truth.get("date")
                            )
                        ).fetchone()

                        if cheapest and cheapest["min_price"] is not None and abs(flight_row["price"] - cheapest["min_price"]) < 1.0:
                            met_constraints += 1
                            details["is_cheapest"] = True
                            details["optimal_price"] = cheapest["min_price"]
                        else:
                            details["is_cheapest"] = False
                            details["optimal_price"] = cheapest["min_price"] if cheapest and cheapest["min_price"] is not None else None

                    # Time constraint check
                    if criteria.get("arrives_on_time"):
                        max_time = task.ground_truth.get("max_arrival_time")
                        if flight_row["arrive_time"] <= max_time:
                            met_constraints += 1
                            details["arrives_on_time"] = True
                        else:
                            details["arrives_on_time"] = False

                    # Availability
                    if criteria.get("has_availability"):
                        if flight_row["seats_available"] > 0:
                            met_constraints += 1
                            details["has_availability"] = True
                        else:
                            details["has_availability"] = False

        elif task.ground_truth["type"] == "hotel":
            hotels = output.get("hotels", [])

            # Must have hotel
            if criteria.get("must_have_hotel"):
                if hotels:
                    met_constraints += 1
                    details["has_hotel"] = True
                else:
                    details["has_hotel"] = False

            if hotels:
                hotel_id = hotels[0]["id"] if isinstance(hotels[0], dict) else hotels[0]
                hotel_row = conn.execute(
                    "SELECT * FROM hotels WHERE hotel_id = ?",
                    (hotel_id,)
                ).fetchone()

                if hotel_row:
                    # Correct city
                    if criteria.get("correct_city"):
                        if hotel_row["city"] == task.ground_truth.get("city"):
                            met_constraints += 1
                            details["correct_city"] = True
                        else:
                            details["correct_city"] = False

                    # Has required amenity (gym)
                    if criteria.get("has_gym"):
                        amenities_str = hotel_row["amenities"] or ""
                        if "gym" in amenities_str.lower():
                            met_constraints += 1
                            details["has_gym"] = True
                        else:
                            details["has_gym"] = False

                    # Availability check
                    if criteria.get("has_availability") and criteria.get("correct_date"):
                        check_in = task.ground_truth.get("check_in")
                        avail = conn.execute(
                            """SELECT 1 FROM hotel_availability
                               WHERE hotel_id = ?
                                 AND check_in <= ?
                                 AND check_out > ?
                                 AND rooms_left > 0""",
                            (hotel_id, check_in, check_in)
                        ).fetchone()

                        if avail:
                            met_constraints += 1
                            details["has_availability"] = True
                        else:
                            details["has_availability"] = False

                    # Correct date
                    if criteria.get("correct_date"):
                        if details.get("has_availability", False):
                            met_constraints += 1
                            details["correct_date"] = True
                        else:
                            details["correct_date"] = False

    score = met_constraints / total_constraints if total_constraints > 0 else 0.0
    details["met_constraints"] = met_constraints
    details["total_constraints"] = total_constraints

    return score, details


def calculate_budget_efficiency(
    agent_output: dict,
    constraint_details: dict
) -> tuple[float, dict]:
    """
    Calculate Budget Efficiency score (0.0 - 1.0).
    Formula: 1.0 - ((agent_cost - optimal_cost) / budget)
    """
    output = agent_output.get("output", {})
    details = {}

    agent_cost = output.get("total_cost", 0)
    details["agent_cost"] = agent_cost

    optimal_price = constraint_details.get("optimal_price")
    optimal_cost = optimal_price if optimal_price is not None else agent_cost
    details["optimal_cost"] = optimal_cost

    # generous budget for easy tasks
    budget = max(optimal_cost * 10, 5000) if optimal_cost is not None and optimal_cost > 0 else 5000
    details["budget"] = budget

    if agent_cost > budget:
        score = 0.0
        details["over_budget"] = True
    else:
        if budget > 0:
            score = 1.0 - ((agent_cost - optimal_cost) / budget)
            score = max(0.0, min(1.0, score))
        else:
            score = 1.0 if agent_cost == optimal_cost else 0.0
        details["over_budget"] = False

    return score, details


def calculate_logistics_score(agent_output: dict) -> tuple[float, dict]:
    """
    Calculate Logistics Score (0.0 - 1.0).
    Starts at 1.0, deducts 0.1 for each logical inconsistency.
    """
    output = agent_output.get("output", {})
    score = 1.0
    violations = []

    # Check for errors
    if agent_output.get("error"):
        score -= 0.3
        violations.append(f"Agent error: {agent_output['error']}")

    # Check date consistency
    check_in = output.get("check_in")
    check_out = output.get("check_out")

    if check_in and check_out:
        if check_out <= check_in:
            score -= 0.2
            violations.append("Check-out date not after check-in date")

    # Check hotel nights
    hotel_nights = output.get("hotel_nights", 0)
    if check_in and check_out and hotel_nights > 0:
        from datetime import datetime
        try:
            ci = datetime.strptime(check_in, "%Y-%m-%d")
            co = datetime.strptime(check_out, "%Y-%m-%d")
            expected_nights = (co - ci).days
            if abs(hotel_nights - expected_nights) > 0:
                score -= 0.1
                violations.append(f"Hotel nights mismatch")
        except ValueError:
            score -= 0.1
            violations.append("Invalid date format")

    score = max(0.0, score)

    details = {
        "violations": violations,
        "violation_count": len(violations)
    }

    return score, details


def evaluate_task(task: BenchmarkTask, agent_output: dict) -> TaskScore:
    """Evaluate a single task and return scores."""

    cs_score, cs_details = calculate_constraint_satisfaction(task, agent_output)
    be_score, be_details = calculate_budget_efficiency(agent_output, cs_details)
    ls_score, ls_details = calculate_logistics_score(agent_output)

    all_details = {
        "constraint_satisfaction": cs_details,
        "budget_efficiency": be_details,
        "logistics": ls_details
    }

    return TaskScore(
        task_id=task.task_id,
        task_name=task.name,
        constraint_satisfaction=cs_score,
        budget_efficiency=be_score,
        logistics_score=ls_score,
        details=all_details,
        agent_response=agent_output  # Save full agent response
    )


# run benchmark
def run_benchmark(tasks: list[BenchmarkTask] = None, verbose: bool = True, num_runs: int = 3) -> dict:
    """Run benchmark on all tasks and return results."""
    if tasks is None:
        tasks = EASY_TASKS

    # Verify agent is using the correct database
    if verbose:
        print(f"Benchmark Database: {BENCHMARK_DB_PATH}")
        print(f"Agent Database:     {DB_PATH}")
        if str(DB_PATH) != str(BENCHMARK_DB_PATH):
            print("WARNING: Agent is using a different database than benchmark!")
        else:
            print("different database\n")

    results = []

    for i, task in enumerate(tasks, 1):
        if verbose:
            print(f"\n{'='*70}")
            print(f"Task {i}/{len(tasks)}: {task.name}")
            print(f"{'='*70}")
            print(f"Prompt: {task.user_prompt}")
            print(f"\nRunning agent {num_runs} times...")

        # Run the task multiple times
        run_scores = []
        for run_num in range(1, num_runs + 1):
            if verbose:
                print(f"\n  Run {run_num}/{num_runs}...")

            try:
                agent_response = run_agent(task.user_prompt, verbose=False)
                agent_output = json.loads(agent_response)
            except Exception as e:
                if verbose:
                    print(f"  ERROR: Agent failed - {e}")
                agent_output = {
                    "output": {},
                    "error": str(e)
                }

            score = evaluate_task(task, agent_output)
            run_scores.append(score)

            if verbose:
                print(f"  CS: {score.constraint_satisfaction:.3f} | BE: {score.budget_efficiency:.3f} | LS: {score.logistics_score:.3f}")

        # Calculate average scores across all runs
        avg_cs = sum(s.constraint_satisfaction for s in run_scores) / len(run_scores)
        avg_be = sum(s.budget_efficiency for s in run_scores) / len(run_scores)
        avg_ls = sum(s.logistics_score for s in run_scores) / len(run_scores)

        # Create averaged task score (using the last run's details and agent_response as representative)
        avg_score = TaskScore(
            task_id=task.task_id,
            task_name=task.name,
            constraint_satisfaction=avg_cs,
            budget_efficiency=avg_be,
            logistics_score=avg_ls,
            details={
                "average_of_runs": num_runs,
                "individual_runs": [
                    {
                        "run": idx + 1,
                        "cs": s.constraint_satisfaction,
                        "be": s.budget_efficiency,
                        "ls": s.logistics_score,
                        "details": s.details
                    }
                    for idx, s in enumerate(run_scores)
                ],
                "last_run_details": run_scores[-1].details if run_scores else {}
            },
            agent_response=run_scores[-1].agent_response if run_scores else None
        )

        results.append(avg_score)

        if verbose:
            print(f"\n--- AVERAGE SCORES (across {num_runs} runs) ---")
            print(f"Constraint Satisfaction: {avg_cs:.3f}")
            print(f"Budget Efficiency:       {avg_be:.3f}")
            print(f"Logistics Score:         {avg_ls:.3f}")

    # Calculate overall averages across all tasks
    if verbose:
        print(f"\n{'='*70}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*70}")

    avg_cs = sum(s.constraint_satisfaction for s in results) / len(results)
    avg_be = sum(s.budget_efficiency for s in results) / len(results)
    avg_ls = sum(s.logistics_score for s in results) / len(results)

    summary = {
        "total_tasks": len(results),
        "runs_per_task": num_runs,
        "overall_average_scores": {
            "constraint_satisfaction": avg_cs,
            "budget_efficiency": avg_be,
            "logistics_score": avg_ls
        },
        "task_results": [asdict(s) for s in results]
    }

    if verbose:
        print(f"\nEach task was run {num_runs} times.")
        print(f"\nOverall Average Constraint Satisfaction: {avg_cs:.3f}")
        print(f"Overall Average Budget Efficiency:       {avg_be:.3f}")
        print(f"Overall Average Logistics Score:         {avg_ls:.3f}")
        print(f"\n{'='*70}\n")

    return summary


def save_results(results: dict, output_path: str = None):
    """Save benchmark results to JSON file."""
    if output_path is None:
        output_path = Path(__file__).parent / "benchmark_results.json"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mindy Bench - AI Travel Agent Benchmark")
    parser.add_argument("--output", "-o", type=str, help="Output path for results JSON")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress verbose output")
    parser.add_argument("--runs", "-r", type=int, default=3, help="Number of times to run each task (default: 3)")

    args = parser.parse_args()


    print("MINDY BENCH - AI Travel Agent Benchmarking System")


    results = run_benchmark(verbose=not args.quiet, num_runs=args.runs)
    save_results(results, args.output)
