"""
Main entry point for Signal Statistics System
Simplified version without auth and notifications
"""
import sys
import os
import asyncio
import logging

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_ROOT = os.path.join(PROJECT_ROOT, 'src')
if SRC_ROOT not in sys.path:
    sys.path.insert(0, SRC_ROOT)

# Initialize logger early
logger = logging.getLogger(__name__)

from src.storage.json_storage import JSONStorage
from src.services.price_checker import PriceChecker
from src.services.signal_manager import SignalManager
from src.services.stats_calculator import StatsCalculator
from src.models.signal import ExchangeType
from src.exchanges.binance import BinanceExchange
# Bybit optional - requires pybit library
try:
    from src.exchanges.bybit import BybitExchange
    BYBIT_AVAILABLE = True
except ImportError:
    BYBIT_AVAILABLE = False
    print("⚠️ Bybit not available (pybit not installed)")  # use print before logger setup
from src.exchanges.coinbase import CoinbaseExchange
from src.ui.gradio_interface import SignalStatisticsUI
from src.utils.logger import setup_logging
from src.utils.config import load_config


async def check_signals_background(signal_manager: SignalManager, check_interval: int = 60):
    """
    Background task to check signals for TP/SL
    Runs every minute by default
    """
    logger.info("🚀 Starting background signal checker...")

    while True:
        try:
            logger.info("=" * 60)
            logger.info("🔍 Checking signals for TP/SL...")
            logger.info("=" * 60)

            # Check all signals
            results = await signal_manager.check_all_signals()

            logger.info(f"✅ Check completed. Processed {len(results)} signals")

        except Exception as e:
            logger.error(f"❌ Error in background check: {e}", exc_info=True)

        # Wait for next check
        await asyncio.sleep(check_interval)


async def initialize_exchanges(config) -> dict:
    """Initialize exchange adapters"""
    exchanges = {}

    # Binance
    if ExchangeType.BINANCE in config.exchanges:
        try:
            binance_config = config.get_exchange_config(ExchangeType.BINANCE)
            binance = BinanceExchange(
                api_key=binance_config.api_key,
                api_secret=binance_config.api_secret
            )
            await binance.connect()
            exchanges[ExchangeType.BINANCE] = binance
            logger.info("✅ Binance exchange initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Binance: {e}")

    # Bybit (optional - requires pybit)
    if BYBIT_AVAILABLE and ExchangeType.BYBIT in config.exchanges:
        try:
            bybit_config = config.get_exchange_config(ExchangeType.BYBIT)
            bybit = BybitExchange(
                api_key=bybit_config.api_key,
                api_secret=bybit_config.api_secret
            )
            await bybit.connect()
            exchanges[ExchangeType.BYBIT] = bybit
            logger.info("✅ Bybit exchange initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Bybit: {e}")
    elif not BYBIT_AVAILABLE and ExchangeType.BYBIT in config.exchanges:
        logger.warning("⚠️ Bybit requested but pybit not installed - skipping")

    # Coinbase
    if ExchangeType.COINBASE in config.exchanges:
        try:
            coinbase_config = config.get_exchange_config(ExchangeType.COINBASE)
            coinbase = CoinbaseExchange(
                api_key=coinbase_config.api_key,
                api_secret=coinbase_config.api_secret
            )
            await coinbase.connect()
            exchanges[ExchangeType.COINBASE] = coinbase
            logger.info("✅ Coinbase exchange initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Coinbase: {e}")

    if not exchanges:
        logger.warning("⚠️ No exchanges initialized - signals won't be checked for TP/SL")

    return exchanges


async def main():
    """Main entry point"""
    setup_logging(logging.INFO)
    logger.info("=" * 60)
    logger.info("🚀 Signal Statistics System v2.0")
    logger.info("📊 Telegram Channel Winrate Tracker")
    logger.info("=" * 60)

    try:
        # 1. Load configuration
        env_path = os.path.join(PROJECT_ROOT, '.env')
        if os.path.exists(env_path):
            config = load_config(env_path=env_path)
            logger.info("✅ Configuration loaded")
        else:
            logger.warning("⚠️ No .env file found - using defaults")
            config = None

        # 2. Initialize storage
        storage_path = os.path.join(PROJECT_ROOT, 'data', 'signals.json')
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        storage = JSONStorage(storage_path)
        logger.info(f"💾 Storage initialized: {storage_path}")

        # 3. Initialize services
        stats_calculator = StatsCalculator(storage)
        logger.info("✅ Statistics calculator initialized")

        # 4. Initialize exchanges and price checker (optional)
        exchanges = {}
        if config:
            exchanges = await initialize_exchanges(config)

        if exchanges:
            price_checker = PriceChecker(exchanges)
            signal_manager = SignalManager(
                price_checker=price_checker,
                storage_service=storage,
                stats_calculator=stats_calculator
            )
            logger.info("✅ Signal manager initialized with price checking")

            # Start background checker
            asyncio.create_task(
                check_signals_background(signal_manager, check_interval=60)
            )
            logger.info("🔄 Background signal checker started (60s interval)")
        else:
            logger.warning("⚠️ No exchanges available - background checking disabled")

        # 5. Launch Gradio UI
        logger.info("🎨 Launching Gradio UI...")
        ui = SignalStatisticsUI(storage_path=storage_path)

        # Launch with server
        ui.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )

    except KeyboardInterrupt:
        logger.info("⏹️ System stopped by user")
    except Exception as e:
        logger.critical(f"❌ Critical error: {e}", exc_info=True)
    finally:
        logger.info("🛑 Shutting down...")


if __name__ == "__main__":
    asyncio.run(main())
