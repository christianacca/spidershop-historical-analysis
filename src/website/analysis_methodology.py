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


def _pill(label: str, tone: str = "neutral") -> dict[str, str]:
    return {"label": label, "tone": tone}


def _shared_wishlist_items() -> list[dict[str, str]]:
    return [
        {
            "label": f"Wishlist delta up: delta >= {WISHLIST_DELTA_INCREASE_THRESHOLD}",
            "detail": "A rise only counts when buyer movement clears the conservative weekly threshold.",
        },
        {
            "label": f"Wishlist delta down: delta <= {WISHLIST_DELTA_DECREASE_THRESHOLD}",
            "detail": "Small changes inside the band remain neutral to avoid noise.",
        },
        {
            "label": f"Small-N flattening: max-min <= {WISHLIST_SMALL_N_FLATTEN_THRESHOLD}",
            "detail": "Flat non-zero distributions collapse to Watch instead of creating an artificial Hot tier.",
        },
    ]


def _shared_window_items() -> list[dict[str, str]]:
    return [
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
    ]


def _shared_window_pills() -> list[dict[str, str]]:
    return [
        _pill(f"Carryover {OOS_CARRYOVER_LOOKBACK}"),
        _pill(f"Current lookback {WISHLIST_DELTA_LOOKBACK}"),
        _pill(f"Previous lookback {WISHLIST_DELTA_PREV_LOOKBACK}"),
    ]


def _shared_escalation_pills() -> list[dict[str, str]]:
    return [_pill("Can escalate", "hot"), _pill("Cannot override supply", "avoid")]


def _core_rule_pill(page_label: str) -> dict[str, str]:
    return _pill(f"Core {page_label} rule", "hot")


