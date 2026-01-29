# SVG Sparkline Specification

This document defines how Unicode sparklines are converted to interactive SVG graphics for the website.

## Overview

SVG sparklines enhance the Unicode text sparklines with:
- **Tooltips** showing exact values on hover
- **Color coding** to show trends (up/down/neutral)
- **Square brackets** in tooltips to mark carried-forward values
- Better visual clarity for web display

## What Gets Converted

Each Unicode sparkline character becomes an SVG bar:

```
▁ ▂ ▃ ▄ ▅ ▆ ▇ █
↓  ↓  ↓  ↓  ↓  ↓  ↓  ↓
Short bars → gradually taller → full height bars
```

Space character (` `) = no bar (creates visual gap)

## Core Rules

### Rule 1: Price & Wishlist Sparklines Show NO Gaps

Price and wishlist sparklines are **continuous** (no visual gaps), even when species is OUT of stock. This matches the Unicode behavior where values carry forward.

**Example:**
```
Week:       1     2     3     4     5     6     7
Price:      £12   £15   OUT   OUT   OUT   £18   £20
Display:    ▃     ▆     ▆     ▆     ▆     ▇     █   (continuous bars)
Tooltips:   £12   £15   [£15] [£15] [£15] £18   £20
```

**Why:** Prices don't disappear when stock runs out. The last known price is still the price.

**Square brackets** in tooltips indicate carried-forward (old) data: `[£15]` vs `£15`

### Rule 2: Stock Sparklines Show Gaps

Stock sparklines have **visual gaps** for OUT-of-stock periods.

**Example:**
```
Week:       1    2    3    4    5    6    7
Status:     IN   IN   OUT  OUT  IN   IN   OUT
Display:    █    █    ·    ·    █    █    ·    (· = gap, no bar)
```

**Why:** Stock status is binary (IN or OUT). There's no "carry forward" for availability.

## Tooltip Content Specification

### Format by Metric Type

**Price (`metric_type="price"`):**
- Actual value: `"£X.XX"` (2 decimal places)
- Carried-forward: `"[£X.XX]"` (square brackets)

**Wishlist (`metric_type="wishlist"`):**
- Actual vaFormat

**Price sparklines:**
- Actual: `£15.00`
- Carried forward: `[£15.00]` ← square brackets!

**Wishlist sparklines:**
- Actual: `5 wishlists`
- Carried forward: `[5 wishlists]`

**Stock sparklines:**
- IN: Show "IN"
- OUT: No bar (gap)

### Current Bug

Right now, carried-forward tooltips show placeholders like `"Week 3"` instead of the actual value with square brackets. This needs fixing.olor: Green (`#22c55e`)
- Example: `▁▃▅▇█` (rising prices)

**Downtrend** (last < first):
- Color: Red (`#ef4444`)
- Example: `█▇▅▃▁` (falling prices)

**Neutral** (last = first OR single bar):
- Color: Blue (`#3b82f6`)
- Example: `▄▄▄▄` (flat line)

Sparklines use color to show trends at a glance:

**Green** = Uptrend (value increased from start to end)  
**Red** = Downtrend (value decreased)  
**Blue** = Neutral (no change, or single data point)

**Stock sparklines** are always green (for IN bars
Carried-forward bars could be visually distinct:
- **Option 1**: Reduced opacity (e.g., 0.5 vs 1.0)
- **Option 2**: Dashed/dotted pattern
- **Option 3**: Different fill color (lighter shade)

Example:
```html
<!-- Actual value -->
<rect fill="#22c55e" opacity="1.0" ...>

<!-- Carried-forward value -->
<rect fill="#22c55e" opacity="0.5" ...>
```

## Bar Positioning

**X position**: `bar_index × 10` pixels  
**Y position**: `svg_height - pixel_height` (SVG coordinates: origin at top-left)

BarFuture Enhancements

**Visual distinction for carried-forward bars:**
- Could use lighter color or reduced opacity
- Would make it easier to spot when data is old vs current
- Currently all bars look identica
```
Input:    [£10, £12, OUT, OUT, £15]
Unicode:  ▁▄▄▄█
Expected: 5 continuous bars, tooltips: "£10", "£12", "[£12]", "[£12]", "£15"
Color:    Green (uptrend: £10 → £15)
```

### Scenario 2: Flat Price During OUT Period
```
Input:    [£20, £20, OUT, OUT, OUT, £20]
Unicode:  ▄▄▄▄▄▄
Expected: 6 continuous bars, tooltips: "£20", "£20", "[£20]", "[£20]", "[£20]", "£20"
Color:    Blue (neutral: £20 → £20)
```

### Scenario 3: Stock Availability with Gaps
```
Input:    [IN, IN, OUT, OUT, IN]
Unicode:  ██  █
Expected: 5 positions, bars only at 1,2,5. Visual gaps at positions 3,4
Tooltips: "IN", "IN", (no bar), (no bar), "IN"
Color:    Green (always for stock)
```

## References

- Unicode sparkline spec: [SPARKLINES.md](./SPARKLINES.md)
- Implementation: [generate_website.py](../src/generate_website.py) (`convert_sparkline_to_svg()`)
- Data extraction: [sparkline_helpers.py](../src/sparkline_helpers.py)
Known Issues

**🐛 Tooltips show "Week 3" instead of "[£15.00]"**
- Carried-forward values need square bracket notation
- Currently using placeholder text

**🐛 Carried-forward bars look identical to actual data**
- No visual way to tell old data from current data
- Could use opacity or color difference

**🐛 Color coding might be incorrect for flat lines**
- Flat lines from carry-forward should be blue (neutral)
- May be showing gray instead Examples

**Price rising with OUT period:**
```
Weeks:    1     2     3     4     5
Price:    £10   £12   OUT   OUT   £15
Bars:     ▁     ▄     ▄     ▄     █     (continuous)
Tips:     £10   £12   [£12] [£12] £15
Color:    Green (uptrend)
```

**Flat price during OUT:**
```
Weeks:    1     2     3     4     5
Price:    £20   £20   OUT   OUT   £20
Bars:     ▄     ▄     ▄     ▄     ▄     (continuous)
Tips:     £20   £20   [£20] [£20] £20
Color:    Blue (neutral)
```

**Stock with gaps:**
```
Weeks:    1    2    3    4    5
Status:   IN   IN   OUT  OUT  IN
Bars:     █    █    ·    ·    █     (gaps at 3,4)
Tips:     IN   IN   --   --   IN
Color:    Green