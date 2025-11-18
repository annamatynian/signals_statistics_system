#!/usr/bin/env python3
"""
Demo data generator for Signal Statistics System
Adds sample signals and channels for testing
"""
import sys
import os
import asyncio
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))

from src.storage.json_storage import JSONStorage
from src.services.channel_manager import ChannelManager
from src.services.stats_calculator import StatsCalculator
from src.models.signal import SignalTarget, SignalCondition, SignalStatus, SignalOutcome, ExchangeType


async def add_demo_data():
    """Add demo data to the system"""
    print("=" * 60)
    print("📊 Adding Demo Data to Signal Statistics System")
    print("=" * 60)
    print()

    # Initialize services
    storage = JSONStorage("data/signals.json")
    channel_manager = ChannelManager(storage)
    stats_calculator = StatsCalculator(storage)

    # Step 1: Add channels
    print("📺 Step 1: Adding demo channels...")
    channels_data = [
        {
            "name": "VIP Crypto Signals",
            "url": "https://t.me/vip_crypto_signals",
            "description": "Premium crypto trading signals with high accuracy"
        },
        {
            "name": "Budget Trading Channel",
            "url": "https://t.me/budget_trading",
            "description": "Free community signals for beginners"
        },
        {
            "name": "Pro Traders Hub",
            "url": "https://t.me/pro_traders_hub",
            "description": "Professional trading strategies"
        }
    ]

    for ch_data in channels_data:
        channel = await channel_manager.add_channel(
            name=ch_data["name"],
            telegram_url=ch_data["url"],
            description=ch_data["description"]
        )
        if channel:
            print(f"   ✅ Added: {channel.name}")

    print()

    # Step 2: Add active signals
    print("📈 Step 2: Adding active signals...")
    active_signals = [
        {
            "name": "BTC Long Position",
            "channel": "VIP Crypto Signals",
            "symbol": "BTCUSDT",
            "tp": 95000,
            "sl": 85000
        },
        {
            "name": "ETH Breakout Trade",
            "channel": "VIP Crypto Signals",
            "symbol": "ETHUSDT",
            "tp": 3800,
            "sl": 3200
        },
        {
            "name": "BNB Scalp",
            "channel": "Budget Trading Channel",
            "symbol": "BNBUSDT",
            "tp": 650,
            "sl": 580
        },
        {
            "name": "SOL Long Setup",
            "channel": "Pro Traders Hub",
            "symbol": "SOLUSDT",
            "tp": 250,
            "sl": 180
        }
    ]

    for sig_data in active_signals:
        signal = SignalTarget(
            name=sig_data["name"],
            symbol=sig_data["symbol"],
            exchange=ExchangeType.BINANCE,
            target_price=sig_data["tp"],
            condition=SignalCondition.ABOVE,
            channel_name=sig_data["channel"],
            take_profit=sig_data["tp"],
            stop_loss=sig_data["sl"]
        )
        await storage.save_signal(signal)
        print(f"   ✅ Added: {sig_data['name']} ({sig_data['channel']})")

    print()

    # Step 3: Add closed signals with results
    print("💰 Step 3: Adding closed signals with results...")

    # VIP Crypto Signals: 7 wins, 3 losses (70% winrate)
    vip_results = [
        ("BTC Moon Shot", "BTCUSDT", 52000, 48000, "win"),
        ("ETH Rally", "ETHUSDT", 3500, 3000, "win"),
        ("BNB Pump", "BNBUSDT", 600, 550, "win"),
        ("ADA Breakout", "ADAUSDT", 1.5, 1.0, "win"),
        ("DOT Long", "DOTUSDT", 40, 30, "win"),
        ("MATIC Trade", "MATICUSDT", 2.0, 1.5, "win"),
        ("LINK Signal", "LINKUSDT", 25, 20, "win"),
        ("XRP Trade", "XRPUSDT", 1.0, 0.8, "loss"),
        ("TRX Signal", "TRXUSDT", 0.15, 0.10, "loss"),
        ("DOGE Trade", "DOGEUSDT", 0.30, 0.20, "loss"),
    ]

    # Budget Trading Channel: 4 wins, 6 losses (40% winrate)
    budget_results = [
        ("BTC Quick", "BTCUSDT", 51000, 49000, "win"),
        ("ETH Scalp", "ETHUSDT", 3300, 3100, "win"),
        ("BNB Day", "BNBUSDT", 580, 560, "win"),
        ("SOL Fast", "SOLUSDT", 200, 180, "win"),
        ("AVAX Loss", "AVAXUSDT", 100, 80, "loss"),
        ("ATOM Bad", "ATOMUSDT", 15, 12, "loss"),
        ("NEAR Miss", "NEARUSDT", 10, 8, "loss"),
        ("FTM Fail", "FTMUSDT", 2.0, 1.5, "loss"),
        ("SAND Down", "SANDUSDT", 3.0, 2.0, "loss"),
        ("MANA Loss", "MANAUSDT", 2.5, 1.8, "loss"),
    ]

    # Pro Traders Hub: 8 wins, 2 losses (80% winrate)
    pro_results = [
        ("BTC Pro", "BTCUSDT", 53000, 49000, "win"),
        ("ETH Pro", "ETHUSDT", 3600, 3200, "win"),
        ("BNB Pro", "BNBUSDT", 620, 580, "win"),
        ("SOL Pro", "SOLUSDT", 220, 190, "win"),
        ("AVAX Pro", "AVAXUSDT", 110, 95, "win"),
        ("ATOM Pro", "ATOMUSDT", 18, 14, "win"),
        ("DOT Pro", "DOTUSDT", 42, 35, "win"),
        ("LINK Pro", "LINKUSDT", 27, 22, "win"),
        ("XRP Bad", "XRPUSDT", 0.95, 0.85, "loss"),
        ("ADA Bad", "ADAUSDT", 1.3, 1.1, "loss"),
    ]

    def add_closed_signals(signals, channel_name):
        count_win = 0
        count_loss = 0
        for name, symbol, tp, sl, outcome in signals:
            signal = SignalTarget(
                name=name,
                symbol=symbol,
                exchange=ExchangeType.BINANCE,
                target_price=tp,
                condition=SignalCondition.ABOVE,
                channel_name=channel_name,
                take_profit=tp,
                stop_loss=sl,
                status=SignalStatus.CLOSED,
                outcome=SignalOutcome.WIN if outcome == "win" else SignalOutcome.LOSS,
                closed_at=datetime.now(),
                active=False
            )
            asyncio.create_task(storage.save_signal(signal))
            if outcome == "win":
                count_win += 1
            else:
                count_loss += 1
        return count_win, count_loss

    wins, losses = add_closed_signals(vip_results, "VIP Crypto Signals")
    print(f"   ✅ VIP Crypto Signals: {wins}W/{losses}L")

    wins, losses = add_closed_signals(budget_results, "Budget Trading Channel")
    print(f"   ✅ Budget Trading Channel: {wins}W/{losses}L")

    wins, losses = add_closed_signals(pro_results, "Pro Traders Hub")
    print(f"   ✅ Pro Traders Hub: {wins}W/{losses}L")

    # Wait for all signals to be saved
    await asyncio.sleep(1)

    print()

    # Step 4: Calculate statistics
    print("📊 Step 4: Calculating statistics...")
    await stats_calculator.update_all_statistics()
    print("   ✅ Statistics updated")
    print()

    # Step 5: Display results
    print("=" * 60)
    print("📈 DEMO DATA SUMMARY")
    print("=" * 60)
    print()

    for channel_name in ["VIP Crypto Signals", "Budget Trading Channel", "Pro Traders Hub"]:
        stats = await stats_calculator.calculate_channel_stats(channel_name)
        if stats:
            print(f"{channel_name}:")
            print(f"  Total Signals: {stats.total_signals}")
            print(f"  Active: {stats.active_signals}")
            print(f"  Closed: {stats.closed_signals}")
            print(f"  Wins: {stats.wins}")
            print(f"  Losses: {stats.losses}")
            print(f"  Winrate: {stats.winrate}%")
            print()

    summary = await stats_calculator.get_summary_stats()
    print("Overall Summary:")
    print(f"  Total Channels: {summary['total_channels']}")
    print(f"  Total Signals: {summary['total_signals']}")
    print(f"  Total Wins: {summary['total_wins']}")
    print(f"  Total Losses: {summary['total_losses']}")
    print(f"  Overall Winrate: {summary['overall_winrate']}%")
    print()

    if summary.get('best_channel'):
        print(f"🏆 Best Channel: {summary['best_channel']['name']} ({summary['best_channel']['winrate']}%)")
    if summary.get('worst_channel'):
        print(f"📉 Worst Channel: {summary['worst_channel']['name']} ({summary['worst_channel']['winrate']}%)")

    print()
    print("=" * 60)
    print("✅ Demo data added successfully!")
    print("=" * 60)
    print()
    print("🚀 Now run: python3 run.py")
    print("🌐 Then open: http://localhost:7860")


if __name__ == "__main__":
    asyncio.run(add_demo_data())
