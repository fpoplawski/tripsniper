from __future__ import annotations

from typing import Dict

from .features import (
    discount_pct,
    absolute_price_score,
    hotel_quality,
    flight_comfort,
    urgency_score,
    novelty_score,
    category_match,
)
from ..models import Offer

__all__ = ["steal_score"]

# Default weight table for individual features. Weights should sum to 1.0 so
# that the final score remains in the 0-100 range.
weights: Dict[str, float] = {
    "discount_pct": 0.25,
    "absolute_price_score": 0.2,
    "hotel_quality": 0.2,
    "flight_comfort": 0.15,
    "urgency_score": 0.05,
    "novelty_score": 0.05,
    "category_match": 0.1,
}


def _clamp(value: float, min_value: float = 0.0, max_value: float = 100.0) -> float:
    """Clamp ``value`` to the inclusive ``min_value`` and ``max_value`` range."""
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value


def steal_score(offer: Offer, user_prefs: Dict[str, object] | None = None) -> float:
    """Compute weighted sum of features and return float score 0–100."""
    user_prefs = user_prefs or {}

    # Determine price limit for absolute price scoring. Use user preference when
    # available, otherwise fall back to the offer's average price.
    try:
        price_limit = float(user_prefs.get("max_price"))  # type: ignore[arg-type]
    except Exception:
        price_limit = offer.avg_price

    feature_values = {
        "discount_pct": discount_pct(offer),
        "absolute_price_score": absolute_price_score(offer, price_limit),
        "hotel_quality": hotel_quality(offer),
        "flight_comfort": flight_comfort(offer),
        "urgency_score": urgency_score(offer),
        "novelty_score": novelty_score(offer),
        "category_match": category_match(offer, user_prefs),
    }

    score = sum(feature_values[name] * weights.get(name, 0.0) for name in feature_values)
    return _clamp(score)
