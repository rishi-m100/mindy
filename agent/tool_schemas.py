TOOL_SCHEMAS = [
    {
        "name": "search_flights",
        "description": "Search for available flights between two cities on a specific date. Returns flights sorted by price cheapest first. Accepts city names like 'New York' or IATA codes like 'JFK'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "Departure city name or IATA code"},
                "destination": {"type": "string", "description": "Arrival city name or IATA code"},
                "date": {"type": "string", "description": "Departure date in YYYY-MM-DD format"},
                "max_price": {"type": "number", "description": "Optional maximum price in USD"},
                "cabin": {"type": "string", "enum": ["economy", "business", "first"]},
                "nonstop_only": {"type": "boolean", "description": "If true, only return nonstop flights"},
                "max_results": {"type": "integer", "description": "Max results to return, default 10"},
            },
            "required": ["origin", "destination", "date"],
        },
    },
    {
        "name": "get_flight_details",
        "description": "Get complete details for a specific flight by its flight_id. Use to confirm price and times before finalizing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_id": {"type": "string", "description": "Flight ID from search_flights, e.g. 'FL0000001'"},
            },
            "required": ["flight_id"],
        },
    },
]