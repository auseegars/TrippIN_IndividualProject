"""Step 1: pull attraction data from OpenTripMap and cache the raw JSON."""
import argparse
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

import config

load_dotenv(config.BASE_DIR / ".env")
API_KEY = os.getenv("OPENTRIPMAP_API_KEY")
BASE_URL = "https://api.opentripmap.com/0.1/en/places"


def api_get(endpoint, **params):
    params["apikey"] = API_KEY
    resp = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=30)
    if resp.status_code != 200:
        sys.exit(f"OpenTripMap error {resp.status_code} on '{endpoint}': {resp.text[:300]}")
    return resp.json()


def get_center(refresh):
    cache = config.RAW_DIR / f"{config.SLUG}_center.json"
    if cache.exists() and not refresh:
        return json.loads(cache.read_text())
    if config.LAT_OVERRIDE is not None and config.LON_OVERRIDE is not None:
        center = {"name": config.DESTINATION_NAME,
                  "lat": config.LAT_OVERRIDE, "lon": config.LON_OVERRIDE}
    else:
        data = api_get("geoname", name=config.DESTINATION_NAME,
                       country=config.COUNTRY_CODE)
        if data.get("status") != "OK":
            sys.exit(f"Could not geocode '{config.DESTINATION_NAME}': {data}. "
                     "Set LAT_OVERRIDE / LON_OVERRIDE in config.py.")
        center = {"name": data["name"], "lat": data["lat"], "lon": data["lon"],
                  "country": data.get("country")}
    cache.write_text(json.dumps(center, indent=2))
    return center


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args()

    if not API_KEY or API_KEY == "your_key_here":
        sys.exit()

    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    center = get_center(args.refresh)
    print(f"Destination resolved to: {center}  <-- check this is the right place!")

    for category, kinds in config.CATEGORY_KINDS.items():
        cache = config.RAW_DIR / f"{config.SLUG}_{category}.json"
        if cache.exists() and not args.refresh:
            n = len(json.loads(cache.read_text()))
            print(f"[cached] {category}: {n} places")
            continue
        data = api_get(
            "radius",
            radius=config.RADIUS_M, lon=center["lon"], lat=center["lat"],
            kinds=kinds, rate=config.MIN_RATE[category],
            format="json", limit=config.LIMIT_PER_CATEGORY,
        )
        cache.write_text(json.dumps(data, indent=2))
        print(f"[fetched] {category}: {len(data)} places -> {cache.name}")
        time.sleep(0.5)  # be polite to the free tier

    print("Done. Next: python clean_places.py")


if __name__ == "__main__":
    main()
