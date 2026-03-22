#!/usr/bin/env python3
"""
Generate legend examples dynamically from actual matrix computation logic.

This module defines synthetic test scenarios and computes their results using
the actual breeder_matrix and dealer_matrix functions. The computed results
are then formatted as markdown examples for inclusion in the legend.

This approach ensures examples are always accurate and stay synchronized with
the computation logic automatically.
"""
from scrape.breeder_matrix import build_breeder_opportunity_table
from scrape.dealer_matrix import build_dealer_supply_risk_table
from shared.parsing import format_datetime_smart


def make_row(scrape_datetime, scientific_name, size_cm, price_gbp, wishlist_count="0"):
    """Create a history row for synthetic test scenarios.
    
    Args:
        scrape_datetime: ISO format datetime string (e.g., "2025-01-01")
        scientific_name: Scientific name of the species
        size_cm: Size in cm as string
        price_gbp: Price in GBP as string
        wishlist_count: Wishlist count as string (default "0")
    
    Returns:
        Dictionary matching the CSV schema for history rows
    """
    return {
        "scrape_datetime": scrape_datetime,
        "scientific_name": scientific_name,
        "common_name": f"Common name for {scientific_name}",
        "size_cm": size_cm,
        "price_gbp": price_gbp,
        "wishlist_count": wishlist_count,
        "page_url": f"https://example.com/product/{scientific_name.replace(' ', '-')}",
    }


def format_scenario_table(history_rows, target_species=None):
    """Format history data as a markdown table for display."""
    # Group by date
    by_date = {}
    for row in history_rows:
        date = row["scrape_datetime"]
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(row)
    
    # Sort dates
    dates = sorted(by_date.keys())
    
    # Format all dates smartly (date-only unless collision)
    formatted_dates = format_datetime_smart(dates)
    date_to_formatted = dict(zip(dates, formatted_dates))
    
    # Find target species rows
    target_rows = {}
    for date in dates:
        found = False
        for row in by_date[date]:
            if target_species is None or row["scientific_name"] == target_species:
                target_rows[date] = row
                found = True
                break
        if not found and target_species:
            target_rows[date] = None
    
    # Format as table
    lines = []
    lines.append("| Date | Listed? | Price | Wishlist Count |")
    lines.append("|------|---------|-------|----------------|")
    
    for date in dates:
        formatted_date = date_to_formatted[date]
        
        if date in target_rows:
            row = target_rows[date]
            if row:
                listed = "✅ Yes"
                price = f"£{float(row['price_gbp']):.2f}"
                wishlist = row['wishlist_count']
            else:
                listed = "❌ No"
                price = "-"
                wishlist = "-"
        else:
            continue
            
        lines.append(f"| {formatted_date} | {listed} | {price} | {wishlist} |")
    
    return "\n".join(lines)


def _get_table_entry(table: list, species: str) -> dict:
    """Get table entry for a specific species.
    
    Args:
        table: Table with 'Species' column
        species: Species name to find
        
    Returns:
        Dictionary of the matching row
    """
    return [r for r in table if r["Species"] == species][0]


def generate_breeder_example_1():
    """Example 1: Sustained Scarcity (Strong Opportunity)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "10"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "5"),
        make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
        make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "5"),
        make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "5"),
        make_row("2025-01-29", "Grammostola pulchra", "2.0", "40.00", "5"),
    ]
    
    table = build_breeder_opportunity_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    data_table = format_scenario_table(history, "Aphonopelma seemanni")
    
    return f"""#### Example 1: Sustained Scarcity (Strong Opportunity)
**Scenario:** A species that has been unavailable for 4+ consecutive weeks

{data_table}

**Analysis Result:**

- **OOS:** {entry["OOS"]}
- **OOS Runs:** {entry["OOS Runs"]}
- **Stock Pattern:** {entry["Stock Pattern"]}
- **Signal:** {entry["Signal"]}
- **Recommendation:** {entry["Recommendation"]}

**Why:** When a species disappears for 4+ weeks in a row, this indicates persistent market scarcity. This is a strong signal for breeders that demand is outpacing supply, making it a good breeding candidate."""


def generate_breeder_example_2():
    """Example 2: Emerging Scarcity with Rising Price."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "5"),
        make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00", "6"),
        make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
        make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "5"),
        make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "5"),
    ]
    
    table = build_breeder_opportunity_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    data_table = format_scenario_table(history, "Aphonopelma seemanni")
    
    return f"""#### Example 2: Emerging Scarcity with Rising Price
**Scenario:** A species recently went out of stock (2-3 weeks) and price increased before disappearing

{data_table}

**Analysis Result:**

- **OOS:** {entry["OOS"]}
- **OOS Runs:** {entry["OOS Runs"]}
- **Stock Pattern:** {entry["Stock Pattern"]}
- **Price:** {entry["Price"]}
- **Signal:** {entry["Signal"]}
- **Recommendation:** {entry["Recommendation"]}

**Why:** The combination of disappearing stock AND rising prices suggests growing market demand. Even though the scarcity is only emerging (2-3 weeks), the price increase confirms this as a genuine opportunity rather than just temporary fluctuation."""


