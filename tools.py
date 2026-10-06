"""Tools the agent can call.

Each tool is a plain Python function. Gemini reads the function name, the type
hints, and the docstring to decide when and how to call it, so write them for
the model: say what the tool does, when to use it, and what each argument means.

Every tool returns a dict. On failure, return {"error": "..."} with a message
that tells the model what to do next (ask the user, retry with other args)
instead of raising.

Tools marked STUB return fake sample data so you can test the
chat loop end to end. Replace each TODO with real logic.
"""

import os

import requests

BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]


def _check_borough(borough: str) -> str | None:
    if borough.strip().title() not in BOROUGHS:
        return f"Unknown borough '{borough}'. Use one of: {', '.join(BOROUGHS)}."
    return None


PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
# Only ask Google for the fields we use (cheaper and faster).
PLACES_FIELDS = ",".join([
    "places.displayName", "places.formattedAddress", "places.rating",
    "places.userRatingCount", "places.priceLevel", "places.googleMapsUri",
    "places.currentOpeningHours.openNow",
])
# Our 1-4 scale <-> Google's price enum
PRICE_ENUMS = {
    1: "PRICE_LEVEL_INEXPENSIVE", 2: "PRICE_LEVEL_MODERATE",
    3: "PRICE_LEVEL_EXPENSIVE", 4: "PRICE_LEVEL_VERY_EXPENSIVE",
}
PRICE_FROM_ENUM = {v: k for k, v in PRICE_ENUMS.items()}


def search_restaurants(cuisine: str, borough: str, max_price_level: int = 4,
                       near: str = "", open_now: bool = False) -> dict:
    """Search for real NYC restaurants by cuisine, borough, and budget.

    Call this once you know the cuisine and borough. Returns up to 5 places with
    name, address, rating, price level (1-4), whether it is open now, and a
    Google Maps link. Only recommend restaurants that this tool returns.

    Args:
        cuisine: Type of food, e.g. "ramen", "tacos", "Italian", "brunch".
        borough: One of Manhattan, Brooklyn, Queens, Bronx, Staten Island.
        max_price_level: Highest price level to include: 1 ($), 2 ($$),
            3 ($$$), 4 ($$$$). Use 4 if the user has no budget limit.
        near: Optional neighborhood or landmark to search around, e.g.
            "Columbia University", "Williamsburg", "Union Square".
        open_now: True to only return places that are open right now.
    """
    if err := _check_borough(borough):
        return {"error": err}
    if max_price_level not in PRICE_ENUMS:
        return {"error": "max_price_level must be 1, 2, 3, or 4. Ask the user for their budget."}
    borough = borough.strip().title()
    if not cuisine.strip():
        return {"error": "cuisine is empty. Ask the user what they want to eat, or call suggest_cuisines."}

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "Restaurant search is not configured (GOOGLE_MAPS_API_KEY missing). "
                         "Tell the user search is unavailable right now."}

    where = f"near {near}, {borough}" if near.strip() else f"in {borough}"
    body = {
        "textQuery": f"{cuisine} restaurants {where}, New York, NY",
        "includedType": "restaurant",
        "priceLevels": [PRICE_ENUMS[p] for p in range(1, max_price_level + 1)],
        "openNow": open_now,
        "maxResultCount": 5,
    }
    headers = {"X-Goog-Api-Key": api_key, "X-Goog-FieldMask": PLACES_FIELDS}

    try:
        resp = requests.post(PLACES_URL, json=body, headers=headers, timeout=10)
    except requests.RequestException as e:
        return {"error": f"Could not reach the restaurant search service ({type(e).__name__}). "
                         "Try again once; if it fails again, tell the user."}
    if resp.status_code != 200:
        try:
            msg = resp.json()["error"]["message"]
        except (ValueError, KeyError, TypeError):
            msg = resp.text[:200]
        return {"error": f"Restaurant search failed (HTTP {resp.status_code}): {msg}"}

    places = resp.json().get("places", [])
    if not places:
        return {"results": [], "message": (
            f"No {cuisine} restaurants found {where} at that budget"
            f"{' that are open now' if open_now else ''}. Suggest a higher budget, "
            "a nearby borough, or a different cuisine.")}

    results = []
    for p in places:
        level = PRICE_FROM_ENUM.get(p.get("priceLevel"))
        results.append({
            "name": p.get("displayName", {}).get("text"),
            "address": p.get("formattedAddress"),
            "rating": p.get("rating"),
            "review_count": p.get("userRatingCount"),
            "price_level": level,  # 1-4, or None if Google doesn't know
            "price": "$" * level if level else "unknown",
            "open_now": p.get("currentOpeningHours", {}).get("openNow"),
            "maps_url": p.get("googleMapsUri"),
        })
    return {"query": body["textQuery"], "results": results}


def surprise_pick(borough: str, max_price_level: int = 4) -> dict:
    """Pick ONE random restaurant for a user who can't decide.

    Use when the user says something like "just pick for me" or "surprise me".

    Args:
        borough: One of Manhattan, Brooklyn, Queens, Bronx, Staten Island.
        max_price_level: Highest price level to include, 1 ($) to 4 ($$$$).
    """
    if err := _check_borough(borough):
        return {"error": err}
    # TODO: e.g. choose a random cuisine, call search_restaurants, random.choice
    return {"pick": {"name": "Sample Surprise Diner", "borough": borough},
            "note": "STUB DATA"}


def estimate_total_cost(price_level: int, party_size: int = 1,
                        tip_percent: float = 20.0) -> dict:
    """Estimate the total bill for a meal, including NYC sales tax and tip.

    Args:
        price_level: Restaurant price level, 1 ($) to 4 ($$$$).
        party_size: Number of people eating.
        tip_percent: Tip as a percent of the pre-tax subtotal, e.g. 20.
    """
    # TODO: tune these per-person estimates
    per_person = {1: 15, 2: 30, 3: 60, 4: 120}
    if price_level not in per_person:
        return {"error": "price_level must be 1-4."}
    if party_size < 1:
        return {"error": "party_size must be at least 1."}
    subtotal = per_person[price_level] * party_size
    tax = subtotal * 0.08875  # NYC sales tax
    tip = subtotal * tip_percent / 100
    return {"subtotal": round(subtotal, 2), "tax": round(tax, 2),
            "tip": round(tip, 2), "total": round(subtotal + tax + tip, 2)}


def suggest_cuisines(mood: str) -> dict:
    """Suggest a few cuisines based on the user's mood or craving.

    Use when the user doesn't know what kind of food they want.

    Args:
        mood: Free text, e.g. "something cozy", "hungover", "date night", "cheap".
    """
    # TODO: replace with your own mapping or logic
    return {"mood": mood, "suggestions": ["ramen", "pho", "pizza"], "note": "STUB DATA"}


def get_subway_trip(origin: str, destination: str) -> dict:
    """Get subway directions and travel time between two NYC places.

    Use after picking a restaurant to tell the user how to get there.

    Args:
        origin: Where the user is, e.g. "Columbia University" or a street address.
        destination: The restaurant's address.
    """
    # TODO: Google Maps Directions API with mode=transit, or MTA data
    return {"origin": origin, "destination": destination,
            "lines": ["1"], "minutes": 25, "note": "STUB DATA"}


# Registry used by agent.py. Add new tools here.
TOOLS = {
    fn.__name__: fn
    for fn in [search_restaurants, surprise_pick, estimate_total_cost,
               suggest_cuisines, get_subway_trip]
}
