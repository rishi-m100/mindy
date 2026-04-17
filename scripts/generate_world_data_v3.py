import argparse, csv, json, math, os, random, sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--seed",    type=int, default=42)
parser.add_argument("--db",      default="data/mindy_dataset_v3.db")
parser.add_argument("--csv-dir", default="data/csvs")
args = parser.parse_args()
random.seed(args.seed)
Path(args.csv_dir).mkdir(parents=True, exist_ok=True)
Path(args.db).parent.mkdir(parents=True, exist_ok=True)

# 3-day window (small dataset for benchmarking)
DATE_START = date(2025, 6, 10)
DATE_END   = date(2025, 6, 13)
ALL_DATES  = [DATE_START + timedelta(days=i) for i in range((DATE_END - DATE_START).days)]

AIRPORTS = [
    ("JFK","New York","NY",-5,40.64,-73.78),
    ("LAX","Los Angeles","CA",-8,33.94,-118.41),
    ("ORD","Chicago","IL",-6,41.98,-87.91),
    ("DFW","Dallas","TX",-6,32.90,-97.04),
    ("ATL","Atlanta","GA",-5,33.64,-84.43),
    ("SFO","San Francisco","CA",-8,37.62,-122.38),
    ("SEA","Seattle","WA",-8,47.45,-122.31),
    ("MIA","Miami","FL",-5,25.80,-80.29),
    ("BOS","Boston","MA",-5,42.36,-71.01),
    ("DEN","Denver","CO",-7,39.86,-104.67),
    ("LAS","Las Vegas","NV",-8,36.08,-115.15),
    ("PHX","Phoenix","AZ",-7,33.44,-112.01),
    ("MSP","Minneapolis","MN",-6,44.88,-93.22),
    ("DTW","Detroit","MI",-5,42.21,-83.35),
    ("PDX","Portland","OR",-8,45.59,-122.60),
    ("SAN","San Diego","CA",-8,32.73,-117.19),
    ("AUS","Austin","TX",-6,30.20,-97.67),
    ("BNA","Nashville","TN",-6,36.12,-86.68),
    ("CLE","Cleveland","OH",-5,41.41,-81.85),
    ("MSY","New Orleans","LA",-6,29.99,-90.26),
    ("SLC","Salt Lake City","UT",-7,40.79,-111.98),
    ("IAH","Houston","TX",-6,29.99,-95.34),
    ("PHL","Philadelphia","PA",-5,39.87,-75.24),
    ("BWI","Baltimore","MD",-5,39.18,-76.67),
    ("DCA","Washington DC","VA",-5,38.85,-77.04),
    ("RDU","Raleigh","NC",-5,35.88,-78.79),
    ("TPA","Tampa","FL",-5,27.98,-82.53),
    ("MCO","Orlando","FL",-5,28.43,-81.31),
    ("STL","St. Louis","MO",-6,38.75,-90.37),
    ("MCI","Kansas City","MO",-6,39.30,-94.71),
    ("IND","Indianapolis","IN",-5,39.72,-86.29),
    ("CMH","Columbus","OH",-5,39.99,-82.89),
    ("PIT","Pittsburgh","PA",-5,40.49,-80.23),
    ("MKE","Milwaukee","WI",-6,42.95,-87.90),
    ("OMA","Omaha","NE",-6,41.30,-95.89),
    ("ABQ","Albuquerque","NM",-7,35.04,-106.61),
    ("TUL","Tulsa","OK",-6,36.20,-95.89),
    ("OKC","Oklahoma City","OK",-6,35.39,-97.60),
    ("ELP","El Paso","TX",-7,31.81,-106.38),
    ("LIT","Little Rock","AR",-6,34.73,-92.22),
    ("MEM","Memphis","TN",-6,35.04,-89.98),
    ("BHM","Birmingham","AL",-6,33.56,-86.75),
    ("JAX","Jacksonville","FL",-5,30.49,-81.69),
    ("SAV","Savannah","GA",-5,32.13,-81.20),
    ("CHS","Charleston","SC",-5,32.90,-80.04),
    ("BOI","Boise","ID",-7,43.56,-116.22),
    ("GEG","Spokane","WA",-8,47.62,-117.53),
    ("FAT","Fresno","CA",-8,36.78,-119.72),
    ("SMF","Sacramento","CA",-8,38.70,-121.59),
    ("ONT","Ontario","CA",-8,34.06,-117.60),
]

