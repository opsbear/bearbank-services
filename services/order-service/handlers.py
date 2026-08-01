"""
order-service — order pricing and orchestration.

Service-owned logic, so a fix here changes order-service alone.
"""

from typing import Any


class PricingUnavailable(Exception):
    """Raised so the caller can turn it into a 503.

    Deliberately NOT a Python builtin: ``summarize_trace_exceptions`` forces an
    incident to ``code_bug`` whenever a builtin dominates the spans, and this
    failure is meant to present as an error-rate problem instead. Changing this
    to, say, KeyError would silently re-categorise the whole scenario.
    """


def apply_pricing(order: dict[str, Any], config: dict[str, Any]) -> float:
    """Price an order.

    The 'new pricing engine' reads a per-currency multiplier. It assumes every
    order carries a currency it knows about — true for the shapes it was tested
    against, false for orders in currencies added since.

    NOTE: the demo's second deliberate defect. The fix is a fallback here; the
    feature flag is a legitimate rollout control, not the bug, so disabling the
    flag would be treating the symptom.
    """
    amount = float(order.get("amount", 1.0) or 1.0)
    features = config.get("features") or {}

    if not features.get("new_pricing_engine"):
        return amount

    multipliers = (config.get("pricing") or {}).get("multipliers") or {}
    currency = order.get("currency", "USD")
    if currency not in multipliers:
        raise PricingUnavailable(f"no multiplier configured for {currency}")
    return amount * float(multipliers[currency])


def handle(request: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    """Price one order. Raises PricingUnavailable -> 503."""
    return {"priced_amount": apply_pricing(request, config)}
