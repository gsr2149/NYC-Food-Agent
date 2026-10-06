"""Tools the agent can call.

Each tool is a plain Python function. Gemini reads the function name, the type
hints, and the docstring to decide when and how to call it, so write them for
the model: say what the tool does, when to use it, and what each argument means.

Every tool returns a dict. On failure, return {"error": "..."} with a message
that tells the model what to do next (ask the user, retry with other args)
instead of raising.

The bodies below are STUBS that return fake sample data so you can test the
chat loop end to end. Replace each TODO with real logic.
"""

BOROUGHS = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]


def _check_borough(borough: str) -> str | None:
    if borough.strip().title() not in BOROUGHS:
        return f"Unknown borough '{borough}'. Use one of: {', '.join(BOROUGHS)}."
    return None


def search_restaurants(cuisine: str, borough: str, max_price_level: int = 4) -> dict:
    """Search for real NYC restaurants matching a cuisine, borough, and budget.

    Call this once you know at least the cuisine and borough. This tool makes the
    external API request (e.g. Google Places, Yelp Fusion, or NYC Open Data).

    Args:
        cuisine: Type of food, e.g. "ramen", "tacos", "Italian".
        borough: One of Manhattan, Brooklyn, Queens, Bronx, Staten Island.
        max_price_level: Highest price level to include, 1 ($) to 4 ($$$$).
    """
    if err := _check_borough(borough):
        return {"error": err}
    if not 1 <= max_price_level <= 4:
        return {"error": "max_price_level must be 1-4. Ask the user for their budget."}
    # TODO: call a real API with requests.get(..., timeout=10) and catch
    # requests.RequestException -> return {"error": "...try again or ..."}
    return {
        "results": [
            {"name": f"Sample {cuisine.title()} Spot", "borough": borough,
             "price_level": min(2, max_price_level), "rating": 4.5,
             "address": "123 Example St"},
        ],
        "note": "STUB DATA - replace with a real API call.",
    }


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