AIRPORT_LOOKUP = {r[0]: r for r in AIRPORTS}

# Market premium affects flight pricing (geometric mean of origin+dest)
AIRPORT_MARKET_MULT = {
    "JFK":1.45, "SFO":1.40, "LAX":1.35, "BOS":1.30, "MIA":1.25,
    "SEA":1.20, "ORD":1.18, "DCA":1.18, "BWI":1.12, "DEN":1.15,
    "SAN":1.20, "AUS":1.18, "PDX":1.15, "BNA":1.12, "LAS":1.10,
    "ATL":1.10, "DFW":1.08, "IAH":1.08, "PHX":1.05, "MCO":1.12,
    "TPA":1.05, "MSP":1.05, "PHL":1.08, "DTW":1.05, "SLC":1.08,
    "MSY":1.10, "RDU":1.08, "STL":1.00, "MCI":1.00, "IND":0.97,
    "CMH":0.97, "PIT":1.00, "MKE":0.97, "CLE":0.97, "JAX":1.00,
    "TUL":0.90, "OKC":0.90, "OMA":0.90, "ABQ":0.92, "ELP":0.90,
    "LIT":0.88, "MEM":0.92, "BHM":0.90, "SAV":0.95, "CHS":0.97,
    "BOI":0.93, "GEG":0.88, "FAT":0.88, "SMF":1.00, "ONT":0.92,
}

# Cost of living multiplier applied to hotel and activity prices
CITY_COST_MULT = {
    "JFK":2.30, "SFO":2.20, "LAX":2.00, "BOS":1.90, "MIA":1.70,
    "SEA":1.60, "DCA":1.55, "BWI":1.40, "ORD":1.50, "DEN":1.45,
    "SAN":1.55, "AUS":1.40, "PDX":1.35, "BNA":1.30, "LAS":1.25,
    "ATL":1.20, "DFW":1.20, "IAH":1.18, "PHX":1.12, "MCO":1.20,
    "TPA":1.10, "MSP":1.10, "PHL":1.25, "DTW":1.05, "SLC":1.15,
    "MSY":1.15, "RDU":1.10, "STL":1.00, "MCI":1.00, "IND":0.95,
    "CMH":0.95, "PIT":1.00, "MKE":0.95, "CLE":0.93, "JAX":1.00,
    "TUL":0.85, "OKC":0.87, "OMA":0.85, "ABQ":0.90, "ELP":0.85,
    "LIT":0.82, "MEM":0.88, "BHM":0.85, "SAV":0.92, "CHS":1.00,
    "BOI":0.90, "GEG":0.85, "FAT":0.85, "SMF":1.05, "ONT":0.92,
}

# (iata, name, on_time, cancel_rate, tier, cpm_lo, cpm_hi, biz_mult_lo, biz_mult_hi)
AIRLINES_EXT = [
    ("AA", "American Airlines",   0.82, 0.015, "premium",    0.12, 0.18, 3.5, 5.0),
    ("DL", "Delta Air Lines",     0.87, 0.010, "premium",    0.13, 0.19, 3.5, 5.5),
    ("UA", "United Airlines",     0.80, 0.018, "premium",    0.11, 0.17, 3.2, 5.0),
    ("WN", "Southwest Airlines",  0.78, 0.020, "mainstream", 0.09, 0.14, 2.5, 3.5),
    ("B6", "JetBlue Airways",     0.75, 0.022, "mainstream", 0.09, 0.13, 2.8, 3.8),
    ("AS", "Alaska Airlines",     0.85, 0.012, "mainstream", 0.10, 0.15, 3.0, 4.2),
    ("F9", "Frontier Airlines",   0.72, 0.025, "budget",     0.06, 0.09, 2.0, 2.8),
    ("NK", "Spirit Airlines",     0.68, 0.030, "budget",     0.05, 0.08, 1.8, 2.5),
    ("G4", "Allegiant Air",       0.70, 0.028, "budget",     0.06, 0.09, 2.0, 2.8),
    ("SY", "Sun Country",         0.76, 0.021, "budget",     0.07, 0.10, 2.2, 3.0),
]
AIRLINES = [(r[0], r[1], r[2], r[3]) for r in AIRLINES_EXT]
AIRLINE_LOOKUP = {r[0]: r for r in AIRLINES_EXT}

