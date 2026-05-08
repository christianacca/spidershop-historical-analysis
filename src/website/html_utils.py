"""HTML generation utilities for website components.

This module provides the shared Jinja2 environment used by website generators.
"""

import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


# Setup Jinja2 environment
template_dir = Path(__file__).parent.parent.parent / "templates"
jinja_env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml']),
    trim_blocks=True,
    lstrip_blocks=True
)

try:
    from website.page_config import NAV_ITEMS
except ModuleNotFoundError:
    from page_config import NAV_ITEMS  # type: ignore[no-redef]

jinja_env.globals['nav_items'] = NAV_ITEMS
# Build version baked into HTML at generation time.  In CI this is the same
# '{shortSha}-r{runId}' string injected into the JS bundle, so comparing the
# two footer values immediately reveals which cache layer (HTML vs JS) is stale.
jinja_env.globals['build_version'] = os.environ.get('BUILD_VERSION', 'local-dev')
