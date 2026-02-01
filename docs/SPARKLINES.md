# Sparkline Specification

This document defines how sparklines are generated and displayed in the spidershop analysis system:
- **Unicode sparklines** for markdown analysis outputs (breeder/dealer matrices)
- **SVG sparklines** for the interactive HTML website

## Overview

Sparklines provide compact visual trend indicators showing how a single species' metrics (price, wishlist count, stock availability) have changed over recent weeks.

## Purpose

- **Price History**: Shows if a species' price is trending up, down, or stable
- **Wishlist History**: Shows if buyer interest is increasing, decreasing, or stable
- **Stock History**: Shows when species was IN or OUT of stock
- **Quick visual scanning**: Enables rapid pattern recognition across many species

## Data Collection

- **Temporal window**: Last 8 weekly scrapes
- **Display order**: Chronological (oldest on left, newest on right)
- **Fields tracked**: `price_gbp`, `wishlist_count`, stock availability

---

## Part 1: Unicode Sparklines (Markdown Output)

### Character Set

Eight levels of block characters, from shortest to tallest:
```
▁ ▂ ▃ ▄ ▅ ▆ ▇ █
```

Space character (` `) can represent gaps (used in stock sparklines only).

### Bar Height Scaling

**Each sparkline is self-contained for ONE species across time.**

#### The Rule
- **Shortest bar** (▁) = lowest value that species had in the last 8 weeks
- **Tallest bar** (█) = highest value that species had in the last 8 weeks  
- Everything in between is scaled proportionally (linear normalization between min/max)

#### Important: NOT Compared Across Species
Bar heights are **NOT** relative to other species in the same week. Each sparkline scales independently to its own historical range.

#### Example

**Spider A - Price History:**
```
Week 1: £10  → ▁  (Spider A's minimum)
Week 2: £12  → ▃
Week 3: £15  → ▆
Week 4: £20  → █  (Spider A's maximum)
```

**Spider B - Price History:**
```
Week 1: £100 → ▁  (Spider B's minimum, but 10x higher in absolute terms)
Week 2: £120 → ▃
Week 3: £150 → ▆
Week 4: £200 → █  (Spider B's maximum)
```

Both sparklines look identical (`▁▃▆█`) even though Spider B costs 10x more.

**What This Means:**
- ✅ You **can** see if a spider's price is trending up/down relative to its own history
- ❌ You **cannot** compare bar heights between different species' sparklines
- 📊 Each sparkline shows **relative change over time**, not absolute values

### Behavioral Rules

#### 1. Start Point - Skip Leading Gaps

**Rule**: Sparklines only begin when the species first appears in history.

**Why**: We don't show empty weeks before a species was first listed.

**Example**:
```
Run:        1    2    3    4    5    6    7    8
Price:      -    -    -    £12  £13  £14  £15  £16
Sparkline:                 ▁    ▃    ▅    ▆    █
```
The sparkline starts at run 4 (first appearance), showing only 5 bars instead of 8.

#### 2. Price & Wishlist: Carry-Forward (No Mid-Sparkline Gaps)

**Rule**: Once started, price and wishlist sparklines have no gaps. When a species goes OUT of stock, the last known value is carried forward.

**Why**: Prices and wishlist interest don't disappear when stock runs out. This reflects the real-world reality that the price hasn't changed, stock is just unavailable.

**Example**:
```
Run:        1    2    3    4    5    6    7    8
Price:      -    -    £12  £12  OUT  OUT  £15  £15
Actual:                £12  £12   -    -   £15  £15
Carried:               £12  £12  £12  £12  £15  £15
Sparkline:            ▃    ▃    ▃    ▃    █    █
```

**Visual Effect**: OUT periods create flat sections in the sparkline, showing "last known state" rather than gaps.

#### 3. Stock: Visual Gaps

**Rule**: Stock availability sparklines show gaps (spaces) for OUT-of-stock periods.

**Example**:
```
Run:        1    2    3    4    5    6    7
Status:     IN   IN   OUT  OUT  IN   IN   OUT
Display:    ██  █ █  ·
```

**Why**: Stock status is binary (IN or OUT). There's no "carry forward" for availability.

#### 4. Edge Cases

**No data at all**: 
```
Display: "-"
```

**Single valid value**:
```
Price:      £12
Display:    "▄"  (mid-height bar)
```

**All values identical (flat line)**:
```
Price:      £12  £12  £12  £12
Display:    "▄▄▄▄"  (all mid-height, since min = max)
```

**Two distinct values only**:
```
Price:      £10  £10  £20  £20
Display:    "▁▁██"  (min gets shortest, max gets tallest)
```

### Example Scenarios

**Steady Increase:**
```
Run:        1    2    3    4    5    6    7    8
Price:      £10  £12  £14  £16  £18  £20  £22  £24
Sparkline:  ▁    ▂    ▃    ▄    ▅    ▆    ▇    █
```

**Volatility with OUT Period:**
```
Run:        1    2    3    4    5    6    7    8
Wishlist:   -    5    7    OUT  OUT  OUT  12   15
Carried:         5    7    7    7    7    12   15
Sparkline:       ▁    ▃    ▃    ▃    ▃    ▇    █
```