def build_breeder_methodology() -> MethodologyDict:
    """Return structured methodology content for the breeder analysis page."""
    return {
        "section_title": "How the breeder analysis works",
        "intro": "Thresholds, compact decision logic, and a worked example that show why a row becomes Hot, Watch, or Avoid.",
        "callout": {
            "title": "Breeder reading lens",
            "body": "Start with supply evidence. Stock pattern sets the base signal, price trend validates or strengthens borderline cases, and wishlist metrics refine urgency without replacing supply logic.",
            "pills": [
                _pill("Supply-first"),
                _pill("Demand modifies confidence"),
                _pill("Conservative by default"),
            ],
        },
        "tabs": [
            {
                "id": "thresholds",
                "label": "Thresholds & Windows",
                "layout": "thresholds",
                "cards": [
                    {
                        "title": "Stock Pattern Thresholds",
                        "pills": [_pill("Supply-first"), _core_rule_pill("breeder")],
                        "items": [
                            {
                                "label": f"Newly Observed: present now, observed in {BREEDER_NEWLY_OBSERVED_MAX_RUNS} runs or fewer, and all observed runs are current trailing runs",
                                "detail": "This protects the breeder page from overreacting when history is genuinely sparse.",
                            },
                            {
                                "label": f"Sustained: OOS runs >= {BREEDER_SUSTAINED_OOS_RUNS}",
                                "detail": "Persistent absence is treated as the strongest supply-side breeding signal.",
                            },
                            {
                                "label": f"Emerging: OOS runs >= {BREEDER_EMERGING_MIN_OOS_RUNS} and < {BREEDER_SUSTAINED_OOS_RUNS}",
                                "detail": "Early tightening counts, but it still needs confirmation to escalate.",
                            },
                            {
                                "label": "Cyclical: current status is IN/OUT",
                                "detail": "Wave restocking stays visible as Watch instead of being treated as stable scarcity.",
                            },
                            {
                                "label": "Always: everything else",
                                "detail": "Consistent availability is the default oversupply state.",
                            },
                        ],
                    },
                    {
                        "title": "Demand Modifiers",
                        "pills": [_pill("Wishlist pressure"), _pill("Delta threshold")],
                        "items": _shared_wishlist_items(),
                    },
                    {
                        "title": "Escalation Rules",
                        "pills": _shared_escalation_pills(),
                        "items": [
                            {
                                "label": "Sustained + price up or flat => Hot",
                                "detail": "The current breeder matrix treats sustained scarcity plus non-falling price as sufficient confirmation for the Hot branch.",
                            },
                            {
                                "label": "Sustained + wishlist Hot => recommendation emphasis only",
                                "detail": "Strong wishlist pressure can strengthen the recommendation wording, but it does not create a second escalation above Hot.",
                            },
                            {
                                "label": "Sustained + price down => misses Hot confirmation",
                                "detail": "The current breeder rules do not promote sustained scarcity when the price signal is falling, so the row drops out of the Hot path.",
                            },
                            {
                                "label": "Emerging + price up => Hot",
                                "detail": "Rising price is the cleanest confirmation path for a two-to-three-run shortage.",
                            },
                            {
                                "label": "Emerging + wishlist Hot + delta up => Hot",
                                "detail": "Demand can only upgrade an emerging pattern when both pressure and momentum are strong.",
                            },
                            {
                                "label": "Always + wishlist Hot => Watch",
                                "detail": "Strong latent demand never overrides consistent availability into a Hot breeder signal.",
                            },
                            {
                                "label": "Always + wishlist Hot + delta down => Avoid",
                                "detail": "Falling momentum keeps oversupplied rows from being dressed up as opportunities.",
                            },
                        ],
                    },
                    {
                        "title": "Time Windows & Caveats",
                        "pills": _shared_window_pills(),
                        "items": _shared_window_items(),
                    },
                ],
            },
            {
                "id": "tree",
                "label": "Decision Tree",
                "layout": "tree",
                "tree": {
                    "title": "Compact Breeder Decision Tree",
                    "root": {
                        "step": "Step 1",
                        "title": "Classify stock pattern from current availability and OOS runs",
                        "copy": "Newly Observed, Sustained, Emerging, Cyclical, or Always.",
                    },
                    "branches": [
                        {
                            "label": "If Sustained",
                            "title": f"OOS runs {BREEDER_SUSTAINED_OOS_RUNS} or more",
                            "copy": f"If price is up or flat, classify as Hot. A falling price misses that Hot confirmation branch. Wishlist Hot can still strengthen the recommendation wording once the row is already Hot, and any OUT-row demand carryover is bounded to {OOS_CARRYOVER_LOOKBACK} runs.",
                        },
                        {
                            "label": "If Emerging",
                            "title": f"OOS runs {BREEDER_EMERGING_MIN_OOS_RUNS} to {BREEDER_SUSTAINED_OOS_RUNS - 1}",
                            "copy": "Price up becomes Hot. Otherwise, Hot wishlist plus rising delta can still escalate the row, but demand has to confirm both pressure and momentum together.",
                        },
                        {
                            "label": "If Newly Observed",
                            "title": f"Observed in {BREEDER_NEWLY_OBSERVED_MAX_RUNS} runs or fewer",
                            "copy": "Stay Watch while the history is sparse. The model exposes the row, but it does not treat missing pre-first-seen runs as proven scarcity.",
                        },
                        {
                            "label": "If Cyclical",
                            "title": "Recent IN/OUT flapping",
                            "copy": "Remain Watch. The model treats this as wave restocking, not stable scarcity.",
                        },
                        {
                            "label": "If Always",
                            "title": "No convincing supply shortage",
                            "copy": "Demand can only lift this to Watch, never Hot. Falling momentum keeps it Avoid.",
                        },
                        {
                            "label": "Demand windows",
                            "title": "Bounded pressure and momentum lookups",
                            "copy": f"Demand signals stay recent: OUT carryover ends after {OOS_CARRYOVER_LOOKBACK} runs, the current delta lookup uses {WISHLIST_DELTA_LOOKBACK} runs, and the previous comparable lookup uses {WISHLIST_DELTA_PREV_LOOKBACK} runs.",
                        },
                    ],
                },
            },
            {
                "id": "example",
                "label": "Worked Example",
                "layout": "example",
                "example": {
                    "title": "Worked Example",
                    "result": "🔥 Hot",
                    "result_tone": "hot",
                    "species": "Aphonopelma seemanni",
                    "subtitle": "Costa Rican Zebra, 1.5 cm",
                    "pills": [_pill("Result: Hot", "hot"), _pill("Aphonopelma seemanni")],
                    "steps": [
                        {
                            "number": "1",
                            "title": "Stock pattern",
                            "detail": f"Current row is OUT and the absence has lasted {BREEDER_SUSTAINED_OOS_RUNS} runs, so the pattern becomes Sustained.",
                        },
                        {
                            "number": "2",
                            "title": "Price trend",
                            "detail": "In this worked example the price climbs from £8.99 to £15.00 to £25.00, so the current breeder price signal is rising rather than softening.",
                        },
                        {
                            "number": "3",
                            "title": "Demand context",
                            "detail": f"Wishlist pressure is strong and recent demand can still carry forward for up to {OOS_CARRYOVER_LOOKBACK} runs while the species remains OUT.",
                        },
                        {
                            "number": "4",
                            "title": "Output row",
                            "detail": "Signal remains Hot because sustained scarcity reached the base trigger first, the non-falling price branch confirmed it, and wishlist strength only reinforced the recommendation wording.",
                        },
                    ],
                },
                "aside": {
                    "title": "What changes when the row is not strong enough?",
                    "items": [
                        "Emerging without price support drops to Watch.",
                        "Always never jumps straight to Hot.",
                        "Newly Observed becomes Watch because the model avoids over-reading sparse history.",
                    ],
                },
            },
        ],
    }


