"""Checkpoint 2 evaluation: baseline vs static personalized vs weather-aware adaptive,
same profiles x same weather scenarios.

    python evaluate_cp2.py              # real data: data/processed/attractions.csv
    python evaluate_cp2.py --synthetic  # smoke test only, writes to results/synthetic/

Cases = profiles x scenarios. Per case, three planners are scored on:
  pref_match_%      share of stops in a liked category (partly built in; see README)
  budget_ok_%       share of days with estimated cost <= daily budget
  weather_fit_%     share of stops that respect the scenario's outdoor rule
  overlap_with_static_%  how much the adaptive plan differs from the static one
Not measured yet: reviewer-judged relevance, real prices.
"""
import argparse, sys
import pandas as pd
import config
from adaptive import adaptive_itinerary, days_within_budget
from itinerary import (baseline_itinerary, format_itinerary, load_attractions,
                       load_profiles, personalized_itinerary, preference_match, avg_daily_cost)
from weather import SCENARIOS, weather_fit


def overlap(a, b):
    sa, sb = set(pd.concat(a)["xid"]), set(pd.concat(b)["xid"])
    return 100.0 * len(sa & sb) / len(sa | sb)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--synthetic", action="store_true")
    args = ap.parse_args()
    if args.synthetic:
        sys.path.insert(0, str(config.BASE_DIR / "tests"))
        from make_synthetic import make
        df, out = make(), config.RESULTS_DIR / "synthetic"
    else:
        df, out = load_attractions(), config.RESULTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    rows, samples = [], []
    for p in load_profiles():
        for s in SCENARIOS:
            plans = {"baseline": baseline_itinerary(df, p),
                     "static": personalized_itinerary(df, p),
                     "adaptive": adaptive_itinerary(df, p, s)}
            for name, days in plans.items():
                rows.append({"profile": p["name"], "scenario": s, "planner": name,
                             "pref_match_%": round(preference_match(days, p), 1),
                             "budget_ok_%": round(days_within_budget(days, p["budget_per_day"]), 1),
                             "weather_fit_%": round(weather_fit(days, s), 1),
                             "avg_daily_cost_$": round(avg_daily_cost(days), 1),
                             "overlap_with_static_%": round(overlap(days, plans["static"]), 1)})
            if s in ("clear", "rain"):
                samples += [f"##### scenario: {SCENARIOS[s]['label']}",
                            format_itinerary("STATIC", plans["static"], p),
                            format_itinerary("ADAPTIVE", plans["adaptive"], p), ""]
    res = pd.DataFrame(rows)
    res.to_csv(out / "checkpoint2_cases.csv", index=False)
    summary = (res.groupby("planner")[["pref_match_%", "budget_ok_%", "weather_fit_%",
                                       "avg_daily_cost_$"]].mean().round(1))
    summary["cases"] = res.groupby("planner").size()
    by_scn = res.pivot_table(index="scenario", columns="planner", values="weather_fit_%").round(1)
    summary.to_csv(out / "checkpoint2_summary.csv"); by_scn.to_csv(out / "checkpoint2_weather_fit_by_scenario.csv")
    (out / "sample_itineraries_cp2.txt").write_text("\n".join(samples))
    print(summary.to_string()); print(); print(by_scn.to_string())
    print(f"\nWrote results to {out}")


if __name__ == "__main__":
    main()
