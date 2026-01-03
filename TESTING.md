# Testing Instructions for Wishlist Count Feature

## Overview
This document describes how to test the new wishlist count extraction feature that has been added to the spidershop scraper.

## What Was Changed

### New Column: `wishlist_count`
- Added between `price_gbp` and `page_url` in the CSV schema
- Contains the number of users who have added each product to their wishlist
- Extracted from: `<span class="yith-wcwl-add-to-wishlist__counter">17 users have this item in their wishlists</span>`

### Technology Stack Updates
- **Selenium WebDriver**: Added to handle JavaScript-rendered content
- **Headless Chrome**: Used to execute JavaScript and wait for dynamic elements
- **Explicit Waits**: Waits up to 10 seconds for wishlist counter element to appear

### Modified Files
1. `src/config.py` - Added wishlist_count to CSV_HEADER and WISHLIST_COUNT_RE regex
2. `src/parsing.py` - Added parse_wishlist_count() function
3. `src/scraper.py` - Updated to use browser automation for product pages
4. `src/browser_client.py` - NEW: Selenium WebDriver wrapper module
5. `src/scrape_spidershop_spiderlings.py` - Added browser cleanup in finally block
6. `.github/workflows/scrape.yml` - Added Chrome installation and selenium dependency

## How to Test

### Step 1: Trigger the GitHub Workflow
1. Go to the repository: https://github.com/christianacca/spidershop-historical-analysis
2. Click on "Actions" tab
3. Select "Spider Shop Spiderlings Scrape" workflow
4. Click "Run workflow" button
5. Select the branch: `copilot/add-wishlist-count-extraction`
6. Click "Run workflow" to start

### Step 2: Wait for Completion
- The workflow should take 5-15 minutes depending on the number of products
- Monitor the workflow progress in the Actions tab
- Check for any errors in the workflow logs

### Step 3: Download and Verify Artifacts

#### Download the Snapshot Artifact
1. Once workflow completes, scroll down to "Artifacts" section
2. Download `spidershop-snapshot` artifact
3. Extract the ZIP file to get `spidershop_spiderlings_scrape.csv`

#### Verify CSV Structure
Open the CSV file and verify:

1. **Column Headers** (in order):
   - scrape_datetime
   - scientific_name
   - common_name
   - size_cm
   - price_gbp
   - **wishlist_count** ← NEW COLUMN
   - page_url

2. **Data Validation**:
   - The `wishlist_count` column should contain integer values (0 or greater)
   - **Most importantly**: Verify that MULTIPLE rows have values > 0
   - Example row:
     ```
     2026-01-03T16:00,Aphonopelma seemanni,Costa Rican Zebra,2,45.00,17,https://thespidershop.co.uk/product/...
     ```

3. **Expected Results**:
   - ✓ All rows should have the wishlist_count column populated
   - ✓ Some rows should have wishlist_count > 0 (e.g., 1, 5, 17, 42, etc.)
   - ✓ Rows with no wishlist data should show "0"
   - ✓ No rows should have empty/missing wishlist_count values

### Step 4: Verify History File
1. Download `spidershop-history__copilot-add-wishlist-count-extraction` artifact (or similar branch-scoped name)
2. Extract and open `spidershop_spiderlings_history.csv`
3. Verify it also has the `wishlist_count` column
4. Check that historical data is preserved (if any existed before)

## Expected Behavior

### Success Criteria
- ✅ Workflow completes without errors
- ✅ CSV files contain the new `wishlist_count` column
- ✅ Multiple products have wishlist_count > 0
- ✅ Wishlist counts match the actual website data
- ✅ No data loss in other columns

### Common Issues and Solutions

#### All wishlist_count values are 0
- **Cause**: Website changed the HTML structure or class names
- **Solution**: Inspect a product page on the website to verify the selector `.yith-wcwl-add-to-wishlist__counter` is still correct

#### Workflow fails during Chrome installation
- **Cause**: Chrome setup action failed
- **Solution**: Check if `browser-actions/setup-chrome@v1` is still valid, may need version update

#### Selenium errors (NoSuchElementException, WebDriverException)
- **Cause**: Chrome driver or browser compatibility issues
- **Solution**: Check workflow logs for specific error, may need to update Selenium version or Chrome flags

#### Timeout errors
- **Cause**: Pages taking longer than 10 seconds to load wishlist element
- **Solution**: Increase timeout value in `scraper.py` (currently 10 seconds)

## Rollback Plan
If the feature causes issues, rollback by:
1. Reverting to commit `611fb55` (before wishlist changes)
2. Or removing the `wishlist_count` column from CSV_HEADER and reverting scraper.py changes

## Contact
For questions or issues, create an issue in the GitHub repository.