def build_dealer_methodology() -> MethodologyDict:
    """Return structured methodology content for the dealer analysis page."""
    return {
        "section_title": "How the dealer analysis works",
        "intro": "Thresholds, compact decision logic, and a worked example that explain why a row becomes High Risk, Moderate Risk, or Low Risk.",
        "callout": {
            "title": "Dealer reading lens",
            "body": "Start with reliability and restock speed. Wishlist pressure changes urgency inside the supply bands, but healthy supply should not be promoted into a risk state by demand alone.",
            "pills": [
                _pill("Reliability first", "hot"),
                _pill("Demand adjusts urgency"),
                _pill("Healthy supply stays low risk"),
            ],
        },
        "tabs": [
            {
                "id": "thresholds",
                "label": "Thresholds & Windows",
                "layout": "thresholds",
                "cards": [
                    {
                        "title": "Supply Reliability Thresholds",
                        "pills": [_pill("Presence %"), _core_rule_pill("dealer")],
                        "items": [
                            {
                                "label": f"High: presence percentage >= {DEALER_HIGH_RELIABILITY_THRESHOLD}",
                                "detail": "Species present in at least 80% of runs are treated as reliably supplied.",
                            },
                            {
                                "label": f"Medium: >= {DEALER_MEDIUM_RELIABILITY_THRESHOLD} and < {DEALER_HIGH_RELIABILITY_THRESHOLD}",
                                "detail": "Intermittent supply stays in the moderate-risk family unless demand surges.",
                            },
                            {
                                "label": f"Low: presence percentage < {DEALER_MEDIUM_RELIABILITY_THRESHOLD}",
                                "detail": "Supply gaps dominate the classification once the species falls below the medium band.",
                            },
                        ],
                    },
                    {
                        "title": "Restock Speed",
                        "pills": [_pill("Avg OOS duration")],
                        "items": [
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
                    {
                        "title": "Escalation Rules",
                        "pills": _shared_escalation_pills(),
                        "items": [
                            {
                                "label": "Low reliability + slow restock => High Risk",
                                "detail": "This is already enough supply evidence for the urgent dealer bucket.",
                            },
                            {
                                "label": "Low reliability + wishlist Hot or delta up => High Risk",
                                "detail": "Demand can accelerate a weak-supply row into active sourcing urgency.",
                            },
                            {
                                "label": "Medium reliability + wishlist Hot + delta up => High Risk",
                                "detail": "Medium supply only escalates fully when both pressure and momentum align.",
                            },
                            {
                                "label": "High reliability stays Low Risk",
                                "detail": "Even elevated interest never overrides consistently healthy supply.",
                            },
                        ],
                    },
                    {
                        "title": "Time Windows & Caveats",
                        "pills": _shared_window_pills(),
                        "items": _shared_window_items()
                        + [
                            {
                                "label": "Dealer Limited History",
                                "detail": "This appears only when a species has been observed in at most two runs and earlier runs before first observation are ambiguous.",
                            },
                            {
                                "label": "Dealer price pressure",
                                "detail": "Price pressure is informational only. It appears in the table and Drivers text, but it does not decide the dealer risk classification.",
                            },
                        ],
                    },
                ],
            },
            {
                "id": "tree",
                "label": "Decision Tree",
                "layout": "tree",
                "tree": {
                    "title": "Compact Dealer Decision Tree",
                    "root": {
                        "step": "Step 1",
                        "title": "Bucket the row by stock reliability",
                        "copy": f"High at {DEALER_HIGH_RELIABILITY_THRESHOLD:.1f}+ presence, Medium at {DEALER_MEDIUM_RELIABILITY_THRESHOLD:.1f} to {DEALER_HIGH_RELIABILITY_THRESHOLD:.1f}, Low below {DEALER_MEDIUM_RELIABILITY_THRESHOLD:.1f}.",
                    },
                    "branches": [
                        {
                            "label": "If Low",
                            "title": "Supply is already weak",
                            "copy": "Slow restock is already enough to classify the row as High Risk. If restock is faster, Hot wishlist or rising delta can still accelerate sourcing urgency for an already weak supply row.",
                        },
                        {
                            "label": "If Medium",
                            "title": "Variable supply",
                            "copy": "Stay Moderate Risk by default. Restock speed alone does not promote medium reliability rows, so escalate to High Risk only when both Hot wishlist and rising delta combine.",
                        },
                        {
                            "label": "If High",
                            "title": "Healthy supply",
                            "copy": "Remain Low Risk. Restock speed does not override healthy supply, and strong wishlist may trigger monitoring language but does not override the supply classification.",
                        },
                        {
                            "label": "Demand windows",
                            "title": "Bounded momentum, informational price",
                            "copy": f"Wishlist momentum stays recent: the current delta lookup uses {WISHLIST_DELTA_LOOKBACK} runs, the previous comparable lookup uses {WISHLIST_DELTA_PREV_LOOKBACK} runs, and price remains informational only.",
                        },
                        {
                            "label": "Final note",
                            "title": "Append limited-history caveat when needed",
                            "copy": "Sparse evidence becomes explanatory text, not a new risk bucket.",
                        },
                    ],
                },
            },
            {
                "id": "example",
                "label": "Worked Example",
                "layout": "example",
                "example": {
                    "title": "Worked Example",
                    "result": "🔥 High Risk",
                    "result_tone": "hot",
                    "species": "Aphonopelma seemanni",
                    "subtitle": "Costa Rican Zebra, 1.5 cm",
                    "pills": [_pill("Result: High Risk", "hot"), _pill("Aphonopelma seemanni")],
                    "steps": [
                        {
                            "number": "1",
                            "title": "Reliability bucket",
                            "detail": f"This row is tagged Stock Reliability = Low, which places it below the {DEALER_MEDIUM_RELIABILITY_THRESHOLD:.1f} medium-reliability floor and immediately signals weak supply coverage.",
                        },
                        {
                            "number": "2",
                            "title": "Restock speed",
                            "detail": "In this worked example the row is marked Restock Speed = Slow, so the supply gap is not being treated as a quick one-run blip.",
                        },
                        {
                            "number": "3",
                            "title": "Demand pressure",
                            "detail": "Drivers show rising wishlist interest, which reinforces urgency for a low-reliability row instead of letting it sit in passive monitoring.",
                        },
                        {
                            "number": "4",
                            "title": "Output row",
                            "detail": "Dealer Risk becomes High Risk because low reliability already weakens supply, Slow restock confirms the fragility, and the rising wishlist signal only reinforces urgency. Price pressure remains informational only on the dealer page.",
                        },
                    ],
                },
                "aside": {
                    "title": "What changes when the row is healthier?",
                    "items": [
                        "Medium reliability without strong demand stays Moderate Risk.",
                        "High reliability remains Low Risk even when wishlist pressure is strong.",
                        "Limited history adds caution text instead of creating a new risk bucket.",
                    ],
                },
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
