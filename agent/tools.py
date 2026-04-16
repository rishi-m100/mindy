import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "mindy_dataset.db"

_ALIASES: dict[str, str] = {
    "nyc": "New York",  "new york city": "New York",
    "la": "Los Angeles", "l.a.": "Los Angeles",
    "chi": "Chicago", "chitown": "Chicago",
    "sf": "San Francisco", "san fran": "San Francisco",
    "dc": "Washington DC", "washington": "Washington DC",
    "philly": "Philadelphia",
    "nola": "New Orleans",
    "sin city": "Las Vegas", "vegas": "Las Vegas",
    "the a": "Atlanta",
    "h-town": "Houston", "space city": "Houston",
    "mile high": "Denver",
    "emerald city": "Seattle",
    "music city": "Nashville",
    "charm city": "Baltimore",
    "naptown": "Indianapolis",
    "cle": "Cleveland",
    "phl": "Philadelphia",
    "bna": "Nashville",
    "msp": "Minneapolis",
    "pdx": "Portland",
    "slc": "Salt Lake City",
    "mia": "Miami",
    "bos": "Boston",
    "atl": "Atlanta",
    "dfw": "Dallas",
    "ord": "Chicago",
    "lax": "Los Angeles",
    "jfk": "New York",
    "ewr": "New York",
    "lga": "New York",
    "sfo": "San Francisco",
    "oak": "San Francisco",
    "sea": "Seattle",
    "den": "Denver",
    "las": "Las Vegas",
    "phx": "Phoenix",
    "iah": "Houston",
    "hou": "Houston",
    "aus": "Austin",
    "rdu": "Raleigh",
    "mco": "Orlando",
    "tpa": "Tampa",
    "msy": "New Orleans",
    "stl": "St. Louis",
    "mci": "Kansas City",
    "ind": "Indianapolis",
    "cmh": "Columbus",
    "pit": "Pittsburgh",
    "mke": "Milwaukee",
    "oma": "Omaha",
    "abq": "Albuquerque",
    "tul": "Tulsa",
    "okc": "Oklahoma City",
    "elp": "El Paso",
    "lit": "Little Rock",
    "mem": "Memphis",
    "bhm": "Birmingham",
    "jax": "Jacksonville",
    "sav": "Savannah",
    "chs": "Charleston",
    "boi": "Boise",
    "geg": "Spokane",
    "fat": "Fresno",
    "smf": "Sacramento",
    "ont": "Ontario",
    "san": "San Diego",
    "dtw": "Detroit",
    "phl": "Philadelphia",
    "bwi": "Baltimore",
    "dca": "Washington DC", "dc": "Washington DC", "d.c.": "Washington DC",
    "cle": "Cleveland",
    "pit": "Pittsburgh",
}

def _norm(loc: str) -> str:
    return _ALIASES.get(loc.strip().lower(), loc.strip())

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def search_flights(
    origin: str,
    destination: str,
    date: str,
    max_price: float | None = None,
    cabin: str | None = None,
    nonstop_only: bool = False,
    max_results: int = 10,
) -> list[dict]:
    query = """
        SELECT f.flight_id, f.airline_iata, f.flight_number,
               ao.city AS origin_city, ad.city AS destination_city,
               f.origin AS origin_iata, f.destination AS destination_iata,
               f.depart_date, f.depart_time, f.arrive_time,
               f.duration_hours, f.price, f.seats_available,
               f.stops, f.layover_airport, f.layover_minutes, f.cabin
        FROM flights f
        JOIN airports ao ON f.origin = ao.iata
        JOIN airports ad ON f.destination = ad.iata
        WHERE (LOWER(ao.city) = LOWER(?) OR UPPER(f.origin) = UPPER(?))
          AND (LOWER(ad.city) = LOWER(?) OR UPPER(f.destination) = UPPER(?))
          AND f.depart_date = ?
    """

    origin      = _norm(origin)
    destination = _norm(destination)
    params = [origin, origin, destination, destination, date]

    if max_price is not None:
        query += " AND f.price <= ?"
        params.append(max_price)

    if cabin is not None:
        query += " AND LOWER(f.cabin) = LOWER(?)"
        params.append(cabin)

    if nonstop_only:
        query += " AND f.stops = 0"

    query += " ORDER BY f.price ASC LIMIT ?"
    params.append(max_results)

    with _get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(r) for r in rows]


def get_flight_details(flight_id: str) -> dict | None:
    query = """
        SELECT f.*, ao.city AS origin_city, ad.city AS destination_city
        FROM flights f
        JOIN airports ao ON f.origin = ao.iata
        JOIN airports ad ON f.destination = ad.iata
        WHERE f.flight_id = ?
    """
    with _get_conn() as conn:
        row = conn.execute(query, (flight_id,)).fetchone()
    return dict(row) if row else None

