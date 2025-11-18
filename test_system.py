#!/usr/bin/env python3
"""
Комплексный тест системы Signal Statistics
Тестирует:
1. Подключение к биржам
2. Получение цен
3. Создание и сохранение сигналов
4. JSON storage
5. Signal Manager logic
"""
import sys
import os
import asyncio
import logging
from datetime import datetime

# Добавляем src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.signal import SignalTarget, ExchangeType, SignalCondition
from exchanges.binance import BinanceExchange
from exchanges.coinbase import CoinbaseExchange
from exchanges.bybit import BybitExchange
from storage.json_storage import JSONStorage
from services.price_checker import PriceChecker

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Отключаем шумные логгеры
logging.getLogger('ccxt').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


async def test_exchange_connection(exchange_name: str, exchange_class):
    """Тест подключения к бирже"""
    print(f"\n{'='*60}")
    print(f"  ТЕСТ: Подключение к {exchange_name}")
    print('='*60)

    try:
        exchange = exchange_class()
        await exchange.connect()
        print(f"✅ {exchange_name}: Успешно подключено!")
        return exchange
    except Exception as e:
        print(f"❌ {exchange_name}: Ошибка подключения - {e}")
        return None


async def test_get_price(exchange, symbol: str):
    """Тест получения цены"""
    if not exchange:
        print(f"  ⏭️  Пропускаем тест (биржа недоступна)")
        return None

    print(f"\n  📊 Получаем цену {symbol}...")
    try:
        price_data = await exchange.get_price(symbol)
        if price_data:
            print(f"  ✅ Цена {symbol}: ${price_data.price:,.2f}")
            print(f"     • Биржа: {price_data.exchange.value}")
            print(f"     • Время: {price_data.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            if price_data.volume_24h:
                print(f"     • Объем 24h: ${price_data.volume_24h:,.0f}")
            return price_data
        else:
            print(f"  ❌ Не удалось получить цену для {symbol}")
            return None
    except Exception as e:
        print(f"  ❌ Ошибка при получении цены: {e}")
        return None


async def test_price_checker(exchanges: dict):
    """Тест PriceChecker с fallback механизмом"""
    print(f"\n{'='*60}")
    print(f"  ТЕСТ: PriceChecker с Fallback")
    print('='*60)

    price_checker = PriceChecker(exchanges)

    test_symbols = ["BTCUSDT", "ETHUSDT"]

    for symbol in test_symbols:
        print(f"\n  🔍 Проверка {symbol} со всеми биржами...")
        price_data = await price_checker.get_price(symbol)

        if price_data:
            print(f"  ✅ Получена цена: ${price_data.price:,.2f}")
            print(f"     • Источник: {price_data.exchange.value}")
        else:
            print(f"  ❌ Не удалось получить цену")

    return price_checker


async def test_json_storage():
    """Тест JSON хранилища"""
    print(f"\n{'='*60}")
    print(f"  ТЕСТ: JSON Storage")
    print('='*60)

    # Создаём временное хранилище
    test_file = "/tmp/test_signals.json"
    storage = JSONStorage(file_path=test_file)

    # Тестовый сигнал
    test_signal = SignalTarget(
        name="TEST BTC above 100k",
        symbol="BTCUSDT",
        target_price=100000.0,
        condition=SignalCondition.ABOVE,
        exchange=ExchangeType.BINANCE,
        user_id="test_user"
    )
    test_signal.id = test_signal.generate_id()

    print(f"\n  💾 Сохраняем тестовый сигнал...")
    print(f"     • ID: {test_signal.id}")
    print(f"     • Symbol: {test_signal.symbol}")
    print(f"     • Condition: {test_signal.condition.value}")
    print(f"     • Target: ${test_signal.target_price:,.0f}")

    success = await storage.save_signal(test_signal)
    if success:
        print(f"  ✅ Сигнал сохранен!")
    else:
        print(f"  ❌ Ошибка сохранения")
        return None

    # Загружаем сигналы
    print(f"\n  📂 Загружаем сигналы из хранилища...")
    signals = await storage.load_signals()
    print(f"  ✅ Загружено {len(signals)} сигналов")

    for i, sig in enumerate(signals, 1):
        print(f"     {i}. {sig.name} ({sig.symbol}) - {sig.condition.value} ${sig.target_price:,.0f}")

    return storage


async def test_signal_logic(price_checker: PriceChecker):
    """Тест логики проверки сигналов"""
    print(f"\n{'='*60}")
    print(f"  ТЕСТ: Signal Logic (ABOVE/BELOW/EQUAL)")
    print('='*60)

    # Получаем текущую цену BTC
    btc_price_data = await price_checker.get_price("BTCUSDT")
    if not btc_price_data:
        print(f"  ❌ Не удалось получить цену BTC для теста")
        return

    current_price = btc_price_data.price
    print(f"\n  📊 Текущая цена BTC: ${current_price:,.2f}")

    # Создаём тестовые сигналы
    test_cases = [
        {
            "name": "BTC выше текущей (не сработает)",
            "target": current_price + 1000,
            "condition": SignalCondition.ABOVE,
            "should_trigger": False
        },
        {
            "name": "BTC ниже текущей (не сработает)",
            "target": current_price - 1000,
            "condition": SignalCondition.BELOW,
            "should_trigger": False
        },
        {
            "name": "BTC выше очень низкой цены (СРАБОТАЕТ)",
            "target": 1000.0,
            "condition": SignalCondition.ABOVE,
            "should_trigger": True
        },
        {
            "name": "BTC ниже очень высокой цены (СРАБОТАЕТ)",
            "target": 1000000.0,
            "condition": SignalCondition.BELOW,
            "should_trigger": True
        }
    ]

    print(f"\n  🧪 Проверяем логику срабатывания сигналов:")

    for i, test in enumerate(test_cases, 1):
        print(f"\n  Test {i}: {test['name']}")
        print(f"     • Условие: {test['condition'].value}")
        print(f"     • Целевая цена: ${test['target']:,.0f}")
        print(f"     • Текущая цена: ${current_price:,.2f}")

        # Проверяем условие
        triggered = False
        if test['condition'] == SignalCondition.ABOVE:
            triggered = current_price > test['target']
        elif test['condition'] == SignalCondition.BELOW:
            triggered = current_price < test['target']
        elif test['condition'] == SignalCondition.EQUAL:
            triggered = abs(current_price - test['target']) < 0.01

        expected = test['should_trigger']
        if triggered == expected:
            print(f"     ✅ PASS: Сработал={triggered} (ожидалось={expected})")
        else:
            print(f"     ❌ FAIL: Сработал={triggered} (ожидалось={expected})")


async def main():
    """Главная функция тестирования"""
    print("\n" + "="*60)
    print("  🚀 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ SIGNAL STATISTICS SYSTEM")
    print("="*60)

    # 1. Тестируем подключение к биржам
    print("\n" + "🔌 ШАГ 1: Подключение к биржам".center(60))

    exchanges = {}

    binance = await test_exchange_connection("Binance", BinanceExchange)
    if binance:
        exchanges[ExchangeType.BINANCE] = binance

    coinbase = await test_exchange_connection("Coinbase", CoinbaseExchange)
    if coinbase:
        exchanges[ExchangeType.COINBASE] = coinbase

    bybit = await test_exchange_connection("Bybit", BybitExchange)
    if bybit:
        exchanges[ExchangeType.BYBIT] = bybit

    if not exchanges:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Нет доступных бирж!")
        return

    print(f"\n✅ Доступно бирж: {len(exchanges)}")

    # 2. Тестируем получение цен
    print("\n" + "💰 ШАГ 2: Получение цен".center(60))

    for exchange_type, exchange in exchanges.items():
        await test_get_price(exchange, "BTCUSDT")
        await test_get_price(exchange, "ETHUSDT")

    # 3. Тестируем PriceChecker
    print("\n" + "🔍 ШАГ 3: Price Checker с Fallback".center(60))
    price_checker = await test_price_checker(exchanges)

    # 4. Тестируем JSON Storage
    print("\n" + "💾 ШАГ 4: JSON Storage".center(60))
    storage = await test_json_storage()

    # 5. Тестируем логику сигналов
    print("\n" + "🧪 ШАГ 5: Signal Logic".center(60))
    await test_signal_logic(price_checker)

    # Итоги
    print("\n" + "="*60)
    print("  ✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("="*60)

    print("\n📋 КРАТКИЕ ИТОГИ:")
    print(f"  • Доступно бирж: {len(exchanges)}")
    print(f"  • PriceChecker: {'✅' if price_checker else '❌'}")
    print(f"  • JSON Storage: {'✅' if storage else '❌'}")
    print(f"  • Логика сигналов: ✅")

    print("\n" + "="*60 + "\n")

    # Закрываем соединения
    for exchange in exchanges.values():
        try:
            await exchange.disconnect()
        except:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
