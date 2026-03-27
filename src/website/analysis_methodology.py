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
        "intro": "Thresholds, compact decision logic, and a rule trace that show why a row becomes Hot, Watch, or Avoid.",
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
                                "detail": "This resolves to ⚠️ Watch. The breeder page exposes the row, but it avoids treating sparse history as proven scarcity.",
                            },
                            {
                                "label": f"Sustained: OOS runs >= {BREEDER_SUSTAINED_OOS_RUNS}",
                                "detail": "This is the strongest supply-side setup. With price up or flat it becomes 🔥 Hot; if price falls, the row misses that Hot branch and drops out of the confirmed Hot path.",
                            },
                            {
                                "label": f"Emerging: OOS runs >= {BREEDER_EMERGING_MIN_OOS_RUNS} and < {BREEDER_SUSTAINED_OOS_RUNS}",
                                "detail": "This defaults to ⚠️ Watch and only becomes 🔥 Hot when price is up, or when wishlist pressure is Hot and delta is rising together.",
                            },
                            {
                                "label": "Cyclical: current status is IN/OUT",
                                "detail": "This resolves to ⚠️ Watch. Wave restocking stays visible without being treated as stable scarcity.",
                            },
                            {
                                "label": "Always: everything else",
                                "detail": "This is the oversupply bucket. It stays ❌ Avoid by default, and the best demand can do is lift it to ⚠️ Watch rather than 🔥 Hot.",
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
                                "label": "Assign 🔥 Hot: Sustained + price up or flat",
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
                                "label": "Assign 🔥 Hot: Emerging + price up",
                                "detail": "Rising price is the cleanest confirmation path for a two-to-three-run shortage.",
                            },
                            {
                                "label": "Assign 🔥 Hot: Emerging + wishlist Hot + delta up",
                                "detail": "Demand can only upgrade an emerging pattern when both pressure and momentum are strong.",
                            },
                            {
                                "label": "Assign ⚠️ Watch: Newly Observed or Cyclical",
                                "detail": "Both of these paths stay visible but unconfirmed. Sparse history and wave restocking do not produce a Hot or Avoid signal on their own.",
                            },
                            {
                                "label": "Assign ⚠️ Watch: Always + wishlist Hot",
                                "detail": "Strong latent demand never overrides consistent availability into a Hot breeder signal.",
                            },
                            {
                                "label": "Assign ❌ Avoid: Always + wishlist Hot + delta down",
                                "detail": "Falling momentum keeps oversupplied rows from being dressed up as opportunities.",
                            },
                            {
                                "label": "Assign ❌ Avoid: Any remaining unmatched path",
                                "detail": "If none of the scarcity or watch-state checks fire, the breeder classifier falls back to oversupplied Avoid.",
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
                        "copy": "Classify the row as Newly Observed, Sustained, Emerging, Cyclical, or Always. From there the breeder page assigns one of three outputs: 🔥 Hot, ⚠️ Watch, or ❌ Avoid.",
                    },
                    "branches": [
                        {
                            "label": "If Sustained",
                            "title": f"OOS runs {BREEDER_SUSTAINED_OOS_RUNS} or more",
                            "copy": f"Assign 🔥 Hot if price is up or flat. A falling price misses that Hot confirmation branch, so this sustained row does not stay on the confirmed Hot path and can fall through to ❌ Avoid if no other watch-state rule applies. Wishlist Hot can still strengthen the recommendation wording once the row is already Hot, and any OUT-row demand carryover is bounded to {OOS_CARRYOVER_LOOKBACK} runs.",
                        },
                        {
                            "label": "If Emerging",
                            "title": f"OOS runs {BREEDER_EMERGING_MIN_OOS_RUNS} to {BREEDER_SUSTAINED_OOS_RUNS - 1}",
                            "copy": "Assign ⚠️ Watch by default. Price up becomes 🔥 Hot. Otherwise, Hot wishlist plus rising delta can still escalate the row to 🔥 Hot, but demand has to confirm both pressure and momentum together.",
                        },
                        {
                            "label": "If Newly Observed",
                            "title": f"Observed in {BREEDER_NEWLY_OBSERVED_MAX_RUNS} runs or fewer",
                            "copy": "Assign ⚠️ Watch while the history is sparse. The model exposes the row, but it does not treat missing pre-first-seen runs as proven scarcity.",
                        },
                        {
                            "label": "If Cyclical",
                            "title": "Recent IN/OUT flapping",
                            "copy": "Assign ⚠️ Watch. The model treats this as wave restocking, not stable scarcity.",
                        },
                        {
                            "label": "If Always",
                            "title": "No convincing supply shortage",
                            "copy": "Assign ❌ Avoid by default. Demand can only lift this to ⚠️ Watch, never Hot, and falling momentum keeps it ❌ Avoid.",
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
                "id": "trace",
                "label": "Rule Trace",
                "layout": "example",
                "example": {
                    "title": "Rule Trace",
                    "result": "🔥 Hot",
                    "result_tone": "hot",
                    "species": "Aphonopelma seemanni",
                    "subtitle": "Costa Rican Zebra, 1.5 cm",
                    "pills": [_pill("Result: Hot", "hot"), _pill("Aphonopelma seemanni")],
                    "steps": [
                        {
                            "number": "1",
                            "title": "Stock pattern",
                            "detail": f"Current row is OUT and the absence has lasted {BREEDER_SUSTAINED_OOS_RUNS} runs, so the first rule hit is Sustained rather than Emerging or Cyclical.",
                        },
                        {
                            "number": "2",
                            "title": "Price trend",
                            "detail": "The price climbs from £8.99 to £15.00 to £25.00, so the confirmation check is price up rather than falling price.",
                        },
                        {
                            "number": "3",
                            "title": "Demand context",
                            "detail": f"Wishlist pressure is strong, and recent demand can still carry forward for up to {OOS_CARRYOVER_LOOKBACK} runs while the species remains OUT. That reinforces the Hot reading, but it is not the primary trigger.",
                        },
                        {
                            "number": "4",
                            "title": "Output row",
                            "detail": "Assign 🔥 Hot because sustained scarcity reached the base trigger first and the non-falling price branch confirmed it. This is not ⚠️ Watch because the row is no longer borderline, and not ❌ Avoid because the Always oversupply path never applied.",
                        },
                    ],
                },
                "aside": {
                    "title": "Rule Trace Contrasts",
                    "items": [
                        "Emerging without price support stays ⚠️ Watch instead of upgrading to 🔥 Hot.",
                        "Always never jumps straight to 🔥 Hot because supply still looks broad.",
                        "Newly Observed stays ⚠️ Watch because the model avoids over-reading sparse history.",
                    ],
                },
            },
        ],
    }


