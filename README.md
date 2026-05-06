# Mindy-Bench & AI Travel Agent

Mindy is an AI travel-planning agent that takes user specifications and constraints into account when planning an itinerary.

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

## Benchmark Tasks

### Easy Tasks (4 tasks)

#### easy_01: Find Cheapest Flight in Time Period
**Prompt:** "Find the cheapest flight from Chicago (ORD) to Seattle (SEA) on June 10th, 2025."

**Ground Truth:**
- Route: Chicago (ORD) to Seattle (SEA)
- Date: 2025-06-10
- Optimal Price: $325.48 (FL00000619)

**Success Criteria:**
- Must have flight
- Correct route
- Correct date
- Is cheapest available option
- Has availability

#### easy_02: Find Hotel with Amenity Requirement
**Prompt:** "I need a hotel in New York for June 10th, 2025 that has a gym"

**Ground Truth:**
- City: New York
- Check-in: 2025-06-10
- Required amenity: Gym

**Success Criteria:**
- Must have hotel
- Correct city
- Correct date
- Has gym amenity
- Has availability

#### easy_03: Find Flight within Time Constraint
**Prompt:** "Find a flight from New York (JFK) to Los Angeles (LAX) on June 11th, 2025 that arrives before 4:00 PM."

**Ground Truth:**
- Route: New York (JFK) to Los Angeles (LAX)
- Date: 2025-06-11
- Max arrival time: 16:00 (4:00 PM)

**Success Criteria:**
- Must have flight
- Correct route
- Correct date
- Arrives on time (before 16:00)
- Has availability

#### easy_04: Find Non-Stop Flight
**Prompt:** "I need a non-stop flight from San Francisco (SFO) to Boston (BOS) on June 10th, 2025."

**Ground Truth:**
- Route: San Francisco (SFO) to Boston (BOS)
- Date: 2025-06-10
- Max stops: 0 (non-stop required)
- Available non-stop: $702.00 vs cheapest with stops: $522.32

**Success Criteria:**
- Must have flight
- Correct route
- Correct date
- Is non-stop (stops = 0)
- Has availability

**Challenge:** Agent must prioritize non-stop constraint over price optimization.

### Medium Tasks (4 tasks)

#### medium_01: Weekend Trip with Budget - Flight and Hotel
**Prompt:** "I'm in Chicago and need a flight to Miami plus a hotel for a weekend trip (June 10-12, 2025). My total budget is $800."

**Ground Truth:**
- Route: Chicago (ORD) to Miami (MIA)
- Dates: June 10-12, 2025 (2 nights)
- Budget: $800
- Example solution: Flight $235.82 + Hotel $143.68 = $379.50

**Success Criteria:**
- Must have flight
- Must have hotel
- Correct destination (Miami)
- Correct dates
- Within budget ($800)
- Has availability

**Challenge:** Multi-item booking with budget constraint and route verification.

#### medium_02: Multi-Constraint Trip - Hotel Amenity and Activities
**Prompt:** "I'm in Los Angeles and want to plan a 2-day relaxing trip to Denver (June 10-12, 2025). I need a flight, a hotel with a pool, and some wellness activities. Budget is $1,000."

**Ground Truth:**
- Route: Los Angeles (LAX) to Denver (DEN)
- Dates: June 10-12, 2025 (2 nights)
- Required amenity: Pool
- Activity category: Wellness
- Budget: $1,000
- Example solution: Flight $94.75 + Hotel $235.26 + Activities $96.25 = $426.26

**Success Criteria:**
- Must have flight
- Must have hotel
- Correct destination (Denver)
- Correct dates
- Has required amenity (pool)
- Has wellness activities
- Within budget ($1,000)
- Has availability

**Challenge:** Route verification, hotel amenity filtering, and activity category matching.

#### medium_03: Business Trip with Time Constraint
**Prompt:** "I'm in Philadelphia and have a meeting in Boston at 2 PM on June 10th, 2025. I need a flight from Philadelphia (PHL) that gets me there by noon and a hotel near the airport."

**Ground Truth:**
- Route: Philadelphia (PHL) to Boston (BOS)
- Date: 2025-06-10
- Max arrival time: 12:00 (noon)
- Available option: FL00005323 arrives 11:28 AM, $62.33

**Success Criteria:**
- Must have flight
- Must have hotel
- Correct destination (Boston)
- Correct date
- Arrives on time (by 12:00)
- Has availability

**Challenge:** Temporal constraint (arrival time) with route verification.

#### medium_04: Family Trip with Multiple Activities
**Prompt:** "We're in Boston and want to plan a 3-day family trip to Orlando (June 10-13, 2025). We need a flight, hotel, and 2 fun activities for kids. Our budget is $2,500."

**Ground Truth:**
- Route: Boston (BOS) to Orlando (MCO)
- Dates: June 10-13, 2025 (3 nights)
- Minimum activities: 2
- Budget: $2,500
- Example solution: Flight $190.28 + Hotel $181.26 + Activities $55.45 = $426.99

