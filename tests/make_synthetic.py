"""SMOKE-TEST DATA ONLY. Random places so the code can be unit-tested without the
OpenTripMap cache. Never use this for reported results."""
import numpy as np, pandas as pd

def make(n=200, seed=0):
    rng = np.random.default_rng(seed)
    cats = rng.choice(["food", "outdoors", "museums", "nightlife"], n, p=[.4, .2, .2, .2])
    price = {"food": [10, 12, 30, 30], "outdoors": [0], "museums": [15], "nightlife": [20, 25]}
    return pd.DataFrame({
        "xid": [f"X{i}" for i in range(n)], "name": [f"Place {i}" for i in range(n)],
        "category": cats, "kinds": "", "rate": rng.integers(2, 4, n),
        "has_wikidata": rng.random(n) < .5, "lat": 41.88 + rng.normal(0, .02, n),
        "lon": -87.63 + rng.normal(0, .02, n), "dist_m": rng.integers(100, 6000, n),
        "popularity": rng.random(n), "est_price": [rng.choice(price[c]) for c in cats],
        "indoor": cats != "outdoors"})
