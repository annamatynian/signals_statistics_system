# Это файл src/services/signal_manager.py

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone

# --- Импорты ваших моделей и сервисов ---
from ..models.signal import SignalTarget, SignalResult, SignalCondition, SignalStatus, SignalOutcome
from .price_checker import PriceChecker
from ..storage.base import StorageBase

logger = logging.getLogger(__name__)

class SignalManager:
    """
    Главный сервис, который управляет жизненным циклом сигналов:
    1. Загружает активные сигналы из хранилища.
    2. Получает актуальные цены с бирж.
    3. Проверяет TP/SL условия для определения win/loss.
    4. Обновляет состояние сигналов с результатами.
    5. (Уведомления удалены - не используются)
    """
    def __init__(
        self,
        price_checker: PriceChecker,
        storage_service: StorageBase,
        stats_calculator=None  # Optional: для автоматического обновления статистики
    ):
        self.price_checker = price_checker
        self.storage = storage_service
        self.stats_calculator = stats_calculator

    async def check_all_signals(self):
        """
        Основной метод для выполнения одного цикла проверки всех сигналов.
        Проверяет TP/SL уровни и определяет win/loss.

        Returns:
            List[SignalResult]: Список результатов проверки для всех активных сигналов
        """
        logger.info("Starting new signal check cycle...")

        # 1. Загружаем все сигналы из хранилища
        try:
            all_signals = await self.storage.load_signals()
        except Exception as e:
            logger.error(f"Failed to load signals from storage: {e}")
            return []

        # Фильтруем только активные и не закрытые сигналы
        active_signals = [
            signal for signal in all_signals
            if signal.can_trigger() and signal.status != SignalStatus.CLOSED
        ]

        if not active_signals:
            logger.info("No active signals to check.")
            return []

        # 2. Группируем сигналы для эффективного получения цен
        signals_to_check = defaultdict(lambda: defaultdict(list))
        for signal in active_signals:
            signals_to_check[signal.exchange][signal.symbol].append(signal)

        # 3. Асинхронно получаем все необходимые цены
        price_tasks = []
        for exchange, symbols in signals_to_check.items():
            price_tasks.append(
                self.price_checker.get_prices_for_exchange(exchange, list(symbols.keys()))
            )

        price_results_list = await asyncio.gather(*price_tasks, return_exceptions=True)

        # Преобразуем в удобный словарь { (exchange, symbol): price }
        current_prices = {}
        for result in price_results_list:
            if isinstance(result, list):
                for price_data in result:
                    key = (price_data.exchange, price_data.symbol)
                    current_prices[key] = price_data.price
            elif isinstance(result, Exception):
                logger.error(f"Error fetching prices: {result}")

        # 4. Проверяем TP/SL условия для каждого сигнала
        all_results = []
        signals_to_close = []  # Сигналы, которые достигли TP или SL
        channels_to_update_stats = set()  # Каналы для обновления статистики

        for signal in active_signals:
            price_key = (signal.exchange, signal.symbol)
            current_price = current_prices.get(price_key)

            if current_price is None:
                logger.warning(
                    f"Could not get price for {signal.symbol} on {signal.exchange}. "
                    f"Skipping signal '{signal.name}'."
                )
                continue

            # Проверяем условия TP и SL
            tp_hit = current_price >= signal.take_profit
            sl_hit = current_price <= signal.stop_loss

            triggered = False
            signal_closed = False

            # Определяем результат
            if tp_hit:
                # Take Profit достигнут = WIN
                logger.info(
                    f"Signal '{signal.name}' HIT TAKE PROFIT! "
                    f"Price: {current_price}, TP: {signal.take_profit}"
                )
                signal.status = SignalStatus.CLOSED
                signal.outcome = SignalOutcome.WIN
                signal.closed_at = datetime.now(timezone.utc)
                signal.active = False
                triggered = True
                signal_closed = True
                channels_to_update_stats.add(signal.channel_name)

            elif sl_hit:
                # Stop Loss достигнут = LOSS
                logger.info(
                    f"Signal '{signal.name}' HIT STOP LOSS! "
                    f"Price: {current_price}, SL: {signal.stop_loss}"
                )
                signal.status = SignalStatus.CLOSED
                signal.outcome = SignalOutcome.LOSS
                signal.closed_at = datetime.now(timezone.utc)
                signal.active = False
                triggered = True
                signal_closed = True
                channels_to_update_stats.add(signal.channel_name)

            # Создаем результат
            result = SignalResult(
                signal=signal,
                current_price=current_price,
                triggered=triggered
            )
            all_results.append(result)

            if signal_closed:
                signals_to_close.append(signal)

        # 5. Обновляем закрытые сигналы в базе данных
        if signals_to_close:
            update_tasks = [
                self.storage.update_signal(signal)
                for signal in signals_to_close
            ]
            await asyncio.gather(*update_tasks, return_exceptions=True)

            logger.info(
                f"Signal check cycle completed. {len(signals_to_close)} signals closed: "
                f"{sum(1 for s in signals_to_close if s.outcome == SignalOutcome.WIN)} wins, "
                f"{sum(1 for s in signals_to_close if s.outcome == SignalOutcome.LOSS)} losses."
            )

            # 6. Обновляем статистику для затронутых каналов
            if self.stats_calculator and channels_to_update_stats:
                for channel_name in channels_to_update_stats:
                    try:
                        await self.stats_calculator.update_channel_statistics(channel_name)
                        logger.info(f"Updated statistics for channel: {channel_name}")
                    except Exception as e:
                        logger.error(f"Failed to update stats for '{channel_name}': {e}")
        else:
            logger.info("Signal check cycle completed. No signals reached TP/SL.")

        return all_results
