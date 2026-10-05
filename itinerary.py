"""Step 3: baseline and personalized (content-based) itinerary generators.
"""
import argparse
import json
import math

import pandas as pd

import config


# ----------------------------------------------------------------- utilities
def load_attractions():
    return pd.read_csv(config.PROCESSED_CSV)


def load_profiles():
    return json.loads(config.PROFILES_PATH.read_text())


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def pack_into_days(chosen, n_days, per_day):
    """Group chosen places into days by proximity.
    Baseline and personalized system uses, difference in results come from which place was chosen
    """
    remaining = chosen.reset_index(drop=True).copy()
    order = {c: i for i, c in enumerate(config.DAY_ORDER)}
    days = []
    while len(days) < n_days and not remaining.empty:
        seed = remaining.iloc[0]  # best-ranked place not yet scheduled
        dist = remaining.apply(
            lambda r: haversine_km(seed["lat"], seed["lon"], r["lat"], r["lon"]), axis=1)
        pick = dist.sort_values(kind="stable").head(per_day).index
        day = remaining.loc[pick]
        day = (day.assign(_o=day["category"].map(order))
                  .sort_values("_o").drop(columns="_o"))
        days.append(day)
        remaining = remaining.drop(pick)
    return days


# ------------------------------------------------------------------ baseline
def baseline_itinerary(df, profile):
    """Non-AI baseline"""
    n_days, per_day = profile["days"], profile["activities_per_day"]
    ranked = df.sort_values(["popularity", "dist_m"], ascending=[False, True])
    return pack_into_days(ranked.head(n_days * per_day), n_days, per_day)


# ------------------------------------------------------- personalized system
def allocate_slots(weights, total):
    """Split `total` activity slots across categories by interest weight"""
    raw = {c: w * total for c, w in weights.items()}
    slots = {c: int(v) for c, v in raw.items()}
    leftover = total - sum(slots.values())
    for c in sorted(raw, key=lambda c: raw[c] - slots[c], reverse=True)[:leftover]:
        slots[c] += 1
    return slots


def personalized_itinerary(df, profile):
    """Content-based ranking: score = 0.7 * interest match + 0.3 * popularity,
    with slots allocated across categories in proportion to stated interests
    and places too expensive for the daily budget filtered out."""
    n_days, per_day = profile["days"], profile["activities_per_day"]
    total = n_days * per_day

    interests = {c: w for c, w in profile["interests"].items() if w > 0}
    wsum = sum(interests.values())
    weights = {c: w / wsum for c, w in interests.items()}
    wmax = max(weights.values())

    # Budget rule: no single activity may cost more than half the day's budget.
    pool = df[df["est_price"] <= 0.5 * profile["budget_per_day"]].copy()
    pool["interest"] = pool["category"].map(weights).fillna(0) / wmax
    pool["score"] = 0.7 * pool["interest"] + 0.3 * pool["popularity"]
    pool = pool.sort_values(["score", "dist_m"], ascending=[False, True])

    slots = allocate_slots(weights, total)
    chosen = pd.concat([pool[pool["category"] == c].head(n) for c, n in slots.items()])
    if len(chosen) < total:  # a category ran short: fill with next-best places
        chosen = pd.concat([chosen, pool.drop(chosen.index).head(total - len(chosen))])
    chosen = chosen.sort_values(["score", "dist_m"], ascending=[False, True])
    return pack_into_days(chosen, n_days, per_day)


# ------------------------------------------------------------------- metrics
def preference_match(days, profile):
    """% of recommended activities whose category is one of the user's
    stated interests."""
    items = pd.concat(days)
    liked = {c for c, w in profile["interests"].items() if w > 0}
    return 100.0 * items["category"].isin(liked).mean()


def avg_daily_cost(days):
    return sum(d["est_price"].sum() for d in days) / len(days)


# ------------------------------------------------------------------- display
def format_itinerary(title, days, profile):
    lines = [f"=== {title} ===",
             f"Profile: {profile['name']} | interests: {profile['interests']} | "
             f"budget/day: ${profile['budget_per_day']}"]
    running = 0
    for i, day in enumerate(days, 1):
        cost = day["est_price"].sum()
        running += cost
        flag = "  ** over budget **" if cost > profile["budget_per_day"] else ""
        lines.append(f"Day {i}  (est. ${cost:.0f} per person){flag}")
        for _, r in day.iterrows():
            lines.append(f"   - {r['name']}  [{r['category']}]  ~${r['est_price']:.0f} (est.)")
    lines.append(f"Running total (est.): ${running:.0f} per person")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default=None)
    args = parser.parse_args()

    df = load_attractions()
    profiles = load_profiles()
    profile = next((p for p in profiles if p["name"] == args.profile), profiles[0])

    base = baseline_itinerary(df, profile)
    pers = personalized_itinerary(df, profile)
    print(format_itinerary("BASELINE (popularity only)", base, profile))
    print()
    print(format_itinerary("PERSONALIZED (content-based)", pers, profile))
    print()
    print(f"Preference match  baseline: {preference_match(base, profile):.0f}%   "
          f"personalized: {preference_match(pers, profile):.0f}%")


if __name__ == "__main__":
    main()
