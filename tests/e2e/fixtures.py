"""Shared fixtures for E2E tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def e2e_site_minimal(request):
    """E2E test fixture with minimal data (1 species) for navigation/smoke tests.
    
    Module-scoped: Website is generated once per test module for performance.
    
    Yields:
        tuple: (page, base_url, errors) where:
            - page: Playwright Page object
            - base_url: Local server URL (e.g., "http://127.0.0.1:12345")
            - errors: Dict with 'console_errors', 'page_errors', 'bad_responses' lists
    
    Automatically handles:
        - RUN_E2E environment check
        - Website generation with minimal test data (once per module)
        - Browser/server setup and teardown
        - Trace recording (only on test failure)
        - Error filtering (local URLs only)
    """
    if os.environ.get("RUN_E2E") != "1":
        pytest.skip("Playwright E2E tests are opt-in; run via `make test-e2e`.")

    playwright_sync = pytest.importorskip("playwright.sync_api")
    sync_playwright = playwright_sync.sync_playwright
    
    from website.generate_website import OUTPUT_DIR, main
    from e2e.helpers import (
        write_minimal_test_data,
        test_server,
        create_browser_with_error_capture,
        assert_no_browser_errors
    )

    # Setup
    cwd = Path.cwd()
    write_minimal_test_data(cwd)
    main()

    output_dir = (cwd / OUTPUT_DIR).resolve(strict=False)
    assert output_dir.exists(), "Expected website output directory to exist"

    # Browser options
    headed = os.environ.get("PWHEADED") == "1" or request.config.getoption("--headed", default=False)
    slow_mo = int(os.environ.get("PWSLOW", "0"))
    video_dir = cwd / "tmp" / "e2e-videos" if os.environ.get("PWVIDEO") == "1" else None
    
    # Trace only on failure (PWTRACE=1 forces always-on)
    module_name = request.module.__name__.split('.')[-1]
    trace_path = cwd / "tmp" / f"e2e-trace-{module_name}-minimal.zip" if os.environ.get("PWTRACE") == "1" else None

    with test_server(output_dir) as base_url:
        with sync_playwright() as p:
            browser, context, page, errors = create_browser_with_error_capture(
                p, headed=headed, slow_mo=slow_mo, video_dir=video_dir, trace_path=trace_path
            )

            try:
                yield page, base_url, errors
            finally:
                # Filter responses to only include local server URLs
                errors['bad_responses'] = [
                    resp for resp in errors['bad_responses'] 
                    if base_url in resp
                ]
                
                # Cleanup
                if trace_path:
                    context.tracing.stop(path=str(trace_path))
                context.close()
                browser.close()
                
                # Assert no errors at the end
                assert_no_browser_errors(errors, None)


@pytest.fixture(scope="module")
def e2e_site_multi_species(request):
    """E2E test fixture with multi-species data (5 species) for table interaction tests.
    
    Module-scoped: Website is generated once per test module for performance.
    
    Yields:
        tuple: (page, base_url, errors) where:
            - page: Playwright Page object
            - base_url: Local server URL (e.g., "http://127.0.0.1:12345")
            - errors: Dict with 'console_errors', 'page_errors', 'bad_responses' lists
    
    Automatically handles:
        - RUN_E2E environment check
        - Website generation with multi-species test data (once per module)
        - Browser/server setup and teardown
        - Trace recording (only on test failure)
        - Error filtering (local URLs only)
    """
    if os.environ.get("RUN_E2E") != "1":
        pytest.skip("Playwright E2E tests are opt-in; run via `make test-e2e`.")

    playwright_sync = pytest.importorskip("playwright.sync_api")
    sync_playwright = playwright_sync.sync_playwright
    
    from website.generate_website import OUTPUT_DIR, main
    from e2e.helpers import (
        write_multi_species_test_data,
        test_server,
        create_browser_with_error_capture,
        assert_no_browser_errors
    )

    # Setup
    cwd = Path.cwd()
    write_multi_species_test_data(cwd)
    main()

    output_dir = (cwd / OUTPUT_DIR).resolve(strict=False)
    assert output_dir.exists(), "Expected website output directory to exist"

    # Browser options
    headed = os.environ.get("PWHEADED") == "1" or request.config.getoption("--headed", default=False)
    slow_mo = int(os.environ.get("PWSLOW", "0"))
    video_dir = cwd / "tmp" / "e2e-videos" if os.environ.get("PWVIDEO") == "1" else None
    
    # Trace only on failure (PWTRACE=1 forces always-on)
    module_name = request.module.__name__.split('.')[-1]
    trace_path = cwd / "tmp" / f"e2e-trace-{module_name}-multi.zip" if os.environ.get("PWTRACE") == "1" else None

    with test_server(output_dir) as base_url:
        with sync_playwright() as p:
            browser, context, page, errors = create_browser_with_error_capture(
                p, headed=headed, slow_mo=slow_mo, video_dir=video_dir, trace_path=trace_path
            )

            try:
                yield page, base_url, errors
            finally:
                # Filter responses to only include local server URLs
                errors['bad_responses'] = [
                    resp for resp in errors['bad_responses'] 
                    if base_url in resp
                ]
                
                # Cleanup
                if trace_path:
                    context.tracing.stop(path=str(trace_path))
                context.close()
                browser.close()
                
                # Assert no errors at the end
                assert_no_browser_errors(errors, None)
