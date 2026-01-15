#!/usr/bin/env python3
"""
Quick demo/test of the local website testing workflow.

This script demonstrates the typical workflow for testing website changes locally.
"""

import subprocess
import sys
from pathlib import Path


def run_cmd(cmd, description):
    """Run a command and print status."""
    print(f"\n{'='*70}")
    print(f"🔧 {description}")
    print(f"{'='*70}")
    print(f"Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd)
    
    if result.returncode != 0:
        print(f"\n❌ Command failed with exit code {result.returncode}")
        return False
    
    print(f"\n✅ {description} complete")
    return True


def main():
    """Demonstrate the local testing workflow."""
    
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║  Spider Shop Website - Local Testing Demo                           ║
║  This demo shows how to test website changes locally                ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    # Step 1: Check prerequisites
    print("\n📋 Step 1: Checking prerequisites...")
    
    # Check if gh is installed
    result = subprocess.run(["which", "gh"], capture_output=True)
    if result.returncode != 0:
        print("❌ GitHub CLI (gh) is not installed")
        print("\nInstall with:")
        print("  brew install gh")
        print("  gh auth login")
        sys.exit(1)
    
    print("✅ GitHub CLI (gh) is installed")
    
    # Check if authenticated
    result = subprocess.run(["gh", "auth", "status"], capture_output=True)
    if result.returncode != 0:
        print("❌ GitHub CLI is not authenticated")
        print("\nAuthenticate with:")
        print("  gh auth login")
        sys.exit(1)
    
    print("✅ GitHub CLI is authenticated")
    
    # Step 2: Explain workflow
    print("""
📚 Step 2: Understanding the workflow

The test_website_locally.py script automates these steps:

  1. 🔍 Find latest successful scrape workflow run
  2. 📥 Download artifacts (CSV files, markdown summary)
  3. 🏗️  Generate static website HTML files
  4. 🌐 (Optional) Serve website locally for preview

You can now:
  
  A) Run the full workflow:
     python3 test_website_locally.py --serve
     
  B) Use Makefile shortcuts:
     make test-website-serve
     
  C) Run without serving (generate only):
     python3 test_website_locally.py
     make test-website
     
  D) Regenerate without re-downloading:
     python3 test_website_locally.py --skip-download
""")
    
    # Step 3: Ask user what to do
    print("\n" + "="*70)
    print("What would you like to do?")
    print("="*70)
    print("1) Download artifacts and generate website (don't serve)")
    print("2) Download artifacts, generate website, and start server")
    print("3) Just show me the commands (don't run anything)")
    print("0) Exit")
    
    try:
        choice = input("\nEnter your choice (0-3): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n\n👋 Cancelled")
        sys.exit(0)
    
    if choice == "0":
        print("\n👋 Goodbye!")
        return
    
    elif choice == "1":
        success = run_cmd(
            ["python3", "test_website_locally.py"],
            "Downloading artifacts and generating website"
        )
        if success:
            print("\n" + "="*70)
            print("🎉 Success! Website generated in 'website/' directory")
            print("="*70)
            print("\nTo preview the website, run:")
            print("  cd website && python3 -m http.server 8000")
            print("  Or: python3 test_website_locally.py --skip-download --serve")
    
    elif choice == "2":
        print("\n⚠️  This will start a local HTTP server on port 8000")
        print("   Press Ctrl+C to stop the server when done")
        input("\nPress Enter to continue...")
        
        run_cmd(
            ["python3", "test_website_locally.py", "--serve"],
            "Downloading, generating, and serving website"
        )
    
    elif choice == "3":
        print("""
📖 Quick Reference Commands:

# Using Makefile (recommended)
make test-website               # Download and generate
make test-website-serve         # Download, generate, and serve
make clean-artifacts            # Clean up downloaded files

# Using Python script directly  
python3 test_website_locally.py                  # Download and generate
python3 test_website_locally.py --serve          # Download, generate, serve
python3 test_website_locally.py --skip-download  # Regenerate only
python3 test_website_locally.py --run-id 12345   # Use specific run ID
python3 test_website_locally.py --port 3000      # Use custom port

# Manual workflow
cd website && python3 -m http.server 8000       # Serve existing website
make clean-artifacts                             # Clean up

📚 Full documentation: docs/LOCAL_TESTING.md
""")
    
    else:
        print("❌ Invalid choice")


if __name__ == "__main__":
    main()
