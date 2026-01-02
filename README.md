# spidershop-historical-analysis

A Python web scraper that captures and tracks pricing data for tarantula spiderlings from [The Spider Shop UK](https://thespidershop.co.uk/).

## Purpose

This project automatically scrapes tarantula spiderling listings from The Spider Shop UK website on a weekly schedule, capturing:
- **Scientific name** (Genus + species)
- **Common name** (descriptive name)
- **Size** (in centimeters)
- **Price** (in GBP)

The scraped data is used to:
- Track pricing history over time for market analysis
- Generate **Breeder Opportunity Matrices** that identify species with growing demand or favorable pricing trends
- Generate **Dealer Supply Risk Tables** that highlight inventory availability patterns

## How to Access the Scraped Data

The scraper runs automatically every **Wednesday at 06:10 UTC** via GitHub Actions. You can access the data [here](https://github.com/christianacca/spidershop-historical-analysis/actions/workflows/scrape.yml?query=branch%3Amaster).

Alternatively:

1. **Navigate to the Actions tab** in this repository
2. **Click on "Spider Shop Spiderlings Scrape"** workflow runs 
3. **Select the most recent workflow run** (the one at the top of the list)
4. **Scroll down to the "Artifacts" section** at the bottom of the workflow run page

### Available Artifacts

Each workflow run generates the following artifacts:

- **`spidershop-snapshot`** - Current scrape results for this run (CSV format)
- **`spidershop-history`** - Accumulated historical data across all runs (CSV format)
- **`breeder-opportunity-table`** - Analysis showing breeding opportunities based on market trends (CSV format)
- **`dealer-supply-risk-table`** - Analysis showing supply availability patterns (CSV format)

Simply click on any artifact name to download it as a ZIP file, then extract the CSV file(s) inside.

### Manual Workflow Execution

You can also trigger a scrape manually:

1. Go to the **Actions** tab
2. Select **"Spider Shop Spiderlings Scrape"** workflow
3. Click **"Run workflow"** button
4. Select the branch and click **"Run workflow"**

## Technical Details

The script was created via the following ChatGPT session: [Tarantula Scraping Scheduler](https://chatgpt.com/share/69583ba1-0e20-8008-9898-c8024292a0a8)

- **Language**: Python 3.11
- **Key Dependencies**: requests, beautifulsoup4
- **Architecture**: Modular design with separate modules for scraping, parsing, analysis, and data management
