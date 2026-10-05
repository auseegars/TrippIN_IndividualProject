"""Run: python -m pytest tests -q   (or python tests/test_adaptive.py)"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import pandas as pd
from adaptive import adaptive_itinerary, days_within_budget
from itinerary import load_profiles, allocate_slots
from weather import SCENARIOS, weather_fit
from make_synthetic import make

DF = make()

def test_allocate_slots_sums_to_total():
    assert sum(allocate_slots({"a": .6, "b": .4}, 12).values()) == 12

def test_no_outdoors_in_rain_and_snow():
    for p in load_profiles():
        for s in ("rain", "snow"):
            days = adaptive_itinerary(DF, p, s)
            assert (pd.concat(days)["category"] == "outdoors").sum() == 0

def test_budget_cap_all_scenarios():
    for p in load_profiles():
        for s in SCENARIOS:
            days = adaptive_itinerary(DF, p, s)
            assert days_within_budget(days, p["budget_per_day"]) == 100.0

def test_no_duplicate_places_in_itinerary():
    for p in load_profiles():
        items = pd.concat(adaptive_itinerary(DF, p, "heat"))
        assert items["xid"].is_unique

def test_weather_fit_full_for_adaptive():
    for p in load_profiles():
        for s in SCENARIOS:
            assert weather_fit(adaptive_itinerary(DF, p, s), s) == 100.0

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