def generate_breeder_example_3():
    """Example 3: Cyclical Pattern (Batch Supply)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "5"),
        make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "5"),
        make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "26.00", "6"),
        make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "5"),
    ]
    
    table = build_breeder_opportunity_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    data_table = format_scenario_table(history, "Aphonopelma seemanni")
    
    return f"""#### Example 3: Cyclical Pattern (Batch Supply)
**Scenario:** A species that repeatedly disappears and reappears

{data_table}

**Analysis Result:**

- **OOS:** {entry["OOS"]}
- **Stock Pattern:** {entry["Stock Pattern"]}
- **Signal:** {entry["Signal"]}
- **Recommendation:** {entry["Recommendation"]}

**Why:** When species flap between available and unavailable, this suggests suppliers are breeding in batches. It's worth monitoring but not necessarily an urgent opportunity since supply returns regularly."""


def generate_breeder_example_4():
    """Example 4: Always Available (Oversupplied)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "3"),
        make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "3"),
        make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "4"),
    ]
    
    table = build_breeder_opportunity_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    data_table = format_scenario_table(history, "Aphonopelma seemanni")
    
    return f"""#### Example 4: Always Available (Oversupplied)
**Scenario:** A species consistently in stock at stable prices with low interest

{data_table}

**Analysis Result:**

- **OOS:** {entry["OOS"]}
- **OOS Runs:** {entry["OOS Runs"]}
- **Stock Pattern:** {entry["Stock Pattern"]}
- **Wishlist:** {entry["Wishlist"]}
- **Signal:** {entry["Signal"]}
- **Recommendation:** {entry["Recommendation"]}

**Why:** Continuous availability combined with stable prices and low wishlist interest indicates the market has plenty of supply. Not a good breeding opportunity."""


def generate_breeder_example_5():
    """Example 5: Emerging Opportunity with High Demand."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00", "1"),
        make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "15"),
        make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-08", "Brachypelma hamorii", "1.5", "30.00", "1"),
        make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-15", "Brachypelma hamorii", "1.5", "30.00", "1"),
        make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-22", "Brachypelma hamorii", "1.5", "30.00", "1"),
    ]
    
    table = build_breeder_opportunity_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    data_table = format_scenario_table(history, "Aphonopelma seemanni")
    
    return f"""#### Example 5: Emerging Opportunity with High Demand
**Scenario:** A species went out of stock for 2 weeks, but shows significant wishlist interest surge

{data_table}

**Analysis Result:**

- **OOS:** {entry["OOS"]}
- **OOS Runs:** {entry["OOS Runs"]}
- **Stock Pattern:** {entry["Stock Pattern"]}
- **Wishlist:** {entry["Wishlist"]} (carried from last seen)
- **Signal:** {entry["Signal"]}
- **Recommendation:** {entry["Recommendation"]}

**Why:** The dramatic increase in wishlist count (+10) before the species went out of stock, combined with the emerging scarcity pattern, indicates rapidly growing demand. The momentum signal escalates this from a "watch" to a strong opportunity."""


def generate_breeder_example_6():
    """Example 6: Always Available with Falling Interest."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "20"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "15"),
        make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "8"),
        make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "1"),
    ]
    
    table = build_breeder_opportunity_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    data_table = format_scenario_table(history, "Aphonopelma seemanni")
    
    return f"""#### Example 6: Always Available with Falling Interest
**Scenario:** A species remains in stock but wishlist interest is declining

{data_table}

**Analysis Result:**

- **OOS:** {entry["OOS"]}
- **OOS Runs:** {entry["OOS Runs"]}
- **Stock Pattern:** {entry["Stock Pattern"]}
- **Wishlist:** {entry["Wishlist"]}
- **Signal:** {entry["Signal"]}
- **Recommendation:** {entry["Recommendation"]}