MAJOR_HUBS = {
    "JFK", "LAX", "ORD", "DFW", "ATL", "SFO", "SEA",
    "MIA", "BOS", "DEN", "LAS", "IAH", "PHX",
}

HOTEL_CHAINS = [
    ("Marriott",         "luxury",   (200,450), ["pool","gym","spa","restaurant","wifi","parking","bar","concierge"]),
    ("Ritz-Carlton",     "luxury",   (350,700), ["pool","gym","spa","restaurant","wifi","parking","bar","concierge","valet"]),
    ("W Hotels",         "luxury",   (280,550), ["pool","gym","spa","restaurant","wifi","bar","rooftop"]),
    ("Westin",           "luxury",   (220,480), ["pool","gym","spa","restaurant","wifi","parking"]),
    ("Hilton",           "upscale",  (150,350), ["pool","gym","restaurant","wifi","parking","bar"]),
    ("Hyatt Regency",    "upscale",  (160,380), ["pool","gym","spa","restaurant","wifi","bar"]),
    ("Sheraton",         "upscale",  (140,320), ["pool","gym","restaurant","wifi","parking"]),
    ("Kimpton",          "upscale",  (170,360), ["gym","restaurant","wifi","bar","pet_friendly"]),
    ("Renaissance",      "upscale",  (155,340), ["pool","gym","restaurant","wifi","parking"]),
    ("Crowne Plaza",     "upscale",  (130,300), ["pool","gym","restaurant","wifi","parking","breakfast"]),
    ("Holiday Inn",      "midscale", (90,180),  ["pool","gym","wifi","breakfast","parking"]),
    ("Hampton Inn",      "midscale", (80,160),  ["pool","gym","wifi","breakfast"]),
    ("Courtyard",        "midscale", (95,190),  ["pool","gym","wifi","parking"]),
    ("Fairfield Inn",    "midscale", (75,150),  ["pool","gym","wifi","breakfast"]),
    ("Comfort Inn",      "midscale", (70,145),  ["pool","wifi","breakfast"]),
    ("Best Western",     "midscale", (75,155),  ["pool","wifi","breakfast","parking"]),
    ("Radisson",         "midscale", (100,200), ["pool","gym","restaurant","wifi","parking"]),
    ("DoubleTree",       "midscale", (110,220), ["pool","gym","wifi","parking","bar"]),
    ("La Quinta",        "economy",  (60,120),  ["pool","wifi","breakfast"]),
    ("Motel 6",          "economy",  (40,80),   ["wifi","parking"]),
    ("Super 8",          "economy",  (45,85),   ["wifi","breakfast"]),
    ("Days Inn",         "economy",  (50,95),   ["pool","wifi","breakfast"]),
    ("Travelodge",       "economy",  (45,90),   ["wifi","parking"]),
    ("Extended Stay",    "economy",  (55,110),  ["wifi","kitchen","parking"]),
    ("Airbnb Entire",    "midscale", (70,250),  ["wifi","kitchen","washer","parking"]),
    ("Boutique Hotel",   "upscale",  (130,300), ["gym","restaurant","wifi","bar"]),
    ("Autograph Coll.",  "upscale",  (160,370), ["pool","gym","restaurant","wifi","bar","spa"]),
    ("Tapestry Coll.",   "midscale", (100,210), ["pool","gym","wifi","restaurant"]),
]

