#!/usr/bin/env python3
"""
Simple UI-only launcher without asyncio conflicts
Perfect for testing the interface
"""
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

print("=" * 60)
print("🚀 Signal Statistics System - UI Mode")
print("=" * 60)
print()
print("📊 Web interface starting...")
print("   http://localhost:7860")
print()
print("ℹ️  UI-only mode (no background price checking)")
print("Press Ctrl+C to stop")
print("=" * 60)
print()

from src.ui.gradio_interface import SignalStatisticsUI

# Create and launch UI
ui = SignalStatisticsUI(storage_path="data/signals.json")
ui.launch(
    server_name="0.0.0.0",
    server_port=7860,
    share=False,
    show_error=True
)