**Why:** Continuous availability combined with declining wishlist interest suggests the market is saturated and buyer interest is waning. This is a clear signal to avoid breeding this species."""


def generate_breeder_example_7():
    """Example 7: Currently In Stock but Historically Unreliable (Compare with Dealer View)."""
    history = [
        make_row("2025-01-01", "Cyriocosmus elegans", "0.5", "15.00", "8"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
        # OUT for 4 weeks
        make_row("2025-02-05", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-02-12", "Cyriocosmus elegans", "0.5", "15.00", "12"),
        make_row("2025-02-12", "Grammostola pulchra", "2.0", "40.00", "1"),
        # OUT for 4 weeks
        make_row("2025-03-19", "Cyriocosmus elegans", "0.5", "15.00", "16"),
        make_row("2025-03-19", "Grammostola pulchra", "2.0", "40.00", "1"),
    ]
    
    breeder_table = build_breeder_opportunity_table(history)
    dealer_table = build_dealer_supply_risk_table(history)
    
    breeder_entry = _get_table_entry(breeder_table, "Cyriocosmus elegans")
    dealer_entry = _get_table_entry(dealer_table, "Cyriocosmus elegans")
    
    data_table = format_scenario_table(history, "Cyriocosmus elegans")
    
    return f"""#### Example 7: Understanding OOS Metrics — Breeder vs Dealer Perspective
**Scenario:** A species currently in stock, but with a history of extended unavailability

{data_table}

**Breeder Analysis:**

- **OOS:** {breeder_entry["OOS"]} (currently listed)
- **OOS Runs:** {breeder_entry["OOS Runs"]} (no consecutive scarcity right now)
- **Stock Pattern:** {breeder_entry["Stock Pattern"]}
- **Wishlist:** {breeder_entry["Wishlist"]}
- **Signal:** {breeder_entry["Signal"]}
- **Recommendation:** {breeder_entry["Recommendation"]}

**Dealer Analysis:**

- **Stock Reliability:** {dealer_entry["Stock Reliability"]} (only in stock 3 of 10 weeks = 30%)
- **Avg OOS Duration:** {dealer_entry["Avg OOS Duration"]} runs (when it goes OUT, stays OUT ~4 weeks)
- **Restock Speed:** {dealer_entry["Restock Speed"]}
- **Wishlist:** {dealer_entry["Wishlist"]}
- **Dealer Risk:** {dealer_entry["Dealer Risk"]}
- **Recommendation:** {dealer_entry["Dealer Recommendation"]}

**Why the Different Metrics?**

- **Breeder OOS Runs = 0**: Measures *consecutive* weeks OUT *ending now*. Since it's IN stock now, the counter resets. Breeders focus on *current* scarcity windows — if it's available now, there's no immediate breeding signal.

- **Dealer Avg OOS = 4.0**: Measures *average duration* of OOS events *across all history*. This species disappeared twice (weeks 2-5 and weeks 7-10), averaging 4 weeks per event. Dealers need to know *supply reliability* — even if it's in stock today, the pattern shows it frequently becomes unavailable for extended periods.

**The Key Insight:** This is **low-priority for breeders** (no current scarcity) but **high-priority for dealers** (poor supply reliability means lost sales risk). The metrics answer different questions:
- Breeder: "Should I breed this NOW?" → No, it's currently available
- Dealer: "Is supply reliable?" → No, and when it sells out, it stays out for ~4 weeks

This demonstrates how the same market data yields different but equally valid insights for different stakeholders."""


def generate_breeder_example_8():
    """Example 8: Newly Observed (Limited History Hold State)."""
    history = [
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "9"),
        make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "26.00", "14"),
        make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "1"),
    ]

    table = build_breeder_opportunity_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")

    data_table = format_scenario_table(history, "Aphonopelma seemanni")

    return f"""#### Example 8: Newly Observed (Limited History Hold State)
**Scenario:** A species is currently in stock, but only appears in the latest 2 runs after being absent from all earlier dataset history

{data_table}

**Analysis Result:**

- **OOS:** {entry["OOS"]}
- **OOS Runs:** {entry["OOS Runs"]}
- **Stock Pattern:** {entry["Stock Pattern"]}
- **Wishlist:** {entry["Wishlist"]}
- **Signal:** {entry["Signal"]}
- **Recommendation:** {entry["Recommendation"]}

**Why:** This species is too new in the dataset to treat as reliably available, but there is also not enough evidence to treat earlier absence as true scarcity. `Newly Observed` keeps the row in a limited-history hold state until more runs exist."""


def generate_breeder_examples():
    """Generate all Breeder Matrix examples."""
    examples = [
        generate_breeder_example_1(),
        generate_breeder_example_2(),
        generate_breeder_example_3(),
        generate_breeder_example_4(),
        generate_breeder_example_5(),
        generate_breeder_example_6(),
        generate_breeder_example_7(),
        generate_breeder_example_8(),
    ]
    
    header = """### 📖 Breeder Matrix — Practical Examples