ACTIVITY_TEMPLATES = [
    ("{city} Art Museum",              "culture",       3.0, (15,  35), ["art","indoor","family","culture"]),
    ("{city} History Museum",          "culture",       2.5, (12,  28), ["history","indoor","family","culture"]),
    ("{city} Natural History Museum",  "culture",       3.0, (14,  30), ["history","indoor","family","education"]),
    ("{city} Contemporary Art Gall.",  "culture",       2.0, (10,  25), ["art","indoor","adults","culture"]),
    ("Downtown {city} Food Tour",      "food",          3.0, (55,  95), ["food","walking","adults"]),
    ("{city} Street Food Walk",        "food",          2.5, (35,  70), ["food","walking","adults","outdoor"]),
    ("{city} Craft Beer Tour",         "food",          3.0, (45,  85), ["food","adults","indoor","nightlife"]),
    ("{city} Wine & Cheese Tasting",   "food",          2.5, (50,  90), ["food","adults","indoor"]),
    ("{city} Cooking Class",           "food",          3.5, (75, 130), ["food","indoor","adults"]),
    ("Vegan Food Tour {city}",         "food",          3.0, (50,  90), ["food","vegan","walking","adults"]),
    ("{city} Farmers Market",          "food",          2.0, (0,   20), ["food","outdoor","morning","family"]),
    ("{city} Coffee Roastery Tour",    "food",          1.5, (20,  40), ["food","indoor","adults","morning"]),
    ("{city} Botanical Garden",        "nature",        2.0, (10,  25), ["nature","outdoor","family"]),
    ("{city} Zoo",                     "nature",        4.0, (20,  40), ["nature","outdoor","family"]),
    ("{city} Aquarium",                "nature",        3.0, (25,  45), ["nature","indoor","family"]),
    ("{city} State Park Hike",         "adventure",     4.0, (0,   15), ["outdoor","active","nature","adventure"]),
    ("{city} Waterfall Trail",         "adventure",     3.5, (0,   10), ["outdoor","active","nature","adventure"]),
    ("Kayaking in {city}",             "adventure",     3.0, (40,  80), ["water","outdoor","active","adventure"]),
    ("{city} Bike Tour",               "adventure",     3.0, (35,  65), ["outdoor","active","adults","adventure"]),
    ("{city} Rock Climbing",           "adventure",     3.5, (55,  95), ["outdoor","active","adults","adventure"]),
    ("Sunset Sailing {city}",          "sightseeing",   2.5, (55,  95), ["water","outdoor","scenic","adults"]),
    ("Harbor Cruise {city}",           "sightseeing",   2.0, (30,  60), ["water","outdoor","scenic","family"]),
    ("{city} Helicopter Tour",         "sightseeing",   1.0, (100,200), ["aerial","outdoor","scenic","adults"]),
    ("Architecture Walk {city}",       "culture",       2.0, (0,   25), ["walking","outdoor","history","culture"]),
    ("Street Art Tour {city}",         "culture",       2.0, (0,   30), ["outdoor","walking","art","culture"]),
    ("{city} Neighborhood Tour",       "culture",       2.5, (20,  45), ["walking","outdoor","history","culture"]),
    ("Sunset Rooftop Bar {city}",      "nightlife",     2.0, (20,  50), ["nightlife","adults","views","bar"]),
    ("{city} Jazz Club",               "nightlife",     2.5, (20,  50), ["music","adults","evening","nightlife"]),
    ("{city} Comedy Club",             "entertainment", 2.0, (25,  55), ["nightlife","adults","indoor","comedy"]),
    ("{city} Improv Show",             "entertainment", 2.0, (20,  40), ["indoor","adults","comedy","entertainment"]),
    ("{city} Ghost Tour",              "entertainment", 2.0, (25,  45), ["walking","adults","evening","entertainment"]),
    ("{city} Escape Room",             "entertainment", 1.5, (28,  42), ["indoor","group","adults","entertainment"]),
    ("{city} Live Music Venue",        "nightlife",     2.5, (15,  45), ["music","adults","evening","nightlife"]),
    ("{city} Trivia Night",            "entertainment", 2.0, (10,  25), ["indoor","adults","evening","group"]),
    ("Spa Day {city}",                 "wellness",      4.0, (80, 180), ["indoor","adults","relaxation","spa"]),
    ("{city} Yoga in the Park",        "wellness",      1.5, (0,   20), ["outdoor","morning","active","family"]),
    ("{city} Meditation Retreat",      "wellness",      3.0, (40,  90), ["indoor","adults","relaxation","wellness"]),
    ("{city} Science Center",          "culture",       3.0, (18,  32), ["indoor","family","education","science"]),
    ("{city} Planetarium Show",        "culture",       1.5, (12,  22), ["indoor","family","education","science"]),
    ("{city} Children's Museum",       "culture",       2.5, (10,  20), ["indoor","family","kids","education"]),
    ("Professional Sports Game {city}","entertainment", 3.0, (40, 150), ["indoor","sports","adults","family"]),
    ("{city} Bowling Alley Night",     "entertainment", 2.0, (20,  40), ["indoor","group","family","evening"]),
    ("{city} Mini Golf",               "entertainment", 1.5, (12,  22), ["outdoor","family","active"]),
    ("{city} Photography Walk",        "culture",       2.5, (25,  55), ["outdoor","walking","art","adults"]),
    ("{city} Sunset Picnic Kit",       "nature",        2.0, (30,  55), ["outdoor","nature","family","romantic"]),
    ("{city} Paddleboarding",          "adventure",     2.0, (35,  65), ["water","outdoor","active","adventure"]),
    ("{city} Surfing Lesson",          "adventure",     2.5, (60, 110), ["water","outdoor","active","adventure"]),
    ("{city} Ziplining",               "adventure",     2.0, (50,  90), ["outdoor","active","adventure","adults"]),
    ("{city} Hot Air Balloon",         "adventure",     2.5, (150,280), ["aerial","outdoor","scenic","adults","romantic"]),
    ("{city} Distillery Tour",         "food",          2.0, (35,  65), ["food","adults","indoor"]),
    ("{city} Food Hall Crawl",         "food",          2.5, (20,  50), ["food","indoor","adults","family"]),
    ("{city} Night Market",            "food",          2.0, (15,  40), ["food","outdoor","evening","family"]),
    ("{city} Scenic Drive Tour",       "sightseeing",   3.0, (0,   35), ["outdoor","scenic","family"]),
    ("{city} Museum of Science",       "culture",       3.0, (18,  32), ["indoor","family","education","science"]),
]