def search_hotels(
    city: str,
    max_price: float | None = None,
    tier: str | None = None,
    min_rating: float | None = None,
    pet_friendly: bool = False,
    max_results: int = 10,
) -> list[dict]:
    city = _norm(city)
    query = """
        SELECT h.hotel_id, h.name, h.city, h.airport_iata,
               h.brand, h.tier, h.price_per_night, h.rating,
               h.num_reviews, h.amenities, h.distance_miles
        FROM hotels h
        WHERE LOWER(h.city) = LOWER(?) OR UPPER(h.airport_iata) = UPPER(?)
    """
    params = [city, city]

    if max_price is not None:
        query += " AND h.price_per_night <= ?"
        params.append(max_price)

    if tier is not None:
        query += " AND LOWER(h.tier) = LOWER(?)"
        params.append(tier)

    if min_rating is not None:
        query += " AND h.rating >= ?"
        params.append(min_rating)

    if pet_friendly:
        query += " AND h.pet_friendly = 1"

    query += " ORDER BY h.price_per_night ASC LIMIT ?"
    params.append(max_results)

    with _get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(r) for r in rows]


def get_hotel_details(hotel_id: str) -> dict | None:
    query = "SELECT * FROM hotels WHERE hotel_id = ?"
    with _get_conn() as conn:
        row = conn.execute(query, (hotel_id,)).fetchone()
    return dict(row) if row else None


def search_activities(
    city: str,
    category: str | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    accessible_only: bool = False,
    max_results: int = 10,
) -> list[dict]:
    city = _norm(city)
    query = """
        SELECT a.activity_id, a.name, a.city, a.category,
               a.duration_hrs, a.cost, a.rating,
               a.open_time, a.close_time, a.tags
        FROM activities a
        WHERE LOWER(a.city) = LOWER(?) OR UPPER(a.airport_iata) = UPPER(?)
    """
    params = [city, city]

    if category is not None:
        query += " AND LOWER(a.category) = LOWER(?)"
        params.append(category)

    if max_price is not None:
        query += " AND a.cost <= ?"
        params.append(max_price)

    if min_rating is not None:
        query += " AND a.rating >= ?"
        params.append(min_rating)

    if accessible_only:
        query += " AND a.accessible = 1"

    query += " ORDER BY a.cost ASC LIMIT ?"
    params.append(max_results)

    with _get_conn() as conn:
        rows = conn.execute(query, params).fetchall()

    return [dict(r) for r in rows]


def get_activity_details(activity_id: str) -> dict | None:
    query = "SELECT * FROM activities WHERE activity_id = ?"
    with _get_conn() as conn:
        row = conn.execute(query, (activity_id,)).fetchone()
    return dict(row) if row else None


def calculate_total_cost(
    flight_ids: list[str] | None = None,
    hotel_id: str | None = None,
    hotel_nights: int = 0,
    activity_ids: list[str] | None = None
) -> dict:
    total = 0.0
    breakdown = {}

    with _get_conn() as conn:
        if flight_ids:
            flights_cost = 0.0
            for fid in flight_ids:
                row = conn.execute("SELECT price FROM flights WHERE flight_id = ?", (fid,)).fetchone()
                if row:
                    flights_cost += row['price']
            total += flights_cost
            breakdown['flights'] = flights_cost

        if hotel_id and hotel_nights > 0:
            row = conn.execute("SELECT price_per_night FROM hotels WHERE hotel_id = ?", (hotel_id,)).fetchone()
            if row:
                hotel_cost = row['price_per_night'] * hotel_nights
                total += hotel_cost
                breakdown['hotel'] = hotel_cost

        if activity_ids:
            activities_cost = 0.0
            for aid in activity_ids:
                row = conn.execute("SELECT cost FROM activities WHERE activity_id = ?", (aid,)).fetchone()
                if row:
                    activities_cost += row['cost']
            total += activities_cost
            breakdown['activities'] = activities_cost

    breakdown['total'] = total
    return breakdown

def execute_tool(tool_name: str, tool_input: dict) -> str:
    functions = {
        "search_flights": search_flights,
        "get_flight_details": get_flight_details,
        "search_hotels": search_hotels,
        "get_hotel_details": get_hotel_details,
        "search_activities": search_activities,
        "get_activity_details": get_activity_details,
        "calculate_total_cost": calculate_total_cost,
    }
    fn = functions.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return json.dumps(fn(**tool_input), default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})