def build_dealer_methodology() -> MethodologyDict:
    """Return structured methodology content for the dealer analysis page."""
    return {
        "section_title": "How the dealer analysis works",
        "intro": "Thresholds, compact decision logic, and a rule trace that explain why a row becomes High Risk, Moderate Risk, or Low Risk.",
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
                                "detail": "This bucket resolves to ❌ Low Risk on the current dealer page. Strong wishlist interest can change the wording, but it does not change the symbol.",
                            },
                            {
                                "label": f"Medium: >= {DEALER_MEDIUM_RELIABILITY_THRESHOLD} and < {DEALER_HIGH_RELIABILITY_THRESHOLD}",
                                "detail": "This bucket defaults to ⚠️ Moderate Risk. It only escalates to 🔥 High Risk when wishlist pressure is Hot and delta is rising together.",
                            },
                            {
                                "label": f"Low: presence percentage < {DEALER_MEDIUM_RELIABILITY_THRESHOLD}",
                                "detail": "Low reliability starts at ⚠️ Moderate Risk. Slow restock, Hot wishlist pressure, or rising delta each upgrade it to 🔥 High Risk; without those fire triggers it stays ⚠️ rather than dropping to ❌ Low Risk.",
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
                                "label": "Assign 🔥 High Risk: Low reliability + slow restock",
                                "detail": "This is already enough supply evidence for the urgent dealer bucket.",
                            },
                            {
                                "label": "Assign 🔥 High Risk: Low reliability + wishlist Hot or delta up",
                                "detail": "Demand can accelerate a weak-supply row into active sourcing urgency.",
                            },
                            {
                                "label": "Assign 🔥 High Risk: Medium reliability + wishlist Hot + delta up",
                                "detail": "Medium supply only escalates fully when both pressure and momentum align.",
                            },
                            {
                                "label": "Assign ⚠️ Moderate Risk: Low reliability unless a fire trigger applies",
                                "detail": "Poor supply alone is already a warning state. Without slow restock, Hot wishlist pressure, or rising delta, the row stays ⚠️ instead of falling to ❌.",
                            },
                            {
                                "label": "Assign ⚠️ Moderate Risk: Medium reliability unless both wishlist Hot and delta up",
                                "detail": "Medium reliability is the watch-state default. Hot wishlist without rising delta still stays ⚠️.",
                            },
                            {
                                "label": "Assign ❌ Low Risk: High reliability, even when wishlist is Hot",
                                "detail": "Even elevated interest never overrides consistently healthy supply, and any remaining unmatched path also falls back to ❌.",
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
                        "copy": f"High at {DEALER_HIGH_RELIABILITY_THRESHOLD:.1f}+ presence resolves to ❌ Low Risk. Medium at {DEALER_MEDIUM_RELIABILITY_THRESHOLD:.1f} to {DEALER_HIGH_RELIABILITY_THRESHOLD:.1f} defaults to ⚠️ Moderate Risk unless demand upgrades it to 🔥 High Risk. Low below {DEALER_MEDIUM_RELIABILITY_THRESHOLD:.1f} also starts at ⚠️ Moderate Risk, then upgrades to 🔥 High Risk when a fire trigger applies.",
                    },
                    "branches": [
                        {
                            "label": "If Low",
                            "title": "Supply is already weak",
                            "copy": "Assign 🔥 High Risk if restock is Slow: slow restock is enough on its own. If restock is faster, Hot wishlist pressure or rising wishlist delta can still produce 🔥 High Risk. If none of those checks fire, low reliability still remains ⚠️ Moderate Risk because weak supply is never treated as fully healthy.",
                        },
                        {
                            "label": "If Medium",
                            "title": "Variable supply",
                            "copy": "Assign ⚠️ Moderate Risk by default. Restock speed alone does not promote medium-reliability rows, so upgrade to 🔥 High Risk only when both Hot wishlist and rising delta combine.",
                        },
                        {
                            "label": "If High",
                            "title": "Healthy supply",
                            "copy": "Assign ❌ Low Risk. Restock speed does not override healthy supply, and even strong wishlist only adds monitoring language rather than a higher-risk symbol.",
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
                "id": "trace",
                "label": "Rule Trace",
                "layout": "example",
                "example": {
                    "title": "Rule Trace",
                    "result": "🔥 High Risk",
                    "result_tone": "hot",
                    "species": "Aphonopelma seemanni",
                    "subtitle": "Costa Rican Zebra, 1.5 cm",
                    "pills": [_pill("Result: High Risk", "hot"), _pill("Aphonopelma seemanni")],
                    "steps": [
                        {
                            "number": "1",
                            "title": "Reliability bucket",
                            "detail": f"Stock Reliability = Low places the row below the {DEALER_MEDIUM_RELIABILITY_THRESHOLD:.1f} medium-reliability floor, so it starts on the weak-supply branch rather than the Medium or High branches.",
                        },
                        {
                            "number": "2",
                            "title": "Restock speed",
                            "detail": "Restock Speed = Slow, so the low-reliability path already has enough supply evidence for the urgent branch instead of a quick one-run blip.",
                        },
                        {
                            "number": "3",
                            "title": "Demand pressure",
                            "detail": "Drivers show rising wishlist interest. That reinforces urgency for a low-reliability row, but the key rule trace is that High Risk was already available once Low reliability and Slow restock combined.",
                        },
                        {
                            "number": "4",
                            "title": "Output row",
                            "detail": "Assign 🔥 High Risk because low reliability plus Slow restock is already enough to trigger the urgent dealer branch. This is not ⚠️ Moderate Risk because the row is beyond the medium-supply watch state, and not ❌ Low Risk because healthy-supply branches never applied. Price pressure remains informational only.",
                        },
                    ],
                },
                "aside": {
                    "title": "Rule Trace Contrasts",
                    "items": [
                        "Medium reliability without strong demand stays ⚠️ Moderate Risk.",
                        "High reliability remains ❌ Low Risk even when wishlist pressure is strong.",
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
