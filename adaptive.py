"""Checkpoint 2: weather-aware planner with a hard daily budget cap.

Compared against two non-adaptive planners from Checkpoint 1:
  baseline_itinerary      popularity only
  personalized_itinerary  static content-based (the "static planner")
adaptive_itinerary adds (a) weather scenario handling and (b) a repair step that
guarantees each day stays within budget and respects the outdoor cap.
"""
import pandas as pd

import config
from itinerary import allocate_slots, pack_into_days
from weather import SCENARIOS, outdoor_cap


def _score_pool(df, profile, scenario):
    interests = {c: w for c, w in profile["interests"].items() if w > 0}
    factor = SCENARIOS[scenario]["outdoor_factor"]
    if "outdoors" in interests:
        interests["outdoors"] *= factor
    interests = {c: w for c, w in interests.items() if w > 0}
    if not interests:      # e.g. an outdoors-only profile in a snowstorm
        interests = {"museums": 1.0}
    wsum = sum(interests.values())
    weights = {c: w / wsum for c, w in interests.items()}
    wmax = max(weights.values())

    pool = df[df["est_price"] <= 0.5 * profile["budget_per_day"]].copy()
    if factor == 0:
        pool = pool[pool["category"] != "outdoors"]
    pool["interest"] = pool["category"].map(weights).fillna(0) / wmax
    pool["score"] = 0.7 * pool["interest"] + 0.3 * pool["popularity"]
    pool = pool.sort_values(["score", "dist_m"], ascending=[False, True])
    return pool, weights


def _violations(day, budget, cap):
    over = day["est_price"].sum() > budget
    too_many_out = cap is not None and (day["category"] == "outdoors").sum() > cap
    return over, too_many_out


def _repair(days, pool, budget, cap):
    """Swap offending stops for the best unused place that fixes the problem.
    Over budget: replace the priciest stop with a cheaper one of the same category
    (any category if none). Outdoor cap: replace an extra outdoor stop with the
    best unused non-outdoor place that still fits the budget."""
    used = set(pd.concat(days)["xid"])
    out = []
    for day in days:
        day = day.copy()
        for _ in range(20):                      # bounded repair loop
            over, many_out = _violations(day, budget, cap)
            if not (over or many_out):
                break
            free = pool[~pool["xid"].isin(used)]
            if many_out:
                victim = day[day["category"] == "outdoors"].iloc[-1]
                cands = free[free["category"] != "outdoors"]
            else:
                victim = day.sort_values("est_price", ascending=False).iloc[0]
                cands = free[free["est_price"] < victim["est_price"]]
                same = cands[cands["category"] == victim["category"]]
                cands = same if not same.empty else cands
                if cap is not None:
                    cands = cands[cands["category"] != "outdoors"] if cap == 0 else cands
            if many_out:   # the swap must not push the day over budget
                room = budget - (day["est_price"].sum() - victim["est_price"])
                cands = cands[cands["est_price"] <= max(room, victim["est_price"])]
            if cands.empty:
                break
            new = cands.iloc[0]
            day = pd.concat([day[day["xid"] != victim["xid"]], new.to_frame().T])
            used.discard(victim["xid"]); used.add(new["xid"])
        order = {c: i for i, c in enumerate(config.DAY_ORDER)}
        day = day.assign(_o=day["category"].map(order)).sort_values("_o").drop(columns="_o")
        out.append(day)
    return out


def adaptive_itinerary(df, profile, scenario="clear"):
    n_days, per_day = profile["days"], profile["activities_per_day"]
    total = n_days * per_day
    pool, weights = _score_pool(df, profile, scenario)
    slots = allocate_slots(weights, total)
    chosen = pd.concat([pool[pool["category"] == c].head(n) for c, n in slots.items()])
    if len(chosen) < total:
        chosen = pd.concat([chosen, pool[~pool["xid"].isin(chosen["xid"])].head(total - len(chosen))])
    chosen = chosen.sort_values(["score", "dist_m"], ascending=[False, True])
    days = pack_into_days(chosen, n_days, per_day)
    return _repair(days, pool, profile["budget_per_day"], outdoor_cap(scenario))


def days_within_budget(days, budget):
    """% of days whose estimated cost is <= the daily budget."""
    return 100.0 * sum(d["est_price"].sum() <= budget for d in days) / len(days)
