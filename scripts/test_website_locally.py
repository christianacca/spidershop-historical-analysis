#!/usr/bin/env python3
"""
Generate the website locally for testing from CSV files in tmp/local-testing/.

Usage:
    python test_website_locally.py [--serve] [--port PORT]

Options:
    --serve            Start a local HTTP server to preview the website
    --port PORT        Port for the local server (default: 8000)

Note:
    CSV files must exist in tmp/local-testing/ before running this script.
    Use 'make download-artifacts' or 'make scrape-only' to obtain them.
"""

import argparse
import http.server
import os
import socketserver
import subprocess
import sys
from pathlib import Path


TESTING_DIR = Path("tmp/local-testing")
WEBSITE_DIR = TESTING_DIR / "website"


def run_command(cmd, capture_output=True):
    """Run a shell command and return output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture_output, text=True)
    if result.returncode != 0:
        print(f"❌ Error running command: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip() if capture_output else None


def check_python_dependencies():
    """Check if required Python dependencies are installed."""
    try:
        import markdown
    except ImportError:
        print("❌ Required Python dependencies are not installed.")
        print("\n🔧 Fix this by installing dependencies:")
        print("\n   # If using a virtual environment (recommended):")
        print("   source .venv/bin/activate          # macOS/Linux")
        print("   .venv\\Scripts\\activate.bat         # Windows (CMD)")
        print("   .venv\\Scripts\\Activate.ps1         # Windows (PowerShell)")
        print("   pip install -r requirements.txt")
        print("\n   # Or install system-wide (not recommended):")
        print("   pip3 install --user -r requirements.txt")
        sys.exit(1)


def verify_csv_files():
    """Verify that required CSV files exist."""
    required_files = [
        TESTING_DIR / "spidershop_spiderlings_scrape.csv",
        TESTING_DIR / "spidershop_spiderlings_history.csv",
        TESTING_DIR / "breeder_opportunity_table.csv",
        TESTING_DIR / "dealer_supply_risk_table.csv"
    ]
    
    missing = [f.name for f in required_files if not f.exists()]
    if missing:
        print(f"❌ Missing required CSV files: {', '.join(missing)}")
        print(f"\n🔧 Generate CSV files first:")
        print(f"   make download-artifacts  # Download from GitHub Actions")
        print(f"   # OR")
        print(f"   make scrape-only         # Run scraper locally")
        sys.exit(1)


def generate_website():
    """Run the website generator."""
    print("\nGenerating website...")
    
    # Ensure testing directory exists
    TESTING_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if generate_website.py exists
    generator_path = Path("src/generate_website.py")
    if not generator_path.exists():
        print("❌ Could not find src/generate_website.py")
        sys.exit(1)
    
    # Run the generator from the testing directory
    # This way all CSV files and outputs stay in tmp/local-testing/
    original_dir = Path.cwd()
    try:
        os.chdir(TESTING_DIR)
        run_command(["python3", str(original_dir / generator_path)], capture_output=False)
    finally:
        os.chdir(original_dir)
    
    print(f"\n✅ Website generation complete!")
    print(f"   Website files: {TESTING_DIR / 'website'}")
    print(f"   CSV files: {TESTING_DIR}")
    
    print("\n✅ Website generation complete!")


def serve_website(port=8000):
    """Start a local HTTP server to preview the website."""
    if not WEBSITE_DIR.exists():
        print(f"❌ Website directory '{WEBSITE_DIR}' not found")
        sys.exit(1)
    
    print(f"\n🌐 Starting local server at http://localhost:{port}")
    print(f"   Serving: {WEBSITE_DIR}")
    print("   Press Ctrl+C to stop the server\n")
    
    os.chdir(WEBSITE_DIR)
    
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Generate website locally from CSV files in tmp/local-testing/"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start a local HTTP server after generation"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for local server (default: 8000)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🕷️  Spider Shop Website Generator")
    print("=" * 70)
    
    # Check Python dependencies
    check_python_dependencies()
    
    # Verify CSV files exist
    verify_csv_files()
    
    # Generate the website
    generate_website()
    
    # Optionally serve the website
    if args.serve:
        serve_website(args.port)
    else:
        print(f"\n💡 To preview the website, run:")
        print(f"   make scrape-website-serve   # Scrape + build + serve")
        print(f"   make website-serve          # Build from existing data + serve")
        print(f"\n   Or directly:")
        print(f"   python3 test_website_locally.py --serve")
        print(f"\n   Or manually:")
        print(f"   cd {WEBSITE_DIR} && python3 -m http.server 8000")


if __name__ == "__main__":
    main()
