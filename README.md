# TrippIn: An Adaptive AI Travel Itinerary Planner
COMP 365 Individual Project (Ayana Seegars)

Content-based itinerary recommender compared against a popularity-only baseline.
Checkpoint 1 covers: data pull + cleaning, baseline, personalized ranking, and a
preference-match evaluation. Weather/news adjustment and the web front end come
in Checkpoint 2.

## Setup
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then paste your real keys into .env
```

## Run (in order)
```bash
python fetch_places.py     # download + cache raw JSON from OpenTripMap
python clean_places.py     # -> data/processed/attractions.csv + cleaning_report.txt
python itinerary.py --profile foodie_budget   # baseline vs personalized demo
python evaluate.py         # -> results/checkpoint1_results.csv
```
Change the destination in `config.py`; user profiles live in `profiles.json`.

## Checkpoint 2 additions
```bash
python tests/test_adaptive.py      # unit tests (synthetic data, no API needed)
python evaluate_cp2.py             # baseline vs static vs weather-aware on profiles x weather scenarios
```
`weather.py` defines 5 fixed weather scenarios; `adaptive.py` is the weather-aware planner with a
hard daily-budget repair step. `--synthetic` is a smoke test only; never report its numbers.

## Data
OpenTripMap Places API (open data: OpenStreetMap/Wikidata). Raw JSON is cached in
`data/raw/`. API keys are read from `.env` and are never committed.

## Current limitations
- OpenTripMap provides no prices or opening hours; prices are category-based estimates
  and hours are empty.
- Weather and news adjustment not implemented yet (indoor/outdoor flag is already in the data).
- Preference-match is partly built into the recommender by design; adaptation accuracy
  and budget accuracy (vs researched prices) are planned for Checkpoint 2.
