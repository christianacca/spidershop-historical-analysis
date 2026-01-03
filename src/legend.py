#!/usr/bin/env python3
from assertions import get_summary_paths

# =====================
# LEGEND
# =====================

def write_summary_legend():
    summary_paths = get_summary_paths()
    if not summary_paths:
        return

    for summary_path in summary_paths:
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

**Signal**
- `🔥` — Strong breeding opportunity signal
- `⚠️` — Monitor closely; opportunity may be forming
- `❌` — Oversupplied or no meaningful scarcity

**Recommendation**
- Combines **Pattern + Price Trend**
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

**Dealer Risk**
- `🔥` — High risk of lost sales (supply constrained)
- `⚠️` — Manage carefully
- `❌` — No urgency; supply is healthy

**Dealer Recommendation**
- Indicates whether a dealer should actively seek stock, buy opportunistically, or wait

</details>
""")
