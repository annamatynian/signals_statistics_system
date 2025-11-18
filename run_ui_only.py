#!/usr/bin/env python3
"""
Quick start for testing - UI only (no price checking)
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Signal Statistics System (UI Only Mode)")
    print("=" * 60)
    print()
    print("📊 Access the web interface at:")
    print("   http://localhost:7860")
    print()
    print("ℹ️  Note: Price checking disabled (UI testing mode)")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    from src.ui.gradio_interface import SignalStatisticsUI

    # Create UI with storage
    ui = SignalStatisticsUI(storage_path="data/signals.json")

    # Launch Gradio UI
    ui.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
