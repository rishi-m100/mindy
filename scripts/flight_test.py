import sys, json
sys.path.insert(0, '.')
from agent.tools import search_flights, get_flight_details

output = []

tests = [
    ('Basic search',        dict(origin='New York', destination='Los Angeles', date='2025-06-12')),
    ('Max price 700',       dict(origin='New York', destination='Los Angeles', date='2025-06-12', max_price=700)),
    ('Nonstop only',        dict(origin='New York', destination='Los Angeles', date='2025-06-12', nonstop_only=True)),
    ('Business cabin',      dict(origin='New York', destination='Los Angeles', date='2025-06-12', cabin='business')),
    ('IATA codes',          dict(origin='JFK', destination='LAX', date='2025-06-12')),
    ('Different route',     dict(origin='Chicago', destination='Miami', date='2025-07-01')),
    ('Max results 3',       dict(origin='New York', destination='Los Angeles', date='2025-06-12', max_results=3)),
]

for name, params in tests:
    results = search_flights(**params)
    output.append(f'=== {name} ===')
    output.append(f'Params: {params}')
    output.append(f'Found: {len(results)} flights')
    for r in results:
        output.append(json.dumps(r, indent=2))
    output.append('')

# get_flight_details test
base = search_flights('New York', 'Los Angeles', '2025-06-12')
if base:
    for flight in base:
        fid = flight['flight_id']
        detail = get_flight_details(fid)
        output.append(f'=== get_flight_details: {fid} ===')
        output.append(json.dumps(detail, indent=2))
        output.append('')

with open('test_results.txt', 'w') as f:
    f.write('\n'.join(output))

print('Done — see test_results.txt')