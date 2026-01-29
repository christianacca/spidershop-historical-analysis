# Sparkline Specification

This document defines how Unicode sparklines are generated for the markdown analysis outputs (breeder and dealer matrices).

## Overview

Sparklines provide compact visual trend indicators using Unicode block characters (`▁▂▃▄▅▆▇█`). They show how a single species' metrics (price or wishlist count) have changed over recent weeks.

## Purpose

- **Price History sparkline**: Shows if a species' price is trending up, down, or stable over time
- **Wishlist History sparkline**: Shows if buyer interest is increasing, decreasing, or stable
- **Quick visual scanning**: Enables rapid pattern recognition across many species

## Data Collection

- **Temporal window**: Last 8 weekly scrapes
- **Display order**: Chronological (oldest on left, newest on right)
- **Fields tracked**: 
  - `price_gbp` (price in GBP)
  - `wishlist_count` (number of wishlists)

## Visual Representation

### Character Set
Eight levels of block characters, from shortest to tallest:
```
▁ ▂ ▃ ▄ ▅ ▆ ▇ █
```

### Bar Height Calculation

**Each sparkline is self-contained for ONE species across time.**

#### The Rule
- The **shortest bar** (▁) = the **lowest value** that species had in the last 8 weeks
- The **tallest bar** (█) = the **highest value** that species had in the last 8 weeks  
- Everything in between is scaled proportionally between min and max

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

Both sparklines look identical (`▁▃▆█`) even though Spider B costs 10x more, because each sparkline scales to its own min/max range.

#### What This Means
- ✅ You **can** see if a spider's price is trending up/down relative to its own history
- ❌ You **cannot** compare bar heights between different species' sparklines
- 📊 Each sparkline shows **relative change over time**, not absolute values

## Behavioral Rules

### 1. Start Point - Skip Leading Gaps

**Rule**: Sparklines only begin when the species first appears in history.

**Why**: We don't show empty weeks before a species was first listed.

**Example**:
```
Run:        1    2    3    4    5    6    7    8
Price:      -    -    -    £12  £13  £14  £15  £16
Sparkline:                 ▁    ▃    ▅    ▆    █
```
The sparkline starts at run 4 (first appearance), showing only 5 bars instead of 8.

### 2. Carry-Forward - No Mid-Sparkline Gaps

**Rule**: Once started, sparklines have no gaps. When a species goes OUT of stock, the last known value is carried forward.

**Why**: Prices and wishlist interest don't disappear when stock runs out. This reflects the real-world reality that the price hasn't changed, stock is just unavailable.

**Example**:
```
Run:        1    2    3    4    5    6    7    8
Price:      -    -    £12  £12  OUT  OUT  £15  £15
Actual:                £12  £12   -    -   £15  £15
Carried:               £12  £12  £12  £12  £15  £15
Sparkline:            ▃    ▃    ▃    ▃    █    █
```

The sparkline shows a plateau during OUT periods (runs 5-6), then rises when restocked at £15.

**Visual Effect**: OUT periods create flat sections in the sparkline, showing "last known state" rather than gaps.

### 3. Edge Cases

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

## Complete Example Scenarios

### Scenario 1: Steady Increase
```
Run:        1    2    3    4    5    6    7    8
Price:      £10  £12  £14  £16  £18  £20  £22  £24
Sparkline:  ▁    ▂    ▃    ▄    ▅    ▆    ▇    █
```
Interpretation: Clear upward price trend

### Scenario 2: Volatility with OUT Period
```
Run:        1    2    3    4    5    6    7    8
Wishlist:   -    5    7    OUT  OUT  OUT  12   15
Carried:         5    7    7    7    7    12   15
Sparkline:       ▁    ▃    ▃    ▃    ▃    ▇    █
```
Interpretation: Interest growing despite stock unavailability (plateau during OUT, surge on restock)

### Scenario 3: Price Drop with Quick Recovery
```
Run:        1    2    3    4    5    6    7    8
Price:      £20  £18  £15  £15  £16  £18  £19  £20
Sparkline:  █    ▇    ▁    ▁    ▃    ▇    ▇    █
```
Interpretation: Temporary price reduction, returning to original level

## Implementation Details

- **Library used**: `sparklines` Python package
- **Scaling algorithm**: Linear normalization between min/max
- **Function**: `generate_sparkline()` in [sparkline_helpers.py](../src/sparkline_helpers.py)
- **Carry-forward**: `extract_historical_values_with_carryforward()` handles OUT-of-stock logic

## Future Considerations

When converting to HTML/SVG sparklines:
- Distinguish visually between "actual data point" vs "carried forward" value
- Add tooltips showing exact values on hover
- Potentially show gaps differently (e.g., dotted lines during OUT periods)
- Consider adding Y-axis scale indicators for absolute value context