VEGAN_RESTAURANTS = [
    "The Green Plate", "Root & Branch", "Plant Paradise", "Harvest Table",
    "Verdant Kitchen", "Pure Eats", "The Sprout", "Leafy Greens Cafe",
    "Planted", "Nourish Bowl", "Green Soul", "Earthen Kitchen",
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def haversine_miles(iata1, iata2):
    r1 = AIRPORT_LOOKUP[iata1]; r2 = AIRPORT_LOOKUP[iata2]
    lat1, lon1 = math.radians(r1[4]), math.radians(r1[5])
    lat2, lon2 = math.radians(r2[4]), math.radians(r2[5])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 3958.8 * 2 * math.asin(math.sqrt(a))

def flight_hours(miles):
    return max(0.75, miles / 500 + 0.5 + random.uniform(-0.1, 0.3))

def time_add(t, hours):
    dt = datetime.combine(date.today(), t) + timedelta(hours=hours)
    return dt.time()

def fmt(t):
    return t.strftime("%H:%M")

def is_holiday(d):
    if d.month == 11 and d.day >= 22: return True
    if d.month == 12 and d.day >= 20: return True
    if d.month ==  1 and d.day <=  4: return True
    if d.month ==  3 and 10 <= d.day <= 31: return True
    if d.month ==  5 and d.day >= 24: return True
    if d.month ==  9 and d.day <=  7: return True
    return False

def season_mult(d):
    if is_holiday(d):              return random.uniform(1.35, 1.65)
    if d.month in (6, 7, 8):       return random.uniform(1.20, 1.40)
    if d.month in (1, 2):          return random.uniform(0.82, 0.93)
    return random.uniform(0.92, 1.12)

def dow_mult(d):
    dow = d.weekday()
    if dow in (0, 4):    return random.uniform(1.08, 1.18)
    if dow in (1, 2, 3): return random.uniform(0.90, 0.98)
    return random.uniform(0.95, 1.05)

def calc_price(miles, al_iata, cabin, fl_date, origin, dest):
    al  = AIRLINE_LOOKUP[al_iata]
    cpm = random.uniform(al[5], al[6])
    mkt = math.sqrt(
        AIRPORT_MARKET_MULT.get(origin, 1.0) * AIRPORT_MARKET_MULT.get(dest, 1.0)
    )
    base = miles * cpm * mkt * season_mult(fl_date) * dow_mult(fl_date)
    if cabin == "business":
        base *= random.uniform(al[7], al[8])
    if miles < 400:
        floor = 39 if al[4] == "budget" else 59
    elif miles < 1000:
        floor = 79 if al[4] == "budget" else 99
    else:
        floor = 120 if al[4] == "budget" else 149
    return round(max(floor, base + random.uniform(-15, 25)), 2)

def airline_pool(o_hub, d_hub):
    if o_hub and d_hub:
        return (["AA","DL","UA","WN","B6","AS","F9","NK"],
                [20,  20,  18,  14,  10,  10,   5,   3])
    elif o_hub or d_hub:
        return (["AA","DL","UA","WN","B6","AS","F9","NK","G4","SY"],
                [15,  15,  13,  15,  10,  10,   8,   7,   4,   3])
    else:
        return (["WN","F9","NK","G4","SY","B6","AS","AA","DL","UA"],
                [20,  16,  14,  12,  10,   9,   8,   5,   4,   2])

# ─── DB setup ────────────────────────────────────────────────────────────────

if os.path.exists(args.db):
    os.remove(args.db)
conn = sqlite3.connect(args.db)
cur  = conn.cursor()
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA cache_size=-64000")

cur.executescript("""
CREATE TABLE airports (
    iata TEXT PRIMARY KEY, city TEXT NOT NULL, state TEXT NOT NULL,
    tz_offset INTEGER NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL
);
CREATE TABLE airlines (
    iata TEXT PRIMARY KEY, name TEXT NOT NULL,
    on_time_rate REAL NOT NULL, cancel_rate REAL NOT NULL
);
CREATE TABLE flights (
    flight_id       TEXT PRIMARY KEY,
    airline_iata    TEXT NOT NULL,
    flight_number   TEXT NOT NULL,
    origin          TEXT NOT NULL,
    destination     TEXT NOT NULL,
    depart_date     TEXT NOT NULL,
    depart_time     TEXT NOT NULL,
    arrive_time     TEXT NOT NULL,
    duration_hours  REAL NOT NULL,
    price           REAL NOT NULL,
    seats_available INTEGER NOT NULL,
    stops           INTEGER NOT NULL,
    layover_airport TEXT,
    layover_minutes INTEGER,
    cabin           TEXT NOT NULL
);
CREATE TABLE hotels (
    hotel_id        TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    city            TEXT NOT NULL,
    airport_iata    TEXT NOT NULL,
    brand           TEXT NOT NULL,
    tier            TEXT NOT NULL,
    price_per_night REAL NOT NULL,
    rating          REAL NOT NULL,
    num_reviews     INTEGER NOT NULL,
    amenities       TEXT NOT NULL,
    pet_friendly    INTEGER NOT NULL,
    accessible      INTEGER NOT NULL,
    vegan_options   INTEGER NOT NULL,
    distance_miles  REAL NOT NULL,
    max_guests      INTEGER NOT NULL
);
CREATE TABLE hotel_availability (
    avail_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_id   TEXT NOT NULL,
    check_in   TEXT NOT NULL,
    check_out  TEXT NOT NULL,
    rooms_left INTEGER NOT NULL
);
CREATE TABLE activities (
    activity_id    TEXT PRIMARY KEY,
    name           TEXT NOT NULL,
    city           TEXT NOT NULL,
    airport_iata   TEXT NOT NULL,
    category       TEXT NOT NULL,
    description    TEXT NOT NULL,
    duration_hrs   REAL NOT NULL,
    cost           REAL NOT NULL,
    rating         REAL NOT NULL,
    open_time      TEXT NOT NULL,
    close_time     TEXT NOT NULL,
    days_open      TEXT NOT NULL,
    tags           TEXT NOT NULL,
    max_group      INTEGER NOT NULL,
    accessible     INTEGER NOT NULL,
    vegan_friendly INTEGER NOT NULL
);
""")
conn.commit()

cur.executemany("INSERT INTO airports VALUES (?,?,?,?,?,?)", AIRPORTS)
cur.executemany("INSERT INTO airlines VALUES (?,?,?,?)", AIRLINES)
conn.commit()

# ─── Flights ─────────────────────────────────────────────────────────────────
print("Generating flights (3-day range, 2 per route per day)...")

iatas  = [a[0] for a in AIRPORTS]
others = {a: [b for b in iatas if b != a] for a in iatas}

# Build routes with service profile
# (origin, dest, freq_lo, freq_hi, svc_pct)
routes = []
for origin in iatas:
    for dest in iatas:
        if origin == dest:
            continue
        o_hub = origin in MAJOR_HUBS
        d_hub = dest   in MAJOR_HUBS
        if o_hub and d_hub:
            routes.append((origin, dest, 2, 2, 1.00))
        elif o_hub or d_hub:
            routes.append((origin, dest, 2, 2, 1.00))
        else:
            if random.random() < 0.55:
                routes.append((origin, dest, 2, 2, 0.72))

BATCH = 50_000
buf   = []
fid   = 1
total = 0

def flush(cur, buf):
    cur.executemany(
        "INSERT INTO flights VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", buf
    )
    conn.commit()

for origin, dest, flo, fhi, svc_pct in routes:
    miles  = haversine_miles(origin, dest)
    o_hub  = origin in MAJOR_HUBS
    d_hub  = dest   in MAJOR_HUBS
    al_pool, al_wts = airline_pool(o_hub, d_hub)
    other_ap = [a for a in others[origin] if a != dest]

    for fl_date in ALL_DATES:
        if random.random() > svc_pct:
            continue

        n = random.randint(flo, fhi)
        dep_hours = sorted(random.sample(range(5, 23), min(n, 18)))

        for dep_h in dep_hours:
            al    = random.choices(al_pool, weights=al_wts)[0]
            dur   = round(flight_hours(miles) + random.uniform(-0.05, 0.1), 2)
            cabin = random.choices(["economy", "business"], [0.88, 0.12])[0]
            price = calc_price(miles, al, cabin, fl_date, origin, dest)
            dep   = time(dep_h, random.choice([0,5,10,15,20,25,30,35,40,45,50,55]))
            arr   = time_add(dep, dur)
            stops = random.choices([0, 1], [0.65, 0.35])[0]
            lay   = random.choice(other_ap) if stops and other_ap else None
            lay_m = random.randint(45, 180) if stops else None

            buf.append((
                f"FL{fid:08d}", al, f"{al}{random.randint(100,9999)}",
                origin, dest, fl_date.isoformat(), fmt(dep), fmt(arr),
                dur, price, random.randint(1, 150),
                stops, lay, lay_m, cabin
            ))
            fid += 1

            if len(buf) >= BATCH:
                flush(cur, buf)
                total += len(buf)
                print(f"  ... {total:,} flights written")
                buf = []

if buf:
    flush(cur, buf)
    total += len(buf)
    buf = []

print(f"  → {total:,} total flight records")
cur.execute("CREATE INDEX idx_fl_route ON flights(origin, destination, depart_date, cabin)")
cur.execute("CREATE INDEX idx_fl_date  ON flights(depart_date)")
cur.execute("CREATE INDEX idx_fl_price ON flights(price)")
conn.commit()

# ─── Hotels ──────────────────────────────────────────────────────────────────
print("Generating hotels...")

hotel_rows = []
avail_rows = []
hid = 1

for iata, city, state, *_ in AIRPORTS:
    cm       = CITY_COST_MULT.get(iata, 1.0)
    n_hotels = random.randint(18, 28)

    for _ in range(n_hotels):
        brand, tier, price_range, amenities = random.choice(HOTEL_CHAINS)
        price  = round(random.uniform(*price_range) * cm, 2)
        rating = round(random.uniform(
            *{"luxury": (4.0, 5.0), "upscale": (3.8, 4.9), "midscale": (3.2, 4.5)}.get(tier, (2.5, 4.0))
        ), 1)
        name = (
            f"{brand} {city}" if random.random() > 0.3
            else random.choice([
                f"The {city} {brand}",
                f"{city} Grand {brand}",
                f"Hotel {random.randint(1,999)} {city}",
            ])
        )

        hotel_rows.append((
            f"HT{hid:05d}", name, city, iata, brand, tier,
            price, rating, random.randint(30, 8000),
            json.dumps(amenities), int(random.random() < 0.45),
            int(random.random() < 0.80),
            int("restaurant" in amenities and random.random() < 0.40),
            round(random.uniform(0.3, 20.0), 1), random.randint(1, 6)
        ))

        # Availability windows covering every day in the 5-year range
        d = DATE_START
        while d < DATE_END:
            nights = random.randint(1, 7)
            cout   = min(d + timedelta(days=nights), DATE_END)
            rooms  = random.choices(
                [0,1,2,3,4,5,6,7,8,10],
                [4,5,10,15,20,16,11,10,5,4],
            )[0]
            avail_rows.append((f"HT{hid:05d}", d.isoformat(), cout.isoformat(), rooms))
            d = cout
        hid += 1

cur.executemany("INSERT INTO hotels VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", hotel_rows)
for i in range(0, len(avail_rows), BATCH):
    cur.executemany(
        "INSERT INTO hotel_availability (hotel_id, check_in, check_out, rooms_left) VALUES (?,?,?,?)",
        avail_rows[i:i+BATCH],
    )
conn.commit()
print(f"  → {len(hotel_rows):,} hotels, {len(avail_rows):,} availability windows")
cur.execute("CREATE INDEX idx_ht_city  ON hotels(airport_iata, tier)")
cur.execute("CREATE INDEX idx_av_hotel ON hotel_availability(hotel_id, check_in)")
conn.commit()

# ─── Activities ──────────────────────────────────────────────────────────────
print("Generating activities...")

act_rows = []
aid = 1
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

for iata, city, state, *_ in AIRPORTS:
    cm = CITY_COST_MULT.get(iata, 1.0)

    for tmpl, category, duration, cost_range, tags in ACTIVITY_TEMPLATES:
        name = tmpl.format(city=city)
        if category == "nightlife":
            open_h, close_h = "18:00", "02:00"
        elif "morning" in tags:
            open_h, close_h = "07:00", "13:00"
        elif "outdoor" in tags:
            open_h, close_h = "08:00", "19:00"
        else:
            open_h  = f"{random.randint(9,11):02d}:00"
            close_h = f"{random.randint(17,21):02d}:00"

        days = (
            WEEKDAYS[:]
            if category != "nightlife"
            else random.sample(WEEKDAYS, random.randint(4, 7))
        )
        raw  = random.uniform(*cost_range)
        cost = round(max(0.0, raw * cm) if raw > 5 else raw, 2)

        act_rows.append((
            f"AC{aid:06d}", name, city, iata, category,
            f"A popular {category} experience in {city}, {state}.",
            duration, cost, round(random.uniform(3.4, 5.0), 1),
            open_h, close_h, json.dumps(sorted(days)), json.dumps(tags),
            random.randint(1, 60), int(random.random() < 0.70),
            int("vegan" in tags or ("food" in tags and random.random() < 0.35))
        ))
        aid += 1

    for vr in random.sample(VEGAN_RESTAURANTS, 3):
        cost = round(random.uniform(15, 45) * cm, 2)
        act_rows.append((
            f"AC{aid:06d}", f"{vr} {city}", city, iata,
            "food", f"Vegan restaurant in {city}.",
            1.5, cost, round(random.uniform(4.0, 5.0), 1),
            "11:00", "21:00", json.dumps(WEEKDAYS),
            json.dumps(["food","vegan","indoor","adults","family"]),
            30, 1, 1
        ))
        aid += 1

cur.executemany("INSERT INTO activities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", act_rows)
conn.commit()
print(f"  → {len(act_rows):,} activity records")
cur.execute("CREATE INDEX idx_ac_city ON activities(airport_iata, category)")
conn.commit()

# ─── Export CSVs ─────────────────────────────────────────────────────────────
print("Exporting CSVs...")
for tbl in ["airports", "airlines", "flights", "hotels", "hotel_availability", "activities"]:
    rows = conn.execute(f"SELECT * FROM {tbl}").fetchall()
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {tbl} LIMIT 0").description]
    path = os.path.join(args.csv_dir, f"{tbl}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols); w.writerows(rows)
    print(f"  → {path}  ({len(rows):,} rows)")

conn.close()
print("\n✅ Done!")
print(f"   DB : {args.db}")
print(f"   CSV: {args.csv_dir}/")