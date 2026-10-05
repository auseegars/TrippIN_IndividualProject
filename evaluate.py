"""Step 4: compare baseline vs personalized on every profile.

    python evaluate.py
Writes results/checkpoint1_results.csv and results/sample_itineraries.txt
"""
import pandas as pd

import config
from itinerary import (avg_daily_cost, baseline_itinerary, format_itinerary,
                       load_attractions, load_profiles, personalized_itinerary,
                       preference_match)


def main():
    df = load_attractions()
    rows, samples = [], []
    for p in load_profiles():
        base = baseline_itinerary(df, p)
        pers = personalized_itinerary(df, p)
        rows.append({
            "profile": p["name"],
            "baseline_pref_match_%": round(preference_match(base, p), 1),
            "personalized_pref_match_%": round(preference_match(pers, p), 1),
            "baseline_avg_daily_cost_$": round(avg_daily_cost(base), 1),
            "personalized_avg_daily_cost_$": round(avg_daily_cost(pers), 1),
            "budget_per_day_$": p["budget_per_day"],
        })
        samples += [format_itinerary("BASELINE", base, p),
                    format_itinerary("PERSONALIZED", pers, p), ""]

    res = pd.DataFrame(rows)
    res["gain_pts"] = (res["personalized_pref_match_%"] - res["baseline_pref_match_%"]).round(1)
    mean = res.drop(columns="profile").mean().round(1)
    mean["profile"] = "MEAN"
    res = pd.concat([res, mean.to_frame().T], ignore_index=True)

    config.RESULTS_DIR.mkdir(exist_ok=True)
    res.to_csv(config.RESULTS_DIR / "checkpoint1_results.csv", index=False)
    (config.RESULTS_DIR / "sample_itineraries.txt").write_text("\n".join(samples))
    print(res.to_string(index=False))
    print("\nSaved results/checkpoint1_results.csv and results/sample_itineraries.txt")


if __name__ == "__main__":
    main()
