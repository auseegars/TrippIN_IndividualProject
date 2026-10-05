"""Checkpoint 2: weather scenarios for the adaptive planner.

Real-time weather (OpenWeather) is not wired in yet. Instead the same profile is
planned under a fixed set of named scenarios, which is exactly the controlled
comparison the Checkpoint 1 feedback asked for (same profile, different weather).
Each scenario says how usable outdoor activities are.
"""

SCENARIOS = {
    # outdoor_factor: multiplier on interest in outdoor places (0 = exclude)
    # max_outdoor_per_day: hard cap on outdoor stops per day (None = no cap)
    "clear":      {"label": "Clear, 22C",        "outdoor_factor": 1.0,  "max_outdoor_per_day": None},
    "heat":       {"label": "Heat wave, 36C",    "outdoor_factor": 0.35, "max_outdoor_per_day": 1},
    "cold":       {"label": "Cold snap, -8C",    "outdoor_factor": 0.35, "max_outdoor_per_day": 1},
    "rain":       {"label": "Heavy rain",        "outdoor_factor": 0.0,  "max_outdoor_per_day": 0},
    "snow":       {"label": "Snowstorm",         "outdoor_factor": 0.0,  "max_outdoor_per_day": 0},
}


def outdoor_cap(scenario):
    return SCENARIOS[scenario]["max_outdoor_per_day"]


def weather_fit(days, scenario):
    """% of activities that respect the scenario's outdoor rule.
    Under a cap of N outdoor stops/day, outdoor stops beyond N count as unfit."""
    cap = outdoor_cap(scenario)
    total = sum(len(d) for d in days)
    if cap is None:
        return 100.0
    bad = 0
    for d in days:
        n_out = int((d["category"] == "outdoors").sum())
        bad += max(0, n_out - cap)
    return 100.0 * (total - bad) / total
