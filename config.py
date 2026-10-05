"""Project settings for TrippIn."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_CSV = BASE_DIR / "data" / "processed" / "attractions.csv"
CLEANING_REPORT = BASE_DIR / "data" / "processed" / "cleaning_report.txt"
RESULTS_DIR = BASE_DIR / "results"
PROFILES_PATH = BASE_DIR / "profiles.json"

# ---------------------------------------------------------------- destination
# sanity-check the output.
DESTINATION_NAME = "Chicago"
COUNTRY_CODE = "US"
# If the geocoder resolves to the wrong place, set these to override it
LAT_OVERRIDE = 41.8781
LON_OVERRIDE = -87.6298
RADIUS_M = 6000            # search radius around the city center (meters)
LIMIT_PER_CATEGORY = 500   # max results per interest category

SLUG = DESTINATION_NAME.lower().replace(" ", "_")

# ------------------------------------------------- interest categories -> API
# OpenTripMap "kinds" for each of the proposal's interest categories.
CATEGORY_KINDS = {
    "food": "foods",
    "outdoors": "natural,gardens_and_parks",
    "museums": "museums",
    "nightlife": "nightclubs,pubs,bars",
}
# Minimum OpenTripMap popularity rate (1-3) per category.
MIN_RATE = {"food": 2, "outdoors": 2, "museums": 2, "nightlife": 2}
DEDUPE_PRIORITY = ["nightlife", "museums", "outdoors", "food"]

# Order activities appear within a day.
DAY_ORDER = ["outdoors", "museums", "food", "nightlife"]

# ------------------------------------------------------------ cost estimates
# The API has no prices, so these are rough per-person USD ESTIMATES.
# First matching tag wins
PRICE_BY_KIND = [
    ("nightclubs", 25), ("bars", 20), ("pubs", 20),
    ("restaurants", 30), ("cafes", 12), ("fast_food", 10),
    ("museums", 15),
    ("gardens_and_parks", 0), ("beaches", 0), ("natural", 0),
]
DEFAULT_PRICE = {"food": 25, "outdoors": 0, "museums": 15, "nightlife": 20}
