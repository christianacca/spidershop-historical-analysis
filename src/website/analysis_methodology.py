"""Structured methodology content for analysis pages.

The content in this module is derived from the live production analysis rules.
Threshold values are imported directly from the scoring modules and shared config
so the rendered methodology stays aligned with the real classifier behavior.
"""

from __future__ import annotations

from typing import Any

from scrape.breeder_matrix import (
    BREEDER_EMERGING_MIN_OOS_RUNS,
    BREEDER_NEWLY_OBSERVED_MAX_RUNS,
    BREEDER_SUSTAINED_OOS_RUNS,
)
from scrape.dealer_matrix import (
    DEALER_HIGH_RELIABILITY_THRESHOLD,
    DEALER_MEDIUM_RELIABILITY_THRESHOLD,
    DEALER_MODERATE_RESTOCK_AVG_OOS,
    DEALER_SLOW_RESTOCK_MIN_AVG_OOS,
)
from shared.config import (
    OOS_CARRYOVER_LOOKBACK,
    WISHLIST_DELTA_DECREASE_THRESHOLD,
    WISHLIST_DELTA_INCREASE_THRESHOLD,
    WISHLIST_DELTA_LOOKBACK,
    WISHLIST_DELTA_PREV_LOOKBACK,
    WISHLIST_SMALL_N_FLATTEN_THRESHOLD,
)


MethodologyDict = dict[str, Any]


def _shared_wishlist_threshold_group() -> dict[str, Any]:
    return {
        "title": "Shared wishlist thresholds",
        "items": [
            {
                "label": f"Wishlist delta up: delta >= {WISHLIST_DELTA_INCREASE_THRESHOLD}",
                "detail": "A rise only counts when buyer movement clears the conservative weekly threshold.",
            },
            {
                "label": f"Wishlist delta down: delta <= {WISHLIST_DELTA_DECREASE_THRESHOLD}",
                "detail": "Small changes inside the band remain neutral to avoid noise.",
            },
            {
                "label": f"OOS carryover lookback: {OOS_CARRYOVER_LOOKBACK} runs",
                "detail": "OUT rows can inherit their most recent in-stock wishlist pressure for a bounded period.",
            },
            {
                "label": f"Current delta lookup window: {WISHLIST_DELTA_LOOKBACK} runs",
                "detail": "When a species is OUT now, momentum uses only a short carryover window.",
            },
            {
                "label": f"Previous comparable lookup window: {WISHLIST_DELTA_PREV_LOOKBACK} runs",
                "detail": "Older baselines are ignored so momentum is not compared against stale history.",
            },
            {
                "label": f"Small-N flattening: max-min <= {WISHLIST_SMALL_N_FLATTEN_THRESHOLD}",
                "detail": "Flat non-zero distributions collapse to Watch instead of creating an artificial Hot tier.",
            },
        ],
    }