**Price Drop with Recovery:**
```
Run:        1    2    3    4    5    6    7    8
Price:      £20  £18  £15  £15  £16  £18  £19  £20
Sparkline:  █    ▇    ▁    ▁    ▃    ▇    ▇    █
```

---

## Part 2: SVG Sparklines (HTML Website)

SVG sparklines enhance the Unicode text sparklines with:
- **Interactive tooltips** showing exact values on hover
- **Color coding** to indicate trends (up/down/neutral)
- **Square brackets** in tooltips mark carried-forward values
- Better visual clarity for web display

### Conversion Process

Each Unicode sparkline character becomes an SVG bar element. The conversion preserves the visual representation while adding interactivity.

### SVG Bar Height Calculation

SVG sparklines work from **the same historical data** as Unicode sparklines, so both representations are generated from identical data sources.

#### Price & Wishlist: Zero-Based Proportional Heights

Bar heights are calculated using **zero-based normalization** from actual numeric values:

```
normalized = value / max_value
bar_height = (0.1 + normalized × 0.9) × 20px
```

**Example:** Wishlist counts of 120 and 126:
- Max value: 126
- Bar 1: 120/126 = 95.2% → (0.1 + 0.952 × 0.9) × 20 = **19.1px**
- Bar 2: 126/126 = 100% → (0.1 + 1.0 × 0.9) × 20 = **20.0px**

**Result:** Bars look appropriately similar (only 5% difference in height), matching the 5% difference in values.

**Key features:**
- **Zero-based**: All values normalized relative to 0 (not to min/max range)
- **10% minimum**: Ensures all bars are visible (no invisible bars)
- **90% proportional**: Preserves relative differences accurately

**Critical difference from Unicode:** Unicode sparklines use **min/max normalization** (shortest bar = min value, tallest = max value). SVG uses **zero-based normalization** for more accurate proportional representation.

**Fail-fast validation:** If values are missing or invalid for price/wishlist sparklines, conversion fails with an assertion error. This ensures data integrity - SVG conversion only happens when we have valid historical data.

#### Stock: Unicode Character Heights

Stock sparklines use Unicode character positions since there are no numeric values (just IN/OUT status):

```
▁ = 1/8 × 20px = 2.5px
▂ = 2/8 × 20px = 5.0px
▃ = 3/8 × 20px = 7.5px
▄ = 4/8 × 20px = 10.0px
▅ = 5/8 × 20px = 12.5px
▆ = 6/8 × 20px = 15.0px
▇ = 7/8 × 20px = 17.5px
█ = 8/8 × 20px = 20.0px
```

(In practice, stock sparklines typically only use `█` for IN and spaces for OUT gaps)

### Gap Handling

**Price & Wishlist:** No visual gaps (continuous bars, even during OUT periods)
- Matches Unicode behavior where values carry forward
- Space character in Unicode is ignored during conversion

**Stock:** Visual gaps for OUT periods
- Space character in Unicode = no SVG bar rendered
- Creates true gaps in the visualization

### Color Coding

Colors indicate the overall trend from first to last non-None bar:

**Uptrend** (last > first + 1):
- Color: Green (`#22c55e`)
- Example: `▁▃▅▇█` (rising prices)

**Downtrend** (last < first - 1):
- Color: Red (`#ef4444`)
- Example: `█▇▅▃▁` (falling prices)

**Neutral** (last ≈ first, or all carried-forward after first):
- Color: Blue (`#3b82f6`)
- Example: `▄▄▄▄` (flat line)

**Stock sparklines:** Always green (for IN bars)

**Special case:** If all values after the first are carried-forward (detected via `is_carried_forward` flags), the sparkline is treated as neutral (blue) regardless of Unicode character heights, since no actual change occurred.

### Tooltip Content

**Price sparklines:**
- Actual: `£15.00`
- Carried-forward: `[£15.00]` (square brackets)

**Wishlist sparklines:**
- Actual: `5 wishlists`
- Carried-forward: `[5 wishlists]`

**Stock sparklines:**
- IN: `IN`
- OUT: No bar (gap)

Square brackets indicate the value was carried forward from a previous week when the species was OUT of stock.

### Visual Effects

- **Opacity gradient**: Bars get slightly more opaque from left to right (0.7 to 1.0)
- **Hover interaction**: Tooltips appear on mouseover

### SVG Output Specification

- **Bar width**: 8px
- **Bar spacing**: 10px
- **SVG height**: 20px
- **SVG width**: `bar_count × 10px`
- **Position**: Bars positioned from left to right, bottom-aligned

---

## Implementation References

- **Unicode generation**: `generate_sparkline()` in [sparkline_helpers.py](../src/sparkline_helpers.py)
- **Carry-forward logic**: `extract_historical_values_with_carryforward()` in [sparkline_helpers.py](../src/sparkline_helpers.py)
- **SVG conversion**: `convert_sparkline_to_svg()` in [generate_website.py](../src/website/generate_website.py)
- **Unicode library**: `sparklines` Python package
