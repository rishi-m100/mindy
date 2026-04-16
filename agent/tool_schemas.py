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
    {
        "name": "search_hotels",
        "description": "Search for hotels in a specific city. Returns hotels sorted by price cheapest first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name or airport IATA code"},
                "max_price": {"type": "number", "description": "Optional maximum price per night in USD"},
                "tier": {"type": "string", "description": "Optional hotel tier (e.g. 'budget', 'luxury')"},
                "min_rating": {"type": "number", "description": "Optional minimum rating (e.g. 4.0)"},
                "pet_friendly": {"type": "boolean", "description": "If true, only return pet-friendly hotels"},
                "max_results": {"type": "integer", "description": "Max results to return, default 10"},
            },
            "required": ["city"],
        },
    },
    {
        "name": "get_hotel_details",
        "description": "Get complete details for a specific hotel by its hotel_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "hotel_id": {"type": "string", "description": "Hotel ID from search_hotels"},
            },
            "required": ["hotel_id"],
        },
    },
    {
        "name": "search_activities",
        "description": "Search for activities/attractions in a city. Returns activities sorted by cost cheapest first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name or airport IATA code"},
                "category": {"type": "string", "description": "Optional category (e.g. 'Museum', 'Outdoors')"},
                "max_price": {"type": "number", "description": "Optional maximum cost in USD"},
                "min_rating": {"type": "number", "description": "Optional minimum rating (e.g. 4.5)"},
                "accessible_only": {"type": "boolean", "description": "If true, only return wheelchair-accessible activities"},
                "max_results": {"type": "integer", "description": "Max results to return, default 10"},
            },
            "required": ["city"],
        },
    },
    {
        "name": "get_activity_details",
        "description": "Get complete details for a specific activity by its activity_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "activity_id": {"type": "string", "description": "Activity ID from search_activities"},
            },
            "required": ["activity_id"],
        },
    },
    {
        "name": "calculate_total_cost",
        "description": "Calculate total cost for a tentative itinerary including flights, hotel, and activities.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flight_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of flight IDs",
                },
                "hotel_id": {"type": "string", "description": "Hotel ID"},
                "hotel_nights": {"type": "integer", "description": "Number of nights at hotel (default 0)"},
                "activity_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of activity IDs",
                },
            },
        },
    },
    {
        "name": "submit_itinerary",
        "description": "Submit the final itinerary or ask a clarifying question to the user. This MUST be the final tool call.",
        "input_schema": {
            "type": "object",
            "properties": {
                "flights": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Selected flight IDs"
                },
                "hotels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Selected hotel IDs"
                },
                "activities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Selected activity IDs"
                },
                "total_cost": {
                    "type": "number",
                    "description": "Total cost of the itinerary. Pass 0 if none."
                },
                "message": {
                    "type": "string",
                    "description": "Message to the user explaining the itinerary, clarifying questions, or why nothing was found."
                }
            },
            "required": ["flights", "hotels", "activities", "total_cost", "message"]
        }
    }
]