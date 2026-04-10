import json
import sqlite3
from pathlib import Path
 
DB_PATH = Path(__file__).parent.parent / "data" / "mindy_dataset.db"

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

    # ai assistance to write the above SQL query
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

def execute_tool(tool_name: str, tool_input: dict) -> str:
    functions = {
        "search_flights": search_flights,
        "get_flight_details": get_flight_details,
    }
    fn = functions.get(tool_name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        return json.dumps(fn(**tool_input), default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})