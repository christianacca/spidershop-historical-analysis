#!/usr/bin/env python3
from assertions import get_summary_path

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

**OOS**
- `IN` — Species is currently listed for sale
- `OUT` — Species is not listed this run
- `IN/OUT` — Species recently disappeared and reappeared (cyclical supply)

**OOS Runs**
- Number of **consecutive runs** the species has been out of stock  
- With weekly runs, `4+` weeks indicates persistent scarcity

**Pattern**
- `Always` — Normal availability or a single short-term sell-out (noise)
- `Emerging` — Missing for multiple consecutive runs (early scarcity)
- `Sustained` — Missing for many runs (strong breeding signal)
- `Cyclical` — Repeated disappear / reappear pattern (batch supply)

**Price Trend**
- `↑` — Price rising vs last observed price
- `→` — Price stable
- `↓` — Price falling

**Wishlist Pressure**
- Represents **latent demand** (buyer interest, not sales)
- Calculated using **relative ranking** within the current run (not absolute thresholds)
- `🔥` — High wishlist pressure (top tier of current interest)
- `⚠️` — Moderate wishlist pressure (middle range)
- `❌` — Low or no wishlist pressure (bottom tier or zero interest)
- For **OUT-of-stock** species: carries forward the most recent pressure from when it was IN (up to 3 runs back)
- Acts as a **confidence amplifier** for Pattern/Price signals, not a standalone trigger

**Wishlist Δ**
- Measures **meaningful change in wishlist interest** between current and previous IN-stock observations
- `↑` — Buyer interest increasing meaningfully (Δ ≥ +5)
- `→` — Interest stable or within noise threshold (−4 ≤ Δ ≤ +4)
- `↓` — Buyer interest declining meaningfully (Δ ≤ −5)
- Calculated conservatively to avoid false signals from minor fluctuations
- Uses bounded carryover for OUT-of-stock species (≤ 3 runs)
- Acts as a **momentum modifier**, not a standalone signal
- Can escalate or prevent escalation of emerging opportunities

**Signal**
- `🔥` — Strong breeding opportunity signal
- `⚠️` — Monitor closely; opportunity may be forming
- `❌` — Oversupplied or no meaningful scarcity

**Recommendation**
- Combines **Pattern + Price Trend + Wishlist Pressure**
- Designed to be conservative to avoid reacting to short-term noise

---

### 🏪 Dealer Supply Risk Matrix — Legend

**Stock Reliability**
- `High` — Listed in most runs
- `Medium` — Intermittent availability
- `Low` — Rarely listed

**Avg OOS Duration**
- Average number of runs a species stays out of stock once it disappears

**Restock Speed**
- `Fast` — Typically returns quickly
- `Moderate` — Takes several runs
- `Slow` — Prolonged absence after sell-out

**Price Pressure**
- `↑` — Prices increasing
- `→` — Stable pricing
- `↓` — Prices softening

**Wishlist Pressure**
- Represents **latent demand** (buyer interest, not sales)
- Calculated using **relative ranking** within the current run (not absolute thresholds)
- `🔥` — High wishlist pressure (top tier of current interest)
- `⚠️` — Moderate wishlist pressure (middle range)
- `❌` — Low or no wishlist pressure (bottom tier or zero interest)
- For **OUT-of-stock** species: carries forward the most recent pressure from when it was IN (up to 3 runs back)
- Escalates urgency where supply is unreliable; de-escalates where interest is weak

**Wishlist Δ**
- Measures **meaningful change in wishlist interest** between current and previous IN-stock observations
- `↑` — Buyer interest increasing meaningfully (Δ ≥ +5)
- `→` — Interest stable or within noise threshold (−4 ≤ Δ ≤ +4)
- `↓` — Buyer interest declining meaningfully (Δ ≤ −5)
- Calculated conservatively to avoid false signals from minor fluctuations
- Uses bounded carryover for OUT-of-stock species (≤ 3 runs)
- Acts as a **momentum modifier**, not a standalone signal
- Reinforces risk assessments based on supply reliability

**Dealer Risk**
- `🔥` — High risk of lost sales (supply constrained)
- `⚠️` — Manage carefully
- `❌` — No urgency; supply is healthy

**Dealer Recommendation**
- Indicates whether a dealer should actively seek stock, buy opportunistically, or wait

</details>
""")