**Success Criteria:**
- Must have flight
- Must have hotel
- Correct destination (Orlando)
- Correct dates
- Has minimum 2 activities
- Within budget ($2,500)
- Has availability

**Challenge:** Route verification, minimum activity count, and budget management.

### Hard Tasks (2 tasks)

#### hard_01: Multi-Turn Clarification Test - Ambiguous Request
**Prompt:** "I need a trip to Miami."

**Ground Truth:**
- Type: Clarification task
- Destination: Miami
- Requires clarification: True

**Expected Behavior:**
Agent should HALT and ASK for clarification instead of making assumptions.

**Success Criteria:**
- Asks for clarification (message contains questions)
- Mentions missing information (dates, origin, budget, preferences)
- Minimal assumptions (returns 0-1 items, not making bookings without info)

**Challenge:** Tests agent's ability to recognize incomplete requests and request additional information.

**Example Good Response:**
"I'd be happy to help plan your Miami trip! To get started, I need some information:
- When are you planning to travel?
- Where will you be departing from?
- How long do you want to stay?
- What's your budget?"

**Example Bad Response:**
Returns a complete itinerary with assumed dates and origin.

#### hard_02: Long Horizon Planning - 2 Week Trip
**Prompt:** "I'm planning a 2-week trip to Florida (Miami) from Chicago. My budget is $5,000. I want to arrive on June 10th, 2025."

**Ground Truth:**
- Route: Chicago (ORD) to Miami (MIA)
- Dates: June 10-23, 2025 (14 days, 13 nights)
- Budget: $5,000
- Hotel nights: 13
- Minimum activities: 5
- Example solution: Flight $235.82 + Hotel $933.92 + Activities ~$632 = $1,801.74

**Success Criteria:**
- Must have flight
- Must have hotel
- Correct destination (Miami)
- Correct dates
- Long hotel stay (13 nights, ±1 acceptable)
- Has multiple activities (minimum 5)
- Within budget ($5,000)
- Has availability

**Challenge:** Long-term planning horizon, budget management across extended trip, booking multiple activities for 2-week duration.

### Scoring Details

#### Constraint Satisfaction (CS)
Formula: `CS = met_constraints / total_constraints`

Measures how well the agent satisfies task requirements:
- Queries database to verify each criterion
- For "is_cheapest": Runs `SELECT MIN(price)` SQL query
- For "is_nonstop": Checks if `stops = 0`
- For "asks_for_clarification": Scans message for questions
- For "long_hotel_stay": Verifies hotel nights match duration (±1)
- Awards 1 point per satisfied constraint

#### Budget Efficiency (BE)
Formula: `BE = 1.0 - ((agent_cost - optimal_cost) / budget)`

Measures cost-effectiveness:
- Uses task's `max_budget` if specified
- Otherwise uses default: `max(optimal_cost × 10, $5000)`
- Score = 0.0 if agent exceeds budget
- Score clamped between 0.0 and 1.0

#### Logistics Score (LS)
Starts at 1.0, deducts points for violations:
- Agent error: -0.3
- Check-out before check-in: -0.2
- Hotel nights mismatch: -0.1
- Invalid date format: -0.1
- Score clamped to minimum 0.0

#### Evaluation Score (Composite)
Formula: `S = (0.5 × CS) + (0.3 × BE) + (0.2 × LS)`

Weighted combination:
- 50% Constraint Satisfaction
- 30% Budget Efficiency
- 20% Logistics Score

Pass threshold: 0.75

### Running the Benchmark

```bash
# Run all tasks (4 easy + 4 medium + 2 hard = 10 tasks)
python benchmark/mindy_bench.py

# Save results to custom file
python benchmark/mindy_bench.py --output my_results.json

```

### Viewing Results

```bash
# Start the benchmark viewer web interface
python benchmark_viewer.py

# Open browser to http://localhost:5001
```

The viewer displays:
- Overall average scores across all tasks
- Individual task results with expandable details
- Ground truth vs agent response comparison
- Constraint satisfaction breakdown
- Agent reasoning trace
- Budget usage analysis

## Agent Implementation

The repository also includes an autonomous agent built to navigate the Mindy-Bench environment.
* **SQL Tool Calling:** The agent translates natural language into SQL queries to interact with the `.db` synthetic database.
* **Constraint Parsing:** Automatically identifies hard and soft constraints from user prompts.
* **Current Status:** Fully functional

## 🛠️ Tech Stack
* **Language:** Python
* **Database:** SQLite (`.db` format)
* **Models:** LLM-based agents with tool-calling capabilities.

## 🚀 Getting Started

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rishi-m100/mindy.git
   cd mindy
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key:**
   Create a `.env` file in the root directory:
   ```bash
   ANTHROPIC_API_KEY=your_api_key_here
   ```

4. **Run the benchmark:**
   See the [Running the Benchmark](#running-the-benchmark) section above for detailed instructions on running benchmarks and viewing results.
