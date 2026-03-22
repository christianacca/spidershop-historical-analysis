
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
- Runs before a species is first observed are **ambiguous** and do not count as breeder scarcity evidence
- **Key Difference from Dealer Matrix:** Breeder OOS Runs measures current scarcity window (forward-looking opportunity), while Dealer Avg OOS Duration measures historical supply reliability (backward-looking risk assessment)

**Stock Pattern** (Primary Signal)

- `Always` — Normal availability or a single short-term sell-out (noise)
- `Emerging` — Missing for multiple consecutive runs (early scarcity)
- `Sustained` — Missing for many runs (strong breeding signal)
- `Cyclical` — Repeated disappear / reappear pattern (batch supply)
- `Newly Observed` — Currently in stock, but only observed in the latest 1-2 runs; limited history means pre-first-seen absence is ambiguous
- This is the **foundation** of all recommendations — modifiers can only refine, not override

**Price** (Value + Trend)

- Shows current (or last-seen) price plus direction (e.g., `£30.00 ↑`)
- `↑` — Price rising vs last observed price
- `→` — Price stable
- `↓` — Price falling
- **Influence:** Can escalate `Emerging` patterns to 🔥 when rising (strong confirmation of demand)
- Does not affect `Sustained` signals (already high-confidence) or downgrade any patterns

**Price History** (Trend Visualization)

- Unicode sparkline showing last 8 weeks of pricing (▁▂▃▄▅▆▇█)
- Each character represents one week (left = oldest, right = most recent)
- Height indicates relative price within the period
- When species is OUT of stock, last known price is carried forward (prices persist even when not actively sold)
- Shows pricing stability or volatility at a glance
- Example: `▁▂▃▄▅▆▇█` shows steady price increases over 8 weeks

**Wishlist** (Count · Demand Tier · Momentum)

- Shows `count tier momentum` (e.g., `57 🔥 →`) — the raw wishlist count, relative demand tier, and momentum signal
- **Count** — raw wishlist count (higher = more buyer interest); table sorts by count descending within each signal group
- **Tier** (`🔥`/`⚠️`/`❌`) — relative ranking within the current run (not absolute thresholds); for **OUT-of-stock** species carries forward from most recent IN-stock run (up to 5 runs back)
- **Momentum** (`↑`/`→`/`↓`) — meaningful change between current and previous IN-stock observations (±5 threshold); uses bounded carryover for OUT species (up to 3 runs back); returns `→` when no comparable value found
- **Influence:** Tier can elevate `Emerging` patterns to 🔥 when combined with rising momentum; can prevent `Always` patterns from being dismissed when demand is high; never overrides `Sustained` scarcity signals

**Wishlist History** (Trend Visualization)

- Unicode sparkline showing last 8 weeks of wishlist counts (▁▂▃▄▅▆▇█)
- Each character represents one week (left = oldest, right = most recent)
- Height indicates relative wishlist interest within the period
- When species is OUT of stock, last known wishlist count is carried forward (interest persists)
- Shows demand trajectory and momentum at a glance
- Example: `▁▂▄▆█` shows accelerating interest over 5 weeks

**Signal**

- `🔥` — Strong breeding opportunity signal
- `⚠️` — Monitor closely; opportunity may be forming
- `❌` — Oversupplied or no meaningful scarcity
- `Newly Observed` stays in the `⚠️` bucket until more runs exist; it is a limited-history hold state, not confirmed scarcity or abundance

**Recommendation** (Final Assessment)

- Combines **Stock Pattern + Price + Wishlist**
- **Hierarchy:** Stock Pattern is primary (~70% influence), Price and Wishlist together provide ~30% refinement
- Modifiers can escalate signals but never override the base pattern category
- Example: `Sustained` scarcity cannot be downgraded by falling prices
- Example: `Always` available cannot reach 🔥 regardless of wishlist interest
- Example: `Newly Observed` remains ⚠️ while history is sparse, even if current demand is strong
- Designed to be conservative to avoid reacting to short-term noise

---

{{ breeder_examples }}

---

### 🏪 Dealer Supply Risk Matrix — Legend

**Stock Reliability** (Historical Supply Pattern)

- `High` — Listed in ≥80% of all historical runs (typically always available)
- `Medium` — Listed in 40-79% of runs (intermittent availability)
- `Low` — Listed in <40% of runs (rarely available)
- This is the **foundation** of all dealer risk assessments — demand modifiers refine but cannot override supply constraints
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
- **Influence:** Combines with Stock Reliability to define supply stability; slow restock amplifies low reliability risks

**Price** (Value + Trend)

- Shows current (or last-seen) price plus direction (e.g., `£30.00 ↑`)
- `↑` — Prices increasing
- `→` — Stable pricing
- `↓` — Prices softening
- **Influence:** Informational only; does not affect risk classification (supply and demand signals take precedence)

**Price History** (Trend Visualization)

- Unicode sparkline showing last 8 weeks of pricing (▁▂▃▄▅▆▇█)
- Each character represents one week (left = oldest, right = most recent)
- Height indicates relative price within the period
- When species is OUT of stock, last known price is carried forward (prices persist even when not actively sold)
- Shows pricing stability or volatility at a glance
- Example: `▁▂▃▄▅▆▇█` shows steady price increases over 8 weeks

**Wishlist** (Count · Demand Tier · Momentum)

- Shows `count tier momentum` (e.g., `57 🔥 →`) — the raw wishlist count, relative demand tier, and momentum signal
- **Count** — raw wishlist count (higher = more buyer interest); table sorts by count descending within each risk group
- **Tier** (`🔥`/`⚠️`/`❌`) — relative ranking within the current run; for **OUT-of-stock** species carries forward from most recent IN-stock run (up to 5 runs back)
- **Momentum** (`↑`/`→`/`↓`) — meaningful change between observations (±5 threshold); bounded carryover for OUT species (up to 3 runs back); returns `→` when no comparable value found
- **Influence:** Tier escalates `Low` or `Medium` reliability to 🔥 when combined with poor supply stability; rising momentum can escalate `Medium` reliability + high tier to 🔥; falling momentum reinforces `High` reliability ❌

**Wishlist History** (Trend Visualization)

- Unicode sparkline showing last 8 weeks of wishlist counts (▁▂▃▄▅▆▇█)
- Each character represents one week (left = oldest, right = most recent)
- Height indicates relative wishlist interest within the period
- When species is OUT of stock, last known wishlist count is carried forward (interest persists)
- Shows demand trajectory and momentum at a glance
- Example: `▁▂▄▆█` shows accelerating interest over 5 weeks

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
- `❌` — No urgency; supply is healthy

**Dealer Recommendation** (Final Assessment)

- Combines **Stock Reliability + Restock Speed + Wishlist**
- **Hierarchy:** Supply metrics (Reliability + Restock Speed) are primary (~75% influence), demand signals provide ~25% refinement
- Demand modifiers escalate urgency for supply-constrained species but cannot override healthy supply
- Example: `Low` reliability + `Slow` restock = 🔥 regardless of wishlist interest
- Example: `High` reliability cannot reach 🔥 even with surging demand (well-supplied)
- Sparse-history species may carry a limited-history qualifier in the recommendation or drivers, but this does not create a separate dealer taxonomy
- Designed to prevent stockouts while avoiding panic buying of well-stocked items

---

{{ dealer_examples }}

</details>

