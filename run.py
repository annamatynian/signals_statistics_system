#!/usr/bin/env python3
"""
Quick start script for Signal Statistics System
"""
import sys
import os

# Add src to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

if __name__ == "__main__":
    from src.main_new import main
    import asyncio

    print("=" * 60)
    print("🚀 Starting Signal Statistics System...")
    print("=" * 60)
    print()
    print("📊 Access the web interface at:")
    print("   http://localhost:7860")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✅ System stopped")