def build_breeder_methodology() -> MethodologyDict:
    """Return structured methodology content for the breeder analysis page."""
    return {
        "section_title": "Methodology",
        "summary": {
            "title": "How the breeder analysis works",
            "intro": "The breeder model is supply-first. Stock pattern decides the base signal, price trend confirms or strengthens it, and wishlist metrics only upgrade confidence when scarcity is already emerging.",
            "bullets": [
                "The classifier prefers neutral interpretations over early noisy signals.",
                "Supply persistence matters more than one-week demand spikes.",
                "Newly Observed is a real breeder bucket, not a generic missing-data warning.",
            ],
        },
        "worked_example": {
            "title": "Worked example",
            "species": "Aphonopelma seemanni",
            "result": "🔥 Hot",
            "steps": [
                {
                    "label": "1. Stock pattern",
                    "detail": f"In the local preview row, the species is marked OUT with OOS Runs = {BREEDER_SUSTAINED_OOS_RUNS}, so the breeder table classifies it as Sustained scarcity.",
                },
                {
                    "label": "2. Price confirmation",
                    "detail": "Its demo price history ends at £25 after stepping up through £17, £18, £20, and £22, so the scarcity signal is supported by a clear late-window price rise.",
                },
                {
                    "label": "3. Demand modifier",
                    "detail": f"The same preview row finishes with wishlist counts rising to 18, and that demand can still carry forward for up to {OOS_CARRYOVER_LOOKBACK} runs while the species stays OUT.",
                },
                {
                    "label": "4. Final outcome",
                    "detail": "That combination matches the demo recommendation: sustained scarcity first, then rising price and demand confirming a Hot breeder call instead of creating it from scratch.",
                },
            ],
        },
        "threshold_groups": [
            {
                "title": "Breeder stock-pattern rules",
                "items": [
                    {
                        "label": f"Newly Observed: present in the current run, observed in at most {BREEDER_NEWLY_OBSERVED_MAX_RUNS} runs total, and those observations are the trailing runs",
                        "detail": "This protects the breeder page from overreacting when history is genuinely sparse.",
                    },
                    {
                        "label": f"Sustained: OOS runs >= {BREEDER_SUSTAINED_OOS_RUNS}",
                        "detail": "Persistent absence is treated as the strongest supply-side breeding signal.",
                    },
                    {
                        "label": f"Emerging: OOS runs >= {BREEDER_EMERGING_MIN_OOS_RUNS} and < {BREEDER_SUSTAINED_OOS_RUNS}",
                        "detail": "Early tightening counts, but it needs support from price or demand to escalate.",
                    },
                    {
                        "label": "Cyclical: current status is IN/OUT",
                        "detail": "The model treats flapping availability as a Watch pattern rather than a full scarcity signal.",
                    },
                    {
                        "label": "Always: everything else",
                        "detail": "Consistent availability is the default oversupply state.",
                    },
                ],
            },
            _shared_wishlist_threshold_group(),
        ],
        "decision_tree": {
            "title": "Compact breeder decision tree",
            "nodes": [
                {
                    "label": "Newly Observed => Watch",
                    "detail": "Sparse current-history rows stay in a caution state instead of escalating.",
                },
                {
                    "label": "Sustained + price up or flat => Hot",
                    "detail": "Wishlist Hot can reinforce the call, but it is not required once scarcity is sustained.",
                },
                {
                    "label": "Emerging + price up => Hot",
                    "detail": "Rising price is the cleanest escalation path for a two-to-three-run shortage.",
                },
                {
                    "label": "Emerging + wishlist Hot + delta up => Hot",
                    "detail": "Demand can only upgrade an emerging pattern when both pressure and momentum are strong.",
                },
                {
                    "label": "Emerging or Cyclical without enough confirmation => Watch",
                    "detail": "The model keeps borderline rows visible without overselling certainty.",
                },
                {
                    "label": "Always + wishlist Hot => Watch unless delta is down, otherwise Avoid",
                    "detail": "Strong latent demand never overrides consistent availability into a Hot breeder signal.",
                },
            ],
        },
        "edge_cases": [
            {
                "title": "Breeder Newly Observed",
                "body": "This is its own breeder classification. A row can be newly observed only when it is in stock now, appears in no more than two total runs, and those observations are the trailing runs.",
            },
            {
                "title": "Bounded wishlist carryover",
                "body": "OUT rows keep recent demand context only inside the bounded carryover and lookup windows, so old interest cannot prop up stale opportunities forever.",
            },
        ],
    }


