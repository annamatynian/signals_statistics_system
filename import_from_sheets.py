#!/usr/bin/env python3
"""
Import signals from Google Sheets
Bypasses Gradio UI and imports directly into the database
"""
import sys
import os
import asyncio
import logging

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from src.storage.json_storage import JSONStorage
from src.services.sheets_importer import SheetsImporter
from src.services.stats_calculator import StatsCalculator


async def main():
    """Main import function"""
    print("=" * 60)
    print("📥 Google Sheets Signal Importer")
    print("=" * 60)
    print()

    # Check environment variables
    if not os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"):
        print("❌ Error: GOOGLE_SERVICE_ACCOUNT_JSON not set")
        print()
        print("Please set the following environment variables:")
        print("  export GOOGLE_SERVICE_ACCOUNT_JSON='{ ... }'")
        print("  export GOOGLE_SHEETS_SPREADSHEET_ID='your-spreadsheet-id'")
        print()
        return 1

    if not os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID"):
        print("❌ Error: GOOGLE_SHEETS_SPREADSHEET_ID not set")
        print()
        return 1

    # Initialize storage
    storage_path = os.path.join(PROJECT_ROOT, 'data', 'signals.json')
    os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    storage = JSONStorage(storage_path)
    print(f"✅ Storage initialized: {storage_path}")
    print()

    # Initialize importer
    importer = SheetsImporter(storage)

    # Test connection
    print("🔗 Testing Google Sheets connection...")
    if not importer.test_connection():
        print("❌ Failed to connect to Google Sheets")
        print()
        print("Please check:")
        print("  1. GOOGLE_SERVICE_ACCOUNT_JSON is valid")
        print("  2. GOOGLE_SHEETS_SPREADSHEET_ID is correct")
        print("  3. Service account has access to the spreadsheet")
        print()
        return 1

    print("✅ Connection successful!")
    print()

    # Get sheet name from command line or use default
    sheet_name = sys.argv[1] if len(sys.argv) > 1 else "Signals"
    print(f"📊 Reading from sheet: '{sheet_name}'")
    print()

    # Preview signals
    print("👀 Preview of signals in sheet:")
    signals_preview = importer.read_signals_from_sheet(sheet_name)

    if not signals_preview:
        print("❌ No signals found in sheet")
        print()
        print("Make sure your sheet has:")
        print("  - Header row with column names")
        print("  - Required columns: channel_name, symbol, take_profit, stop_loss")
        print()
        return 1

    print(f"Found {len(signals_preview)} signals:")
    for sig in signals_preview[:5]:  # Show first 5
        print(f"  - {sig['name']} ({sig['symbol']}) - {sig['channel_name']}")
    if len(signals_preview) > 5:
        print(f"  ... and {len(signals_preview) - 5} more")
    print()

    # Confirm import
    response = input("📥 Import these signals? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Import cancelled")
        return 0

    print()
    print("📥 Importing signals...")

    # Import signals
    result = await importer.import_signals(
        sheet_name=sheet_name,
        auto_create_channels=True
    )

    print()
    print("=" * 60)
    print("📊 IMPORT RESULTS")
    print("=" * 60)
    print(f"Total rows processed: {result['total_rows']}")
    print(f"Successfully imported: {result['imported']}")
    print(f"Skipped: {result['skipped']}")
    print()

    if result['channels_created']:
        print(f"Channels auto-created: {len(result['channels_created'])}")
        for ch in result['channels_created']:
            print(f"  - {ch}")
        print()

    if result['errors']:
        print(f"Errors ({len(result['errors'])}):")
        for err in result['errors'][:10]:  # Show first 10 errors
            print(f"  - {err}")
        if len(result['errors']) > 10:
            print(f"  ... and {len(result['errors']) - 10} more")
        print()

    if result['success']:
        print("✅ Import completed successfully!")
        print()

        # Update statistics
        print("📊 Updating statistics...")
        stats_calculator = StatsCalculator(storage)
        await stats_calculator.update_all_statistics()
        print("✅ Statistics updated!")
        print()

        # Show summary
        summary = await stats_calculator.get_summary_stats()
        print("📈 Current system state:")
        print(f"  Total channels: {summary['total_channels']}")
        print(f"  Total signals: {summary['total_signals']}")
        print(f"  Active signals: {summary['total_signals'] - summary['total_wins'] - summary['total_losses']}")
        print()

        print("🚀 Done! You can now:")
        print("  1. Run 'python3 run_simple.py' to view in UI")
        print("  2. Check data/signals.json for imported data")
        print()
        return 0
    else:
        print("❌ Import failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