The following examples show how different combinations of signals translate into recommendations. These scenarios are based on actual test cases and represent typical market situations you might encounter.

"""
    
    return header + "\n\n---\n\n".join(examples)


def generate_dealer_examples():
    """Generate all Dealer Matrix examples."""
    examples = [
        generate_dealer_example_1(),
        generate_dealer_example_2(),
        generate_dealer_example_3(),
        generate_dealer_example_4(),
        generate_dealer_example_5(),
        generate_dealer_example_6(),
        generate_dealer_example_7(),
    ]
    
    header = """### 📖 Dealer Matrix — Practical Examples

The following examples show how supply patterns and demand signals combine to assess dealer risk. These scenarios help dealers understand which species require urgent attention and which are well-supplied.

"""
    
    return header + "\n\n---\n\n".join(examples)


def generate_dealer_example_1():
    """Example 1: High Reliability (No Urgency)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-01-29", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-02-05", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-02-12", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-02-19", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        # Skip one week
        make_row("2025-03-05", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-03-12", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        # Add low-wishlist species for pressure calculation
        make_row("2025-03-12", "Grammostola pulchra", "2.0", "40.00", "1"),
    ]
    
    table = build_dealer_supply_risk_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    return f"""#### Example 1: High Reliability (No Urgency)
**Scenario:** A species available in 9 out of 10 weeks with stable demand

**Analysis Result:**

- **Stock Reliability:** {entry["Stock Reliability"]} (9/10 weeks = 90%)
- **Restock Speed:** {entry["Restock Speed"]}
- **Wishlist:** {entry["Wishlist"]}
- **Dealer Risk:** {entry["Dealer Risk"]}
- **Recommendation:** {entry["Dealer Recommendation"]}

**Why:** When a species is almost always available and demand is stable or low, there's no risk of lost sales. Dealers can wait for favorable pricing or focus on more constrained species."""


def generate_dealer_example_2():
    """Example 2: Medium Reliability (Watch and Wait)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        # out week 2
        make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        # out week 4
        make_row("2025-01-29", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        make_row("2025-02-05", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        # out week 7
        make_row("2025-02-19", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        # out week 9
        make_row("2025-03-05", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        # Low-wishlist species for pressure calculation
        make_row("2025-03-05", "Grammostola pulchra", "2.0", "40.00", "1"),
    ]
    
    table = build_dealer_supply_risk_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    return f"""#### Example 2: Medium Reliability (Watch and Wait)
**Scenario:** A species present in 5 out of 10 weeks (50% availability)

**Analysis Result:**

- **Stock Reliability:** {entry["Stock Reliability"]}
- **Dealer Risk:** {entry["Dealer Risk"]}
- **Recommendation:** {entry["Dealer Recommendation"]}

**Why:** Intermittent availability means supply is somewhat unreliable, but not critically constrained. Dealers should buy when good opportunities arise, but don't need to actively seek stock."""


def generate_dealer_example_3():
    """Example 3: Low Reliability + Slow Restock (High Risk)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "5"),
        # out 4 weeks
        make_row("2025-02-05", "Aphonopelma seemanni", "1.0", "26.00", "6"),
        # out 4 weeks
        make_row("2025-03-12", "Aphonopelma seemanni", "1.0", "27.00", "7"),
        # Low-wishlist species for pressure calculation
        make_row("2025-03-12", "Grammostola pulchra", "2.0", "40.00", "1"),
    ]
    
    table = build_dealer_supply_risk_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    return f"""#### Example 3: Low Reliability + Slow Restock (High Risk)
**Scenario:** A species rarely available (3 out of 10 weeks), taking 4+ weeks to restock

**Analysis Result:**

- **Stock Reliability:** {entry["Stock Reliability"]} (<40% availability)
- **Avg OOS Duration:** {entry["Avg OOS Duration"]} runs
- **Restock Speed:** {entry["Restock Speed"]}
- **Dealer Risk:** {entry["Dealer Risk"]}
- **Recommendation:** {entry["Dealer Recommendation"]}

