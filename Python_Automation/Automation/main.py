"""
main.py
========
CS Study Hub — Python Automation Project
Runs the full pipeline: Scrape → Analyze → Export → PDF Report

Usage:
  python main.py

Requirements (install once):
  pip install playwright beautifulsoup4 reportlab matplotlib
  playwright install chromium
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Force UTF-8 encoding for standard output and error to prevent Windows console crashes
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import study_hub_scraper as scraper
import report_generator  as reporter

OUTPUT_DIR = Path("study_hub_output")
DIVIDER    = "═" * 55


def print_terminal_summary(data: dict, all_notes: list, all_flashcards: list, all_quizzes: list):
    """Print a formatted summary table to the terminal."""
    print(f"\n{DIVIDER}")
    print("  📊  CS STUDY HUB — CONTENT SUMMARY")
    print(DIVIDER)
    print(f"  {'Subject':<22} {'Notes':>7} {'Cards':>7} {'Quiz':>7} {'Total':>7}")
    print(f"  {'─'*22} {'─'*7} {'─'*7} {'─'*7} {'─'*7}")

    for name, subj_data in data.items():
        n  = len(subj_data.get("notes", []))
        fc = len(subj_data.get("flashcards", []))
        qz = len(subj_data.get("quiz", []))
        short = name[:22]
        print(f"  {short:<22} {n:>7} {fc:>7} {qz:>7} {n+fc+qz:>7}")

    print(f"  {'─'*22} {'─'*7} {'─'*7} {'─'*7} {'─'*7}")
    print(f"  {'TOTAL':<22} {len(all_notes):>7} {len(all_flashcards):>7} {len(all_quizzes):>7} {len(all_notes)+len(all_flashcards)+len(all_quizzes):>7}")
    print(DIVIDER)


def print_output_files():
    """List all generated output files with sizes."""
    print("\n  📁 Output files:")
    for f in sorted(OUTPUT_DIR.iterdir()):
        size_kb = f.stat().st_size / 1024
        print(f"     {f.name:<30} {size_kb:>7.1f} KB")


def main():
    start = time.time()
    print(f"\n{DIVIDER}")
    print("  🚀  CS STUDY HUB — PYTHON AUTOMATION")
    print(f"  Started: {datetime.now().strftime('%B %d, %Y  %I:%M %p')}")
    print(DIVIDER)

    # ── Step 1: Scrape ────────────────────────────────────────────────────────
    print("\n[STEP 1/3]  🌐  Scraping Study Hub...\n")
    data = scraper.scrape()

    if not data:
        print("\n❌ No data scraped. Check your internet connection and try again.")
        sys.exit(1)

    # ── Step 2: Analyze ───────────────────────────────────────────────────────
    print(f"\n[STEP 2/3]  📊  Analyzing content...")
    all_notes      = []
    all_flashcards = []
    all_quizzes    = []
    for subj_data in data.values():
        all_notes.extend(subj_data.get("notes", []))
        all_flashcards.extend(subj_data.get("flashcards", []))
        all_quizzes.extend(subj_data.get("quiz", []))

    print_terminal_summary(data, all_notes, all_flashcards, all_quizzes)

    # ── Step 3: Export ────────────────────────────────────────────────────────
    print(f"\n[STEP 3/3]  💾  Generating reports...\n")
    reporter.generate(data)

    # ── Done ──────────────────────────────────────────────────────────────────
    elapsed = time.time() - start
    print_output_files()
    print(f"\n{DIVIDER}")
    print(f"  ✅  Done in {elapsed:.1f}s")
    print(f"  📂  {OUTPUT_DIR.resolve()}")
    print(DIVIDER)
    print()


if __name__ == "__main__":
    main()
