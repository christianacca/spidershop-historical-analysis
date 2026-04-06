
<details>
<summary><strong>ℹ️ How to read these tables (Legend)</strong></summary>

### 🧬 Breeder Opportunity Matrix — Legend

**Size (cm)** (Current Listing Context)

- Shows the currently active size for the species
- `1.5` — single currently active size
- `3, 5` — multiple size variants currently listed at the same time (multi-variant)
- When the species is currently OUT, shows the most recently active size
- `—` — species is currently OUT with no identifiable recent size in the standard lookback window
- When a confirmed size transition occurred recently, a ℹ️ icon appears on the **Price** and **Price History** cells (see below)

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
- Runs before a species is first observed are **ambiguous** and do not count as breeder scarcity evidence
- **Key Difference from Dealer Matrix:** Breeder OOS Runs measures current scarcity window (forward-looking opportunity), while Dealer Avg OOS Duration measures historical supply reliability (backward-looking risk assessment)

**Stock Pattern** (Primary Signal)

- `Always` — Normal availability or a single short-term sell-out (noise)
- `Emerging` — Missing for multiple consecutive runs (early scarcity)
- `Sustained` — Missing for many runs (strong breeding signal)
- `Cyclical` — Repeated disappear / reappear pattern (batch supply)
- `Newly Observed` — Currently in stock, but only observed in the latest 1-2 runs; limited history means pre-first-seen absence is ambiguous

**Price** (Value + Trend)

- Shows current (or last-seen) price plus direction (e.g., `£30.00 ↑`)
- `↑` — Price rising vs last observed price
- `→` — Price stable
- `↓` — Price falling
- `Multiple active prices` — two or more size variants are active simultaneously; no single price line is reliable
- **ℹ️ icon** — appears when the listing recently changed its displayed size (confirmed or ambiguous transition); hover or tap for an explanation of the size change and its effect on price interpretation

**Price History** (Trend Visualization)

- Unicode sparkline showing last 8 weeks of pricing (▁▂▃▄▅▆▇█)
- Each character represents one week (left = oldest, right = most recent)
- Height indicates relative price within the period
- When species is OUT of stock, last known price is carried forward (prices persist even when not actively sold)
- Shows pricing stability or volatility at a glance
- Example: `▁▂▃▄▅▆▇█` shows steady price increases over 8 weeks
- `-` — price history is not shown when a size transition is ambiguous or two sizes are simultaneously active (price continuity cannot be guaranteed)
- **ℹ️ icon** — same as the Price cell; indicates price continuity may be partly affected by a recent size change

**Wishlist** (Count · Demand Tier · Momentum)

- Shows `count tier momentum` (e.g., `57 🔥 →`) — the raw wishlist count, relative demand tier, and momentum signal
- **Count** — raw wishlist count (higher = more buyer interest); table sorts by count descending within each signal group
- **Tier** (`🔥`/`⚠️`/`❌`) — relative ranking within the current run (not absolute thresholds); for **OUT-of-stock** species carries forward from most recent IN-stock run (up to 5 runs back)
- **Momentum** (`↑`/`→`/`↓`) — meaningful change between current and previous IN-stock observations (±5 threshold); uses bounded carryover for OUT species (up to 3 runs back); returns `→` when no comparable value found
- Adds demand context beside the supply columns; see the methodology section for exact escalation rules.

**Wishlist History** (Trend Visualization)

- Unicode sparkline showing last 8 weeks of wishlist counts (▁▂▃▄▅▆▇█)
- Each character represents one week (left = oldest, right = most recent)
- Height indicates relative wishlist interest within the period
- When species is OUT of stock, last known wishlist count is carried forward (interest persists)
- Shows demand trajectory and momentum at a glance
- Example: `▁▂▄▆█` shows accelerating interest over 5 weeks
- `-` — wishlist history is not shown when a size transition is ambiguous or two sizes are simultaneously active (momentum continuity cannot be guaranteed)

**Signal**

- `🔥` — Strong breeding opportunity signal
- `⚠️` — Monitor closely; opportunity may be forming
- `❌` — Oversupplied or no meaningful scarcity
- `Newly Observed` stays in the `⚠️` bucket until more runs exist; it is a limited-history hold state, not confirmed scarcity or abundance

**Recommendation** (Final Assessment)

- Combines **Stock Pattern + Price + Wishlist**
- Final label shown in the table after the row's supply and demand columns are considered together.
- See the methodology section above for the detailed decision rules and rule trace.

---

{{ breeder_examples }}

---

### 🏪 Dealer Supply Risk Matrix — Legend

**Size (cm)** (Current Listing Context)

