# spidershop-historical-analysis

A conservative, supply-first market analysis system for UK tarantula spiderlings, built on weekly historical data scraped from  
[The Spider Shop UK](https://thespidershop.co.uk/).

This project is **not a price-tracking dashboard** or a hype detector.  
It is designed to surface **meaningful, explainable signals** for breeders and dealers while deliberately avoiding noise.

---

## What This Project Does

On a **weekly schedule**, the scraper captures all listed tarantula spiderlings and records:

- Scientific name (Genus + species)
- Common name
- Size (cm)
- Price (GBP)
- Wishlist count (number of users who have wish-listed the species)

Each run appends to a growing historical dataset.  
That history is then analysed to produce two conservative decision-support tables:

1. **Breeder Opportunity Matrix**
2. **Dealer Supply Risk Matrix**

All outputs are published as CSV artifacts and rendered on GitHub Pages.

---

## Accessing the Data

### 🌐 GitHub Pages (Recommended)

**https://christianacca.github.io/spidershop-historical-analysis/**

Provides:
- Latest snapshot
- Historical data
- Interactive tables
- CSV downloads
- Breeder & dealer analyses

Updated automatically after each successful run.

### 📦 GitHub Actions Artifacts

Each workflow run publishes:

- `spidershop-snapshot.csv`
- `spidershop-history.csv`
- `breeder_opportunity_table.csv`
- `dealer_supply_risk_table.csv`

Available via the **Actions** tab on GitHub.

---

## Core Design Philosophy

This project follows a few strict principles:

### 1. Supply Comes First
Out-of-stock behaviour, persistence, and restock speed matter more than demand alone.

### 2. Conservative by Default
Neutral signals are preferred over guessing.  
Single-run changes are treated as noise unless confirmed.

### 3. Weekly Cadence Awareness
All thresholds and comparisons assume **weekly execution**.

### 4. No Inference of Missing Data
If a signal cannot be derived confidently, it remains neutral.

The goal is **decision support**, not prediction.

---

## Key Concepts Explained

### Out-of-Stock Patterns (Supply)

Each species is classified into one of four patterns:

- **Always** — normally available; short absences treated as noise
- **Emerging** — missing for multiple consecutive runs
- **Sustained** — missing for many weeks (strong scarcity signal)
- **Cyclical** — repeated disappear / reappear behaviour (batch supply)

These patterns are the foundation of all analysis.

### Price Trend

A simple directional indicator comparing recent prices:

- `↑` increasing
- `→` stable
- `↓` decreasing

Price trend **confirms or weakens** supply signals but never overrides them.

### Wishlist Pressure (Latent Demand)

Wishlist pressure represents **relative buyer interest within a single run**.

- Calculated per-run using ranking (not absolute thresholds)
- Includes safeguards:
  - small-N flattening
  - bounded carryover for out-of-stock species (≤ 3 runs)

Values:
- `🔥` high relative interest
- `⚠️` moderate interest
- `❌` low or no interest

Wishlist pressure **amplifies confidence**; it is never a trigger on its own.

### Wishlist Delta (Momentum)

Wishlist Delta measures **meaningful change in buyer interest** over time.

- Compares two recent *in-stock* observations
- Both values are **time-bounded** to avoid stale comparisons
- Conservative thresholds:
  - `↑` Δ ≥ +5
  - `→` −4 ≤ Δ ≤ +4
  - `↓` Δ ≤ −5

Wishlist Delta acts as a **momentum modifier**, not a standalone signal.

---

## Analysis Outputs

### 🧬 Breeder Opportunity Matrix

**Audience:** Breeders  
**Question answered:** *“Is it worth pairing this species soon?”*

Logic summary:
- Supply pattern is primary
- Price trend confirms or weakens
- Wishlist metrics only escalate **emerging** opportunities
- Sustained scarcity is never downgraded

Strong signals are rare by design.

### 🏪 Dealer Supply Risk Matrix

**Audience:** Dealers  
**Question answered:** *“Am I at risk of lost sales?”*

Logic summary:
- Stock reliability and restock speed dominate
- Wishlist metrics adjust urgency, not classification
- Healthy supply cannot be overridden by demand alone

---

## Automation & Technical Details

- **Schedule:** Weekly (Wednesday, 06:10 UTC)
- **Language:** Python 3.11
- **Dependencies:** requests, beautifulsoup4
- **Architecture:** Modular (`src/` directory)
- **Testing:** Runtime assertions (fail fast, descriptive)

No machine learning.  
No black boxes.  
Every signal is explainable in plain English.

---

## What This Project Is Not

- ❌ A prediction engine  
- ❌ A hype tracker  
- ❌ A real-time sales proxy  

It is a **calm, conservative signal system** designed to be trusted over time.

---

## License & Disclaimer

This project is for research and analysis purposes only.  
It is not affiliated with or endorsed by The Spider Shop UK.
