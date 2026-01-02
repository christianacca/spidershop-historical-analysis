# Copilot Instructions for spidershop-historical-analysis

## Project Overview

This is a Python web scraper that captures pricing data for tarantula spiderlings from The Spider Shop UK website. The scraper runs on a weekly schedule via GitHub Actions and maintains historical pricing data as artifacts.

## Project Purpose

- Scrape tarantula spiderling listings including scientific name, common name, size, and price
- Track pricing history over time for market analysis
- Generate opportunity matrices for breeders and dealers
- Store data as CSV files uploaded to GitHub Actions artifacts

## Project Structure

The project uses a modular architecture with focused modules in the `src/` directory:

- **scrape_spidershop_spiderlings.py**: Main entry point that orchestrates the scraping workflow
- **scraper.py**: Core scraping logic for extracting product URLs and product details
- **http_client.py**: HTTP request handling with proper headers
- **parsing.py**: Text parsing utilities (whitespace normalization, size/price extraction)
- **config.py**: Configuration constants (URLs, file names, regex patterns)
- **history.py**: Historical data management (loading and appending history)
- **pricing_summary.py**: Pricing analysis and summary generation
- **breeder_matrix.py**: Breeder opportunity table generation
- **dealer_matrix.py**: Dealer supply risk table generation
- **legend.py**: Summary legend generation
- **assertions.py**: Validation and assertion utilities

## Dependencies

This project uses minimal external dependencies:

- **requests**: HTTP requests for web scraping
- **beautifulsoup4**: HTML parsing and data extraction
- Standard library: csv, datetime, urllib, decimal, re, os

No requirements.txt or pyproject.toml file currently exists. Dependencies are installed directly in the GitHub Actions workflow.

## Coding Conventions

1. **Python Version**: Python 3.11
2. **Style**: Follow PEP 8 conventions
3. **Imports**: Use absolute imports from src modules
4. **String handling**: Use UTF-8 encoding for file operations
5. **Error handling**: Use assertions for validation with descriptive messages
6. **CSV format**: Use the CSV_HEADER defined in config.py for consistency
7. **Whitespace normalization**: Use the normalize_whitespace() function from parsing.py
8. **Regex patterns**: Define regex patterns in config.py for reusability

## Web Scraping Guidelines

- **User-Agent**: Use the configured User-Agent string in config.py
- **Pagination**: Handle pagination by incrementing page numbers until 404
- **URLs**: Use urljoin() for proper URL construction
- **Selectors**: Use CSS selectors with BeautifulSoup for HTML parsing
- **Error handling**: Catch HTTPError and handle 404s gracefully for pagination
- **Rate limiting**: Be respectful of the target website (no rate limiting currently implemented)

## Data Management

- **Snapshot file**: Current scrape results saved as `spidershop_spiderlings_scrape.csv`
- **History file**: Accumulated historical data in `spidershop_spiderlings_history.csv`
- **Matrix files**: Analysis outputs in `breeder_opportunity_table.csv` and `dealer_supply_risk_table.csv`
- **Artifacts**: Files are uploaded to GitHub Actions artifacts (branch-scoped for history)

## Workflow and CI/CD

- **Schedule**: Weekly execution (Wednesday 06:10 UTC)
- **Trigger**: Manual workflow_dispatch also supported
- **History management**: Branch-scoped artifacts with fallback to default branch
- **Artifact lifecycle**: History artifacts persist between runs; snapshots are per-run

## Testing

Currently, the project uses runtime assertions for validation:

- Use assertions.py utilities for validation
- Check row counts, data presence, and expected values
- Assertions should fail fast with descriptive error messages

No formal test suite (pytest, unittest) currently exists.

## Common Tasks

### Adding a new parsing function
1. Add the function to parsing.py
2. Add any regex patterns to config.py
3. Use normalize_whitespace() for text processing
4. Handle edge cases with empty/None values

### Modifying scraper logic
1. Update scraper.py for extraction changes
2. Keep functions focused and single-purpose
3. Test with actual web pages before deploying

### Adding new analysis
1. Create a new module in src/ (e.g., new_analysis.py)
2. Follow the pattern of breeder_matrix.py or dealer_matrix.py
3. Import and call from scrape_spidershop_spiderlings.py main()
4. Update workflow to upload new artifact files

## Domain Context

- **Scientific names**: Genus + species (e.g., "Aphonopelma seemanni")
- **Common names**: Descriptive names (e.g., "Costa Rican Zebra")
- **Size**: Typically in cm, extracted from parenthetical notation
- **Price**: In GBP (£), decimal format
- **Spiderlings**: Juvenile tarantulas, distinct from adults

## Important Constraints

- Do not add rate limiting or delays that would significantly slow down the scraper
- Maintain CSV format compatibility for historical data
- Keep modules focused and avoid creating monolithic files
- Preserve existing workflow artifact naming conventions for backward compatibility
