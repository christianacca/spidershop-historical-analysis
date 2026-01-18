#!/usr/bin/env python3
"""
Download artifacts from the latest GitHub Actions scrape workflow run
and generate the website locally for testing.

Usage:
    python test_website_locally.py [--run-id RUN_ID] [--serve] [--port PORT]

Options:
    --run-id RUN_ID    Specific workflow run ID to download from (optional)
    --serve            Start a local HTTP server to preview the website
    --port PORT        Port for the local server (default: 8000)
"""

import argparse
import http.server
import os
import shutil
import socketserver
import subprocess
import sys
from pathlib import Path


REPO_OWNER = "christianacca"
REPO_NAME = "spidershop-historical-analysis"
WORKFLOW_NAME = "Spider Shop Spiderlings Scrape"
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


def check_gh_cli():
    """Check if GitHub CLI is installed and authenticated."""
    try:
        run_command(["gh", "--version"])
    except FileNotFoundError:
        print("❌ GitHub CLI (gh) is not installed.")
        print("Install it with: brew install gh")
        print("Then authenticate with: gh auth login")
        sys.exit(1)
    
    # Check authentication
    result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if result.returncode != 0:
        print("❌ GitHub CLI is not authenticated.")
        print("Run: gh auth login")
        sys.exit(1)


def get_latest_workflow_run(run_id=None):
    """Get the latest successful scrape workflow run ID."""
    if run_id:
        print(f"Using specified run ID: {run_id}")
        return run_id
    
    print("Finding latest successful scrape workflow run...")
    cmd = [
        "gh", "api",
        f"repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows",
        "--paginate",
        "-q", f'.workflows[] | select(.name == "{WORKFLOW_NAME}") | .id'
    ]
    workflow_id = run_command(cmd)
    
    if not workflow_id:
        print(f"❌ Could not find workflow named '{WORKFLOW_NAME}'")
        sys.exit(1)
    
    print(f"Found workflow ID: {workflow_id}")
    
    # Get latest successful run
    cmd = [
        "gh", "api",
        f"repos/{REPO_OWNER}/{REPO_NAME}/actions/workflows/{workflow_id}/runs",
        "-q", '.workflow_runs[] | select(.conclusion == "success") | .id'
    ]
    output = run_command(cmd)
    run_ids = output.split('\n')
    
    if not run_ids or not run_ids[0]:
        print(f"❌ No successful runs found for workflow '{WORKFLOW_NAME}'")
        sys.exit(1)
    
    latest_run_id = run_ids[0]
    print(f"✅ Found latest successful run: {latest_run_id}")
    return latest_run_id


def download_artifact(run_id, artifact_name):
    """Download a specific artifact from a workflow run."""
    print(f"  Downloading {artifact_name}...")
    
    # Use the shared download script
    cmd = [
        "./scripts/download_artifact.sh",
        REPO_OWNER,
        REPO_NAME,
        artifact_name,
        str(TESTING_DIR),
        run_id
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"    ✅ Downloaded and extracted {artifact_name}")
        return True
    elif result.returncode == 1:
        print(f"    ⚠️  Artifact '{artifact_name}' not found (skipping)")
        return False
    else:
        print(f"    ⚠️  Failed to download '{artifact_name}': {result.stderr.strip()}")
        return False


def download_all_artifacts(run_id):
    """Download all required artifacts from a workflow run."""
    print("\nDownloading artifacts from GitHub Actions...")
    
    artifacts = [
        "spidershop-snapshot",
        "spidershop-history",
        "breeder-opportunity-table",
        "dealer-supply-risk-table",
        "analysis-summary"
    ]
    
    success_count = 0
    for artifact in artifacts:
        if download_artifact(run_id, artifact):
            success_count += 1
    
    print(f"\n✅ Downloaded {success_count}/{len(artifacts)} artifacts")
    
    # Verify required files exist in testing directory
    required_files = [
        TESTING_DIR / "spidershop_spiderlings_scrape.csv",
        TESTING_DIR / "spidershop_spiderlings_history.csv",
        TESTING_DIR / "breeder_opportunity_table.csv",
        TESTING_DIR / "dealer_supply_risk_table.csv"
    ]
    
    missing = [f.name for f in required_files if not f.exists()]
    if missing:
        print(f"\n⚠️  Warning: Some required files are missing: {', '.join(missing)}")


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
        description="Download artifacts and test website generation locally"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="Specific workflow run ID to download from"
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
        "--skip-download",
        action="store_true",
        help="Skip downloading artifacts (use existing files)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🕷️  Spider Shop Website Local Testing Tool")
    print("=" * 70)
    
    # Check Python dependencies first (always needed)
    check_python_dependencies()
    
    # Check prerequisites
    if not args.skip_download:
        check_gh_cli()
        
        # Get the run ID
        run_id = get_latest_workflow_run(args.run_id)
        
        # Download artifacts
        download_all_artifacts(run_id)
    else:
        print("\n⏭️  Skipping artifact download (using existing files)")
    
    # Generate the website
    generate_website()
    
    # Optionally serve the website
    if args.serve:
        serve_website(args.port)
    else:
        print(f"\n💡 To preview the website, run:")
        print(f"   make test-website-serve")
        print(f"\n   Or directly:")
        print(f"   python3 test_website_locally.py --serve")
        print(f"\n   Or manually:")
        print(f"   cd {WEBSITE_DIR} && python3 -m http.server 8000")


if __name__ == "__main__":
    main()
