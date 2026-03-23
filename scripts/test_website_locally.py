#!/usr/bin/env python3
"""
Generate the website locally for testing from CSV files in tmp/local-testing/.

Usage:
    python test_website_locally.py [--serve] [--port PORT] [--seed-demo-data] [--overwrite-demo-data] [--data-only]

Options:
    --serve            Start a local HTTP server to preview the website
    --port PORT        Port for the local server (default: 8000)
    --seed-demo-data   Seed realistic local demo CSVs when required files are missing
    --overwrite-demo-data
                       Rewrite local CSVs with the realistic demo dataset before generating
    --data-only        Write demo data and exit without generating the website

Note:
    CSV files can come from real artifacts/scrapes or from the realistic local
    demo dataset used for development preview.
"""

import argparse
import http.server
import os
import socketserver
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


TESTING_DIR = Path("tmp/local-testing")
WEBSITE_DIR = TESTING_DIR / "website"


def run_command(cmd, capture_output=True, env=None):
    """Run a shell command and return output."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=capture_output, text=True, env=env)
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
    ensure_local_data(seed_demo_data=False, overwrite_demo_data=False)


def ensure_local_data(*, seed_demo_data: bool = False, overwrite_demo_data: bool = False):
    """Ensure local CSV inputs exist, optionally seeding realistic demo data."""
    from website.local_demo_data import ensure_local_csv_files, write_realistic_demo_data

    if overwrite_demo_data:
        print("🧪 Writing realistic local demo data...")
        write_realistic_demo_data(TESTING_DIR)
        return

    try:
        ensure_local_csv_files(TESTING_DIR, seed_demo_data=seed_demo_data)
    except FileNotFoundError as exc:
        print(f"❌ {exc}")
        print("\n🔧 Generate CSV files first:")
        print("   make download-artifacts  # Download from GitHub Actions")
        print("   # OR")
        print("   make scrape-only         # Run scraper locally")
        print("   # OR")
        print("   make seed-demo-data      # Write realistic local demo data")
        sys.exit(1)

    if seed_demo_data:
        required_files = [
            TESTING_DIR / "spidershop_spiderlings_scrape.csv",
            TESTING_DIR / "spidershop_spiderlings_history.csv",
            TESTING_DIR / "breeder_opportunity_table.csv",
            TESTING_DIR / "dealer_supply_risk_table.csv",
        ]
        if all(path.exists() for path in required_files):
            print("📁 Using existing local CSV files.")


def generate_website():
    """Run the website generator."""
    print("\nGenerating website...")
    
    # Ensure testing directory exists
    TESTING_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if website module exists
    website_module_path = Path("src/website/__main__.py")
    if not website_module_path.exists():
        print("❌ Could not find src/website/__main__.py")
        sys.exit(1)
    
    # Run the generator from the testing directory
    # This way all CSV files and outputs stay in tmp/local-testing/
    original_dir = Path.cwd()
    try:
        os.chdir(TESTING_DIR)
        # Set PYTHONPATH to include src directory
        env = os.environ.copy()
        env['PYTHONPATH'] = str(original_dir / 'src')
        run_command(["python3", "-m", "website"], capture_output=False, env=env)
    finally:
        os.chdir(original_dir)
    
    print(f"\n✅ Website generation complete!")
    print(f"   Website files: {TESTING_DIR / 'website'}")
    print(f"   CSV files: {TESTING_DIR}")


def serve_website(port=8000):
    """Start a local HTTP server to preview the website."""
    if not WEBSITE_DIR.exists():
        print(f"❌ Website directory '{WEBSITE_DIR}' not found")
        sys.exit(1)
    
    # Custom handler that skips reverse DNS lookups (which cause delays)
    class FastHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def address_string(self):
            # Return IP directly instead of doing reverse DNS lookup
            return self.client_address[0]
    
    # Enable socket reuse
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True
    
    print(f"\n🌐 Starting server at http://localhost:{port}")
    print(f"   Serving: {WEBSITE_DIR}")
    print("   Press Ctrl+C to stop\n")
    
    os.chdir(WEBSITE_DIR)
    
    with ReusableTCPServer(("127.0.0.1", port), FastHTTPRequestHandler) as httpd:
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
    parser.add_argument(
        "--seed-demo-data",
        action="store_true",
        help="Seed realistic demo CSVs when local inputs are missing",
    )
    parser.add_argument(
        "--overwrite-demo-data",
        action="store_true",
        help="Rewrite local CSVs with the realistic demo dataset before generating",
    )
    parser.add_argument(
        "--data-only",
        action="store_true",
        help="Write demo data and exit without generating the website",
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🕷️  Spider Shop Website Generator")
    print("=" * 70)
    
    # Check Python dependencies
    check_python_dependencies()
    
    if args.overwrite_demo_data and not args.seed_demo_data:
        parser.error("--overwrite-demo-data requires --seed-demo-data")

    if args.data_only and not args.seed_demo_data:
        parser.error("--data-only requires --seed-demo-data")

    # Verify or seed CSV files
    ensure_local_data(
        seed_demo_data=args.seed_demo_data,
        overwrite_demo_data=args.overwrite_demo_data,
    )

    if args.data_only:
        print("\n✅ Local demo data prepared.")
        return
    
    # Generate the website
    generate_website()
    
    # Optionally serve the website
    if args.serve:
        serve_website(args.port)
    else:
        print(f"\n💡 To preview the website, run:")
        print(f"   make scrape-website-serve   # Scrape + build + serve")
        print(f"   make website-serve          # Build from existing data + serve")
        print(f"   make seed-demo-data && make generate-website")
        print(f"\n   Or directly:")
        print(f"   python3 test_website_locally.py --serve")
        print(f"\n   Or manually:")
        print(f"   cd {WEBSITE_DIR} && python3 -m http.server 8000")


if __name__ == "__main__":
    main()
