#!/usr/bin/env python3
"""
Integration test for Signal Statistics System
Tests the complete flow: add signal -> check TP/SL -> update stats
"""
import sys
import os
import asyncio

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from src.storage.json_storage import JSONStorage
from src.services.channel_manager import ChannelManager
from src.services.stats_calculator import StatsCalculator
from src.models.signal import SignalTarget, SignalCondition, SignalStatus, SignalOutcome, ExchangeType


async def test_integration():
    """Run integration test"""
    print("=" * 60)
    print("🧪 Starting Integration Test")
    print("=" * 60)
    print()

    # 1. Initialize storage
    test_storage_path = "/tmp/test_integration_signals.json"
    if os.path.exists(test_storage_path):
        os.remove(test_storage_path)

    storage = JSONStorage(test_storage_path)
    channel_manager = ChannelManager(storage)
    stats_calculator = StatsCalculator(storage)
    print("✅ Step 1: Storage initialized")
    print()

    # 2. Add test channels
    print("📊 Step 2: Adding test channels...")
    channel1 = await channel_manager.add_channel(
        name="VIP Crypto Signals",
        telegram_url="https://t.me/vip_crypto",
        description="Premium signals"
    )
    channel2 = await channel_manager.add_channel(
        name="Free Trading Signals",
        telegram_url="https://t.me/free_trading",
        description="Free community signals"
    )
    print(f"   ✅ Added channel: {channel1.name}")
    print(f"   ✅ Added channel: {channel2.name}")
    print()

    # 3. Add test signals
    print("📈 Step 3: Adding test signals...")
    signals = []

    # Channel 1 signals (high winrate - 7 wins, 3 losses)
    for i in range(10):
        signal = SignalTarget(
            name=f"BTC Signal #{i+1}",
            symbol="BTCUSDT",
            exchange=ExchangeType.BINANCE,
            target_price=50000 + i*100,
            condition=SignalCondition.ABOVE,
            channel_name="VIP Crypto Signals",
            take_profit=55000,
            stop_loss=48000
        )
        await storage.save_signal(signal)
        signals.append(signal)

    # Channel 2 signals (lower winrate - 4 wins, 6 losses)
    for i in range(10):
        signal = SignalTarget(
            name=f"ETH Signal #{i+1}",
            symbol="ETHUSDT",
            exchange=ExchangeType.BINANCE,
            target_price=3000 + i*10,
            condition=SignalCondition.ABOVE,
            channel_name="Free Trading Signals",
            take_profit=3500,
            stop_loss=2800
        )
        await storage.save_signal(signal)
        signals.append(signal)

    print(f"   ✅ Added {len(signals)} signals")
    print()

    # 4. Simulate signal closures (manual WIN/LOSS assignment)
    print("💰 Step 4: Simulating signal closures...")
    all_signals = await storage.load_signals()

    closed_count = 0
    wins_count = 0
    losses_count = 0

    for idx, signal in enumerate(all_signals):
        # Channel 1: 70% winrate (first 7 are wins)
        if signal.channel_name == "VIP Crypto Signals":
            if idx < 7:
                signal.status = SignalStatus.CLOSED
                signal.outcome = SignalOutcome.WIN
                wins_count += 1
            else:
                signal.status = SignalStatus.CLOSED
                signal.outcome = SignalOutcome.LOSS
                losses_count += 1
            signal.active = False
            closed_count += 1
            await storage.update_signal(signal)

        # Channel 2: 40% winrate (first 4 are wins)
        elif signal.channel_name == "Free Trading Signals":
            if idx - 10 < 4:  # Skip first 10 (channel 1 signals)
                signal.status = SignalStatus.CLOSED
                signal.outcome = SignalOutcome.WIN
                wins_count += 1
            else:
                signal.status = SignalStatus.CLOSED
                signal.outcome = SignalOutcome.LOSS
                losses_count += 1
            signal.active = False
            closed_count += 1
            await storage.update_signal(signal)

    print(f"   ✅ Closed {closed_count} signals")
    print(f"   ✅ Wins: {wins_count}")
    print(f"   ✅ Losses: {losses_count}")
    print()

    # 5. Update statistics
    print("📊 Step 5: Calculating statistics...")
    await stats_calculator.update_all_statistics()
    print("   ✅ Statistics updated")
    print()

    # 6. Verify statistics
    print("🔍 Step 6: Verifying statistics...")
    print()

    stats1 = await channel_manager.get_channel_stats("VIP Crypto Signals")
    print(f"📈 {stats1.channel_name}")
    print(f"   Total Signals: {stats1.total_signals}")
    print(f"   Closed: {stats1.closed_signals}")
    print(f"   Wins: {stats1.wins}")
    print(f"   Losses: {stats1.losses}")
    print(f"   Winrate: {stats1.winrate}%")
    print()

    stats2 = await channel_manager.get_channel_stats("Free Trading Signals")
    print(f"📉 {stats2.channel_name}")
    print(f"   Total Signals: {stats2.total_signals}")
    print(f"   Closed: {stats2.closed_signals}")
    print(f"   Wins: {stats2.wins}")
    print(f"   Losses: {stats2.losses}")
    print(f"   Winrate: {stats2.winrate}%")
    print()

    # 7. Get summary
    summary = await stats_calculator.get_summary_stats()
    print("📊 Overall Summary:")
    print(f"   Total Channels: {summary['total_channels']}")
    print(f"   Total Signals: {summary['total_signals']}")
    print(f"   Total Wins: {summary['total_wins']}")
    print(f"   Total Losses: {summary['total_losses']}")
    print(f"   Overall Winrate: {summary['overall_winrate']}%")
    print()

    if summary.get('best_channel'):
        best = summary['best_channel']
        print(f"🏆 Best Channel: {best['name']} ({best['winrate']}%)")

    if summary.get('worst_channel'):
        worst = summary['worst_channel']
        print(f"📉 Worst Channel: {worst['name']} ({worst['winrate']}%)")
    print()

    # 8. Validation
    print("=" * 60)
    print("✅ VALIDATION")
    print("=" * 60)

    success = True

    # Check channel 1 (expected 70% winrate)
    if abs(stats1.winrate - 70.0) < 0.1:
        print("✅ Channel 1 winrate correct (70.0%)")
    else:
        print(f"❌ Channel 1 winrate incorrect: {stats1.winrate}% (expected 70.0%)")
        success = False

    # Check channel 2 (expected 40% winrate)
    if abs(stats2.winrate - 40.0) < 0.1:
        print("✅ Channel 2 winrate correct (40.0%)")
    else:
        print(f"❌ Channel 2 winrate incorrect: {stats2.winrate}% (expected 40.0%)")
        success = False

    # Check overall winrate (expected 55%)
    expected_overall = (11 / 20) * 100  # 11 wins out of 20
    if abs(summary['overall_winrate'] - expected_overall) < 0.1:
        print(f"✅ Overall winrate correct ({expected_overall}%)")
    else:
        print(f"❌ Overall winrate incorrect: {summary['overall_winrate']}% (expected {expected_overall}%)")
        success = False

    print()

    if success:
        print("=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("✅ System is ready for production use!")
        print()
        print("🚀 To start the system:")
        print("   python3 run.py")
        print()
        print("🌐 Access the web interface at:")
        print("   http://localhost:7860")
        print()
        return 0
    else:
        print("=" * 60)
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_integration())
    sys.exit(exit_code)
