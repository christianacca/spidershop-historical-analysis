#!/usr/bin/env python3
from assertions import get_summary_path
from legend_examples import generate_breeder_examples, generate_dealer_examples

# =====================
# LEGEND
# =====================

def write_summary_legend():
    summary_path = get_summary_path()
    if not summary_path:
        return

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("""
<details>
<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>

### 🧬 Breeder Opportunity Matrix — Legend

**OOS** (Current Availability)

- `IN` — Species is currently listed for sale
- `OUT` — Species is not listed this run
- `IN/OUT` — Species recently disappeared and reappeared (cyclical supply)
- **Note:** This reflects CURRENT availability only, not historical supply patterns

**OOS Runs** (Consecutive Scarcity Window)

- Number of **consecutive runs** the species has been out of stock **ending at the current run**
- With weekly runs, `4+` weeks indicates persistent scarcity
- **Resets to 0 when species returns to stock** — focuses on current opportunity window
- Example: A species OUT for 5 weeks, then IN, then OUT for 2 weeks shows `OOS Runs = 2`
- **Key Difference from Dealer Matrix:** Breeder OOS Runs measures current scarcity window (forward-looking opportunity), while Dealer Avg OOS Duration measures historical supply reliability (backward-looking risk assessment)

**Stock Pattern** (Primary Signal)

- `Always` — Normal availability or a single short-term sell-out (noise)
- `Emerging` — Missing for multiple consecutive runs (early scarcity)
- `Sustained` — Missing for many runs (strong breeding signal)
- `Cyclical` — Repeated disappear / reappear pattern (batch supply)
- This is the **foundation** of all recommendations — modifiers can only refine, not override

**Price Trend** (Confidence Modifier)

- `↑` — Price rising vs last observed price
- `→` — Price stable
- `↓` — Price falling
- **Influence:** Can escalate `Emerging` patterns to 🔥 when rising (strong confirmation of demand)
- Does not affect `Sustained` signals (already high-confidence) or downgrade any patterns

**Wishlist Pressure** (Demand Amplifier)

- Represents **latent demand** (buyer interest, not sales)
- Calculated using **relative ranking** within the current run (not absolute thresholds)
- `🔥` — High wishlist pressure (top tier of current interest)
- `⚠️` — Moderate wishlist pressure (middle range)
- `❌` — Low or no wishlist pressure (bottom tier or zero interest)
- For **OUT-of-stock** species: carries forward the most recent pressure from when it was IN (up to 5 runs back)
- **Influence:** Can elevate `Emerging` patterns to 🔥 when combined with rising momentum
- Can prevent `Always` patterns from being dismissed when demand is high
- Never overrides `Sustained` scarcity signals (already definitive)

**Wishlist Delta**

- Measures **meaningful change in wishlist interest** between current and previous IN-stock observations
- `↑` — Buyer interest increasing meaningfully (Delta ≥ +5)
- `→` — Interest stable or within noise threshold (−4 ≤ Delta ≤ +4)
- `↓` — Buyer interest declining meaningfully (Delta ≤ −5)
- Calculated conservatively to avoid false signals from minor fluctuations
- Uses bounded carryover for OUT-of-stock species (up to 3 runs back)
- Acts as a **momentum modifier**, not a standalone signal
- Can escalate or prevent escalation of emerging opportunities

**Signal**

- `🔥` — Strong breeding opportunity signal
- `⚠️` — Monitor closely; opportunity may be forming
- `❌` — Oversupplied or no meaningful scarcity

**Recommendation** (Final Assessment)

- Combines **Stock Pattern + Price Trend + Wishlist Pressure**
- **Hierarchy:** Stock Pattern is primary (~70% influence), Price Trend and Wishlist together provide ~30% refinement
- Modifiers can escalate signals but never override the base pattern category
- Example: `Sustained` scarcity cannot be downgraded by falling prices
- Example: `Always` available cannot reach 🔥 regardless of wishlist interest
- Designed to be conservative to avoid reacting to short-term noise

---

""")
        
        # Write generated Breeder examples
        f.write(generate_breeder_examples())
        f.write("\n\n---\n\n")
        
        f.write("""
### 🏪 Dealer Supply Risk Matrix — Legend

**Stock Reliability** (Historical Supply Pattern)

- `High` — Listed in ≥80% of all historical runs (typically always available)
- `Medium` — Listed in 40-79% of runs (intermittent availability)
- `Low` — Listed in <40% of runs (rarely available)
- This is the **foundation** of all dealer risk assessments — demand modifiers refine but cannot override supply constraints
- **Calculated across entire history**, not just recent weeks
- Example: A species IN stock now but only appeared in 3 of 10 historical weeks = `Low` reliability

**Avg OOS Duration** (Supply Volatility Measure)

- Average number of runs a species stays out of stock per OOS event **across all history**
- Calculated by counting all OOS events (disappearances) and averaging their durations
- Provides context for understanding restock patterns and supply volatility
- Example: OUT for 4 weeks, IN for 1, OUT for 2 weeks, IN now → Avg OOS = 3.0 runs
- **Independent of current availability** — measures historical behavior
- **Key Difference from Breeder Matrix:** Dealer Avg OOS Duration is a historical average (supply reliability indicator), while Breeder OOS Runs counts only the current consecutive OUT period (immediate scarcity signal)

**Restock Speed** (Supply Confidence)

- `Fast` — Typically returns quickly
- `Moderate` — Takes several runs
- `Slow` — Prolonged absence after sell-out
- **Influence:** Combines with Stock Reliability to define supply stability; slow restock amplifies low reliability risks

**Price Pressure** (Informational)

- `↑` — Prices increasing
- `→` — Stable pricing
- `↓` — Prices softening
- **Influence:** Informational only; does not affect risk classification (supply and demand signals take precedence)

**Wishlist Pressure** (Demand Amplifier)

- Represents **latent demand** (buyer interest, not sales)
- Calculated using **relative ranking** within the current run (not absolute thresholds)
- `🔥` — High wishlist pressure (top tier of current interest)
- `⚠️` — Moderate wishlist pressure (middle range)
- `❌` — Low or no wishlist pressure (bottom tier or zero interest)
- For **OUT-of-stock** species: carries forward the most recent pressure from when it was IN (up to 5 runs back)
- **Influence:** Escalates `Low` or `Medium` reliability to 🔥 when combined with poor supply stability
- Can prevent `Medium` reliability from escalating to 🔥 when interest is weak
- Never overrides `High` reliability (already well-supplied)

**Wishlist Delta** (Momentum Modifier)

- Measures **meaningful change in wishlist interest** between current and previous IN-stock observations
- `↑` — Buyer interest increasing meaningfully (Delta ≥ +5)
- `→` — Interest stable or within noise threshold (−4 ≤ Delta ≤ +4)
- `↓` — Buyer interest declining meaningfully (Delta ≤ −5)
- Calculated conservatively to avoid false signals from minor fluctuations
- Uses bounded carryover for OUT-of-stock species (up to 3 runs back)
- **Influence:** Can escalate `Medium` reliability + high pressure to 🔥 when rising (surging demand)
- Can prevent `High` reliability from being dismissed when falling (declining interest)
- Acts as a **momentum modifier**, not a standalone signal

**Dealer Risk** (Supply Signal)

- `🔥` — High risk of lost sales (supply constrained)
- `⚠️` — Manage carefully
- `❌` — No urgency; supply is healthy

**Dealer Recommendation** (Final Assessment)

- Combines **Stock Reliability + Restock Speed + Wishlist Pressure + Wishlist Delta**
- **Hierarchy:** Supply metrics (Reliability + Restock Speed) are primary (~75% influence), demand signals provide ~25% refinement
- Demand modifiers escalate urgency for supply-constrained species but cannot override healthy supply
- Example: `Low` reliability + `Slow` restock = 🔥 regardless of wishlist interest
- Example: `High` reliability cannot reach 🔥 even with surging demand (well-supplied)
- Designed to prevent stockouts while avoiding panic buying of well-stocked items

---

""")
        
        # Write generated Dealer examples
        f.write(generate_dealer_examples())
        f.write("\n\n")
        
        f.write("""
</details>
""")