- Shows the currently active size for the species
- `1.5` — single currently active size
- `3, 5` — multiple size variants currently listed at the same time (multi-variant)
- When the species is currently OUT, shows the most recently active size
- `—` — species is currently OUT with no identifiable recent size in the standard lookback window
- When a confirmed size transition occurred recently, a ℹ️ icon appears on the **Price** and **Price History** cells (see below)

**Stock Reliability** (Historical Supply Pattern)

- `High` — Listed in ≥80% of all historical runs (typically always available)
- `Medium` — Listed in 40-79% of runs (intermittent availability)
- `Low` — Listed in <40% of runs (rarely available)
- `Low` reliability is never treated as fully healthy supply on the dealer page; without extra fire triggers it still remains a `⚠️` warning state rather than `❌` low risk
- **Calculated across entire history**, not just recent weeks
- Example: A species IN stock now but only appeared in 3 of 10 historical weeks = `Low` reliability
- When a species is only newly observed late in the dataset, reliability still stays supply-first but recommendation text may flag the conclusion as limited-history / low-confidence

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

**Price** (Value + Trend)

- Shows current (or last-seen) price plus direction (e.g., `£30.00 ↑`)
- `↑` — Prices increasing
- `→` — Stable pricing
- `↓` — Prices softening
- **Influence:** Informational only; does not affect risk classification (supply and demand signals take precedence)
- **ℹ️ icon** — appears when the listing recently changed its displayed size (confirmed or ambiguous transition); hover or tap for an explanation of the size change and its effect on price interpretation

**Price History** (Trend Visualization)

- Unicode sparkline showing last 8 weeks of pricing (▁▂▃▄▅▆▇█)
- Each character represents one week (left = oldest, right = most recent)
- Height indicates relative price within the period
- When species is OUT of stock, last known price is carried forward (prices persist even when not actively sold)
- Shows pricing stability or volatility at a glance
- Example: `▁▂▃▄▅▆▇█` shows steady price increases over 8 weeks
- `-` — price history is not shown when a size transition is ambiguous or two sizes are simultaneously active (price continuity cannot be guaranteed)
- **ℹ️ icon** — same as the Price cell; indicates price continuity may be partly affected by a recent size change

**Wishlist** (Count · Demand Tier · Momentum)

- Shows `count tier momentum` (e.g., `57 🔥 →`) — the raw wishlist count, relative demand tier, and momentum signal
- **Count** — raw wishlist count (higher = more buyer interest); table sorts by count descending within each risk group
- **Tier** (`🔥`/`⚠️`/`❌`) — relative ranking within the current run; for **OUT-of-stock** species carries forward from most recent IN-stock run (up to 5 runs back)
- **Momentum** (`↑`/`→`/`↓`) — meaningful change between observations (±5 threshold); bounded carryover for OUT species (up to 3 runs back); returns `→` when no comparable value found
- Adds demand urgency beside the supply columns; see the methodology section for the full dealer escalation rules.

**Wishlist History** (Trend Visualization)

- Unicode sparkline showing last 8 weeks of wishlist counts (▁▂▃▄▅▆▇█)
- Each character represents one week (left = oldest, right = most recent)
- Height indicates relative wishlist interest within the period
- When species is OUT of stock, last known wishlist count is carried forward (interest persists)
- Shows demand trajectory and momentum at a glance
- Example: `▁▂▄▆█` shows accelerating interest over 5 weeks
- `-` — wishlist history is not shown when a size transition is ambiguous or two sizes are simultaneously active (momentum continuity cannot be guaranteed)

**Stock Availability** (Supply Pattern Visualization)

- Binary sparkline showing last 8 weeks of stock status (█ = IN, space = OUT)
- Each position represents one week (left = oldest, right = most recent)
- `█` indicates species was IN stock that week
- Space indicates species was OUT of stock that week
- Visualizes the Stock Reliability metric and supply patterns at a glance
- Examples:
  - `████████` — Always available (high reliability)
  - `█  █  █ ` — Intermittent supply (medium/low reliability)
  - `█       ` — Disappeared from stock (low reliability)

**Dealer Risk** (Supply Signal)

- `🔥` — High risk of lost sales (supply constrained)
- `⚠️` — Manage carefully
- `❌` — No urgency; reserved for healthy high-reliability supply

**Dealer Recommendation** (Final Assessment)

- Combines **Stock Reliability + Restock Speed + Wishlist**
- Final label shown in the table after the row's supply and demand columns are considered together.
- Low reliability on its own is already enough to keep the row out of `❌ Low Risk`; extra fire triggers decide whether it escalates from `⚠️` to `🔥`
- See the methodology section above for the detailed dealer decision rules and rule trace.

---

{{ dealer_examples }}

</details>