def build_dealer_methodology() -> MethodologyDict:
    """Return structured methodology content for the dealer analysis page."""
    return {
        "section_title": "Methodology",
        "summary": {
            "title": "How the dealer analysis works",
            "intro": "The dealer model is also supply-first. Reliability and restock speed set the base risk level, while wishlist pressure only adjusts urgency inside those supply bands.",
            "bullets": [
                "Low reliability can escalate quickly when demand is rising.",
                "Medium reliability stays in the middle bucket unless demand is unusually strong.",
                "High reliability remains Low Risk even when interest is elevated.",
            ],
        },
        "worked_example": {
            "title": "Worked example",
            "species": "Monocentropus balfouri",
            "result": "🔥 High Risk",
            "steps": [
                {
                    "label": "1. Reliability band",
                    "detail": f"In local preview data, this row is explicitly tagged Stock Reliability = Low, which places it below the {DEALER_MEDIUM_RELIABILITY_THRESHOLD:.1f} medium-reliability floor.",
                },
                {
                    "label": "2. Restock speed",
                    "detail": f"Its demo Avg OOS Duration is 3.1 runs, which clears the slow-restock threshold of {DEALER_SLOW_RESTOCK_MIN_AVG_OOS} runs and keeps recovery pressure high.",
                },
                {
                    "label": "3. Demand context",
                    "detail": "The preview row also carries premium-demand context with a wishlist value of 17, so buyer pressure reinforces the supply warning instead of replacing it.",
                },
                {
                    "label": "4. Final outcome",
                    "detail": "That is why the local dealer row lands on High Risk: Low reliability plus Slow restock is already enough, and the demand context just strengthens the reorder urgency.",
                },
            ],
        },
        "threshold_groups": [
            {
                "title": "Dealer reliability and restock rules",
                "items": [
                    {
                        "label": f"High reliability: presence percentage >= {DEALER_HIGH_RELIABILITY_THRESHOLD}",
                        "detail": "Species present in at least 80% of runs are treated as reliably supplied.",
                    },
                    {
                        "label": f"Medium reliability: >= {DEALER_MEDIUM_RELIABILITY_THRESHOLD} and < {DEALER_HIGH_RELIABILITY_THRESHOLD}",
                        "detail": "Intermittent supply stays in the moderate-risk family unless demand surges.",
                    },
                    {
                        "label": f"Low reliability: presence percentage < {DEALER_MEDIUM_RELIABILITY_THRESHOLD}",
                        "detail": "Supply gaps dominate the classification once the species falls below the medium band.",
                    },
                    {
                        "label": f"Slow restock: average OOS duration >= {DEALER_SLOW_RESTOCK_MIN_AVG_OOS}",
                        "detail": "Extended stockouts compound low reliability into the most urgent dealer state.",
                    },
                    {
                        "label": f"Moderate restock: average OOS duration == {DEALER_MODERATE_RESTOCK_AVG_OOS}",
                        "detail": "Two-run stockouts remain concerning but do not automatically become severe.",
                    },
                    {
                        "label": "Fast restock: anything quicker",
                        "detail": "Fast recovery prevents mild supply gaps from over-escalating.",
                    },
                ],
            },
            _shared_wishlist_threshold_group(),
        ],
        "decision_tree": {
            "title": "Compact dealer decision tree",
            "nodes": [
                {
                    "label": "Low reliability + slow restock => High Risk",
                    "detail": "This is the clearest supply-failure case, with or without strong demand.",
                },
                {
                    "label": "Low reliability + wishlist Hot or delta up => High Risk",
                    "detail": "Demand can accelerate a low-reliability row into the urgent bucket.",
                },
                {
                    "label": "Medium reliability + wishlist Hot + delta up => High Risk",
                    "detail": "Medium supply only escalates fully when both pressure and momentum align.",
                },
                {
                    "label": "Medium reliability otherwise => Moderate Risk",
                    "detail": "The model exposes variable supply without overstating it as a crisis.",
                },
                {
                    "label": "High reliability stays Low Risk",
                    "detail": "Even Hot wishlist pressure never overrides a consistently supplied species into a higher dealer bucket.",
                },
            ],
        },
        "edge_cases": [
            {
                "title": "Dealer Limited History",
                "body": "This is an appended caution note, not its own risk bucket. It appears only when a species has been observed in at most two runs and the pre-first-seen runs are ambiguous.",
            },
            {
                "title": "Dealer price pressure",
                "body": "Price pressure is informational only. It appears in the table and in the Drivers text, but it does not decide the dealer risk classification.",
            },
        ],
    }


def build_analysis_methodology(page_type: str) -> MethodologyDict | None:
    """Return methodology content for an analysis page type."""
    if page_type == "breeder":
        return build_breeder_methodology()
    if page_type == "dealer":
        return build_dealer_methodology()
    return None
