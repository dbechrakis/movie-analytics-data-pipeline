"""Small source-response checks before external data reaches the raw tables."""

from typing import Any


def discovery_results(payload: Any, page: int) -> list[dict[str, Any]]:
    """Reject malformed discovery responses, including an empty first page."""
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise ValueError(f"TMDB discovery page {page} has no results list")
    results = payload["results"]
    if page == 1 and not results:
        raise ValueError("TMDB discovery returned no movies on the first page")
    if any(not isinstance(item, dict) for item in results):
        raise ValueError(f"TMDB discovery page {page} contains an invalid movie")
    return results


def movie_details(payload: Any, requested_id: int) -> dict[str, Any]:
    """Prevent a missing or mismatched detail response from masquerading as a movie."""
    if not isinstance(payload, dict) or payload.get("id") != requested_id:
        raise ValueError(f"TMDB details do not match requested movie {requested_id}")
    if not payload.get("title") and not payload.get("original_title"):
        raise ValueError(f"TMDB movie {requested_id} has no title")
    if not isinstance(payload.get("genres"), list):
        raise ValueError(f"TMDB movie {requested_id} has no genres list")
    return payload
