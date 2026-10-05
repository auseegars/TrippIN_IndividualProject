"""Step 2: turn the raw API JSON into one clean table (attractions.csv).
"""
import json
import sys

import pandas as pd

import config


def parse_rate(value):
    """OpenTripMap rates look like 3 or '3h' (h = heritage-listed)."""
    try:
        return min(int(str(value).rstrip("h")), 3)
    except ValueError:
        return 0


def estimate_price(kinds, category):
    for tag, price in config.PRICE_BY_KIND:
        if tag in kinds:
            return price
    return config.DEFAULT_PRICE[category]


def load_category(category):
    path = config.RAW_DIR / f"{config.SLUG}_{category}.json"
    if not path.exists():
        sys.exit(f"Missing {path.name}. Run fetch_places.py first.")
    rows = []
    for item in json.loads(path.read_text()):
        name = (item.get("name") or "").strip()
        point = item.get("point") or {}
        rows.append({
            "xid": item.get("xid"),
            "name": name,
            "category": category,
            "kinds": item.get("kinds", ""),
            "rate": parse_rate(item.get("rate", 0)),
            "has_wikidata": bool(item.get("wikidata")),
            "lat": point.get("lat"),
            "lon": point.get("lon"),
            "dist_m": item.get("dist"),
        })
    return pd.DataFrame(rows)


def main():
    frames = {c: load_category(c) for c in config.CATEGORY_KINDS}
    report = ["TrippIn cleaning report", f"Destination: {config.DESTINATION_NAME}", ""]
    report.append("Raw records per category: " +
                  ", ".join(f"{c}={len(df)}" for c, df in frames.items()))

    # Combine in priority order so ambiguous items (bars) land in the right category.
    df = pd.concat([frames[c] for c in config.DEDUPE_PRIORITY], ignore_index=True)
    n_raw = len(df)

    df = df[df["name"] != ""]
    report.append(f"Dropped unnamed places: {n_raw - len(df)}")

    n = len(df)
    df = df.dropna(subset=["lat", "lon", "xid"])
    report.append(f"Dropped places missing coordinates/id: {n - len(df)}")

    n = len(df)
    df = df.drop_duplicates(subset="xid", keep="first")
    report.append(f"Dropped duplicate ids (same place in 2+ categories): {n - len(df)}")

    # Chains / repeats: keep the most popular copy of each name.
    n = len(df)
    df["_key"] = df["name"].str.lower()
    df = (df.sort_values(["rate", "has_wikidata"], ascending=False)
            .drop_duplicates(subset="_key", keep="first")
            .drop(columns="_key"))
    report.append(f"Dropped repeated names (e.g. chains): {n - len(df)}")

    # Derived features used by the baseline and recommender.
    df["popularity"] = (df["rate"] + 0.5 * df["has_wikidata"]) / 3.5
    df["est_price"] = [estimate_price(k, c) for k, c in zip(df["kinds"], df["category"])]
    df["price_is_estimate"] = True          # API has no prices
    df["hours"] = None                      # API has no hours (known gap)
    df["indoor"] = df["category"] != "outdoors"   # used by weather layer in CP2

    df = df.sort_values(["category", "popularity", "name"],
                        ascending=[True, False, True]).reset_index(drop=True)
    config.PROCESSED_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.PROCESSED_CSV, index=False)

    report += ["", f"Final clean records: {len(df)}", "Records per category:"]
    report += [f"  {c}: {n}" for c, n in df["category"].value_counts().items()]
    report += ["", "Missing data (known gaps):",
               "  hours: 100% missing (not provided by OpenTripMap)",
               "  price: 100% estimated from category/kind lookup, not sourced",
               f"  places with Wikidata entry: {df['has_wikidata'].mean():.0%}",
               "", "Popularity rate distribution:"]
    report += [f"  rate {r}: {n}" for r, n in df["rate"].value_counts().sort_index().items()]
    thin = [c for c in config.CATEGORY_KINDS if (df["category"] == c).sum() < 15]
    if thin:
        report += ["", f"WARNING: thin categories (<15 places): {thin}. "
                       "Lower MIN_RATE or raise RADIUS_M in config.py and re-fetch."]

    text = "\n".join(report)
    config.CLEANING_REPORT.write_text(text)
    print(text)
    print(f"\nSaved {config.PROCESSED_CSV}")


if __name__ == "__main__":
    main()