**Why:** When a species is rarely available AND takes a long time to restock, dealers face high risk of lost sales. Even without exceptional demand, the supply constraint alone makes this a priority species to source."""


def generate_dealer_example_4():
    """Example 4: Low Reliability + High Demand (Critical Risk)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "25.00", "50"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-01", "Brachypelma hamorii", "1.5", "30.00", "1"),
        # Out for 5 weeks
        make_row("2025-02-12", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-02-12", "Brachypelma hamorii", "1.5", "30.00", "1"),
    ]
    
    table = build_dealer_supply_risk_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    return f"""#### Example 4: Low Reliability + High Demand (Critical Risk)
**Scenario:** A rarely available species with strong buyer interest

**Analysis Result:**

- **Stock Reliability:** {entry["Stock Reliability"]} (1/6 weeks)
- **Wishlist:** {entry["Wishlist"]} (carried from last seen)
- **Dealer Risk:** {entry["Dealer Risk"]}
- **Recommendation:** {entry["Dealer Recommendation"]}

**Why:** The combination of unreliable supply AND high buyer interest creates maximum risk. Dealers who don't stock this species are losing sales to competitors. This is the highest priority sourcing situation."""


def generate_dealer_example_5():
    """Example 5: Medium Reliability + Surging Demand (Escalated Risk)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "40.00", "8"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "40.00", "15"),
        make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
        # Out 1 week
        make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "40.00", "22"),
        make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "1"),
        # Out 1 week
        make_row("2025-02-05", "Grammostola pulchra", "2.0", "40.00", "1"),
    ]
    
    table = build_dealer_supply_risk_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    return f"""#### Example 5: Medium Reliability + Surging Demand (Escalated Risk)
**Scenario:** A moderately available species with rapidly increasing wishlist interest

**Analysis Result:**

- **Stock Reliability:** {entry["Stock Reliability"]}
- **Wishlist:** {entry["Wishlist"]}
- **Dealer Risk:** {entry["Dealer Risk"]}
- **Recommendation:** {entry["Dealer Recommendation"]}

**Why:** When demand is rapidly accelerating (wishlist rising significantly) combined with variable supply, this signals an emerging opportunity. Even though reliability is medium, the momentum suggests future supply problems. Dealers should act proactively."""


def generate_dealer_example_6():
    """Example 6: High Reliability + Falling Demand (No Action Needed)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "30.00", "20"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-08", "Aphonopelma seemanni", "1.0", "30.00", "15"),
        make_row("2025-01-08", "Grammostola pulchra", "2.0", "40.00", "1"),
        make_row("2025-01-15", "Aphonopelma seemanni", "1.0", "30.00", "10"),
        make_row("2025-01-15", "Grammostola pulchra", "2.0", "40.00", "1"),
    ]
    
    table = build_dealer_supply_risk_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    return f"""#### Example 6: High Reliability + Falling Demand (No Action Needed)
**Scenario:** A consistently available species with declining buyer interest

**Analysis Result:**

- **Stock Reliability:** {entry["Stock Reliability"]}
- **Wishlist:** {entry["Wishlist"]}
- **Dealer Risk:** {entry["Dealer Risk"]}
- **Recommendation:** {entry["Dealer Recommendation"]}

**Why:** Excellent supply reliability combined with declining interest means the market is well-supplied and demand is softening. Dealers should avoid stocking up and may want to clear existing inventory."""


def generate_dealer_example_7():
    """Example 7: Low Reliability + Surging Interest (Early Warning)."""
    history = [
        make_row("2025-01-01", "Aphonopelma seemanni", "1.0", "30.00", "5"),
        make_row("2025-01-01", "Grammostola pulchra", "2.0", "40.00", "1"),
        # Out 2 weeks
        make_row("2025-01-22", "Aphonopelma seemanni", "1.0", "30.00", "12"),
        make_row("2025-01-22", "Grammostola pulchra", "2.0", "40.00", "1"),
        # Out 1 week
        make_row("2025-02-05", "Grammostola pulchra", "2.0", "40.00", "1"),
    ]
    
    table = build_dealer_supply_risk_table(history)
    entry = _get_table_entry(table, "Aphonopelma seemanni")
    
    return f"""#### Example 7: Low Reliability + Surging Interest (Early Warning)
**Scenario:** An unreliable species showing early-stage demand growth

**Analysis Result:**

- **Stock Reliability:** {entry["Stock Reliability"]}
- **Wishlist:** {entry["Wishlist"]}
- **Dealer Risk:** {entry["Dealer Risk"]}
- **Recommendation:** {entry["Dealer Recommendation"]}

**Why:** Low reliability species with accelerating interest represent early-stage supply constraints. Even if current wishlist pressure isn't at maximum, the positive momentum combined with poor supply reliability signals dealers should secure stock before competition intensifies."""


if __name__ == "__main__":
    # Test generation
    print(generate_breeder_examples())
    print("\n\n")
    print(generate_dealer_examples())
