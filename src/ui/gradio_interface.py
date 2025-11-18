"""
Gradio UI for Signal Statistics System
"""
import gradio as gr
import pandas as pd
import asyncio
from typing import List, Tuple
from datetime import datetime

from ..models.signal import SignalTarget, SignalCondition, ExchangeType, SignalStatus
from ..models.channel import Channel
from ..services.channel_manager import ChannelManager
from ..services.stats_calculator import StatsCalculator
from ..storage.json_storage import JSONStorage


class SignalStatisticsUI:
    """Gradio UI for managing signals and viewing statistics"""

    def __init__(self, storage_path: str = "data/signals.json"):
        """Initialize UI with storage"""
        self.storage = JSONStorage(storage_path)
        self.channel_manager = ChannelManager(self.storage)
        self.stats_calculator = StatsCalculator(self.storage)

    def _run_async(self, coro):
        """Helper to run async coroutines in Gradio"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    async def add_signal_async(
        self,
        name: str,
        channel_name: str,
        symbol: str,
        exchange: str,
        target_price: float,
        take_profit: float,
        stop_loss: float,
        condition: str
    ) -> str:
        """Add new signal to the system"""
        try:
            # Validate inputs
            if not name or not channel_name or not symbol:
                return "❌ Error: Name, Channel Name, and Symbol are required!"

            if take_profit <= 0 or stop_loss <= 0:
                return "❌ Error: Take Profit and Stop Loss must be positive!"

            if take_profit <= stop_loss:
                return "❌ Error: Take Profit must be greater than Stop Loss!"

            # Check if channel exists, if not create it
            existing_channel = await self.channel_manager.get_channel(channel_name)
            if not existing_channel:
                await self.channel_manager.add_channel(
                    name=channel_name,
                    description=f"Auto-created for signal: {name}"
                )

            # Create signal
            signal = SignalTarget(
                name=name,
                symbol=symbol.upper(),
                exchange=ExchangeType(exchange) if exchange else None,
                target_price=target_price if target_price > 0 else take_profit,
                condition=SignalCondition(condition),
                channel_name=channel_name,
                take_profit=take_profit,
                stop_loss=stop_loss
            )

            # Save signal
            success = await self.storage.save_signal(signal)

            if success:
                return f"✅ Signal '{name}' added successfully for channel '{channel_name}'!"
            else:
                return "❌ Error: Failed to save signal"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def add_signal(
        self,
        name: str,
        channel_name: str,
        symbol: str,
        exchange: str,
        target_price: float,
        take_profit: float,
        stop_loss: float,
        condition: str
    ) -> Tuple[str, pd.DataFrame, pd.DataFrame]:
        """Add signal and return updated UI"""
        result = self._run_async(
            self.add_signal_async(
                name, channel_name, symbol, exchange,
                target_price, take_profit, stop_loss, condition
            )
        )

        # Update displays
        signals_df = self.get_active_signals()
        channels_df = self.get_channel_statistics()

        return result, signals_df, channels_df

    async def get_active_signals_async(self) -> pd.DataFrame:
        """Get all active signals as DataFrame"""
        try:
            all_signals = await self.storage.load_signals()
            active_signals = [
                s for s in all_signals
                if s.status != SignalStatus.CLOSED
            ]

            if not active_signals:
                return pd.DataFrame({
                    "Name": [],
                    "Channel": [],
                    "Symbol": [],
                    "TP": [],
                    "SL": [],
                    "Status": [],
                    "Outcome": []
                })

            data = []
            for signal in active_signals:
                data.append({
                    "Name": signal.name,
                    "Channel": signal.channel_name,
                    "Symbol": signal.symbol,
                    "TP": f"${signal.take_profit:.2f}",
                    "SL": f"${signal.stop_loss:.2f}",
                    "Status": signal.status.value,
                    "Outcome": signal.outcome.value
                })

            return pd.DataFrame(data)

        except Exception as e:
            return pd.DataFrame({"Error": [str(e)]})

    def get_active_signals(self) -> pd.DataFrame:
        """Sync wrapper for get_active_signals_async"""
        return self._run_async(self.get_active_signals_async())

    async def get_channel_statistics_async(self) -> pd.DataFrame:
        """Get channel statistics as DataFrame"""
        try:
            # Update all statistics first
            await self.stats_calculator.update_all_statistics()

            # Get channels with stats
            channels_with_stats = await self.channel_manager.get_all_channels_with_stats()

            if not channels_with_stats:
                return pd.DataFrame({
                    "Channel": [],
                    "Total Signals": [],
                    "Active": [],
                    "Closed": [],
                    "Wins": [],
                    "Losses": [],
                    "Winrate": []
                })

            data = []
            for channel, stats in channels_with_stats:
                data.append({
                    "Channel": channel.name,
                    "Total Signals": stats.total_signals,
                    "Active": stats.active_signals,
                    "Closed": stats.closed_signals,
                    "Wins": stats.wins,
                    "Losses": stats.losses,
                    "Winrate": f"{stats.winrate:.1f}%"
                })

            return pd.DataFrame(data)

        except Exception as e:
            return pd.DataFrame({"Error": [str(e)]})

    def get_channel_statistics(self) -> pd.DataFrame:
        """Sync wrapper for get_channel_statistics_async"""
        return self._run_async(self.get_channel_statistics_async())

    async def get_summary_statistics_async(self) -> str:
        """Get overall summary statistics"""
        try:
            summary = await self.stats_calculator.get_summary_stats()

            text = "📊 **Overall Statistics**\n\n"
            text += f"Total Channels: {summary['total_channels']}\n"
            text += f"Total Signals: {summary['total_signals']}\n"
            text += f"Total Wins: {summary['total_wins']}\n"
            text += f"Total Losses: {summary['total_losses']}\n"
            text += f"Overall Winrate: **{summary['overall_winrate']:.1f}%**\n\n"

            if summary.get('best_channel'):
                best = summary['best_channel']
                text += f"🏆 **Best Channel:** {best['name']}\n"
                text += f"   Winrate: {best['winrate']:.1f}% ({best['wins']}W/{best['losses']}L)\n\n"

            if summary.get('worst_channel'):
                worst = summary['worst_channel']
                text += f"📉 **Worst Channel:** {worst['name']}\n"
                text += f"   Winrate: {worst['winrate']:.1f}% ({worst['wins']}W/{worst['losses']}L)\n"

            return text

        except Exception as e:
            return f"Error: {str(e)}"

    def get_summary_statistics(self) -> str:
        """Sync wrapper for get_summary_statistics_async"""
        return self._run_async(self.get_summary_statistics_async())

    def refresh_all(self) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
        """Refresh all UI components"""
        signals_df = self.get_active_signals()
        channels_df = self.get_channel_statistics()
        summary = self.get_summary_statistics()
        return signals_df, channels_df, summary

    async def get_existing_channels_async(self) -> List[str]:
        """Get list of existing channel names"""
        try:
            channels = await self.channel_manager.get_all_channels()
            return [ch.name for ch in channels] if channels else []
        except:
            return []

    def get_existing_channels(self) -> List[str]:
        """Sync wrapper for get_existing_channels_async"""
        return self._run_async(self.get_existing_channels_async())

    def create_interface(self) -> gr.Blocks:
        """Create and return Gradio interface"""
        with gr.Blocks(title="Signal Statistics System", theme=gr.themes.Soft()) as interface:
            gr.Markdown("# 📊 Telegram Signals Statistics System")
            gr.Markdown("Track and analyze trading signals from Telegram channels")

            with gr.Tabs():
                # Tab 1: Add Signal
                with gr.Tab("➕ Add Signal"):
                    gr.Markdown("### Add New Trading Signal")

                    with gr.Row():
                        with gr.Column():
                            signal_name = gr.Textbox(
                                label="Signal Name",
                                placeholder="e.g., BTC Long Position",
                                info="Descriptive name for this signal"
                            )
                            channel_name = gr.Textbox(
                                label="Telegram Channel Name",
                                placeholder="e.g., Crypto VIP Signals",
                                info="Name of the Telegram channel (required)"
                            )
                            symbol = gr.Textbox(
                                label="Trading Symbol",
                                placeholder="e.g., BTCUSDT",
                                info="Must be uppercase (5-15 characters)"
                            )

                        with gr.Column():
                            exchange = gr.Dropdown(
                                choices=["binance", "bybit", "coinbase"],
                                label="Exchange",
                                value="binance",
                                info="Target exchange (optional)"
                            )
                            condition = gr.Dropdown(
                                choices=["above", "below", "equal"],
                                label="Entry Condition",
                                value="above",
                                info="Price condition for entry"
                            )
                            target_price = gr.Number(
                                label="Target Price (Optional)",
                                value=0,
                                info="Entry price target (0 = use TP as target)"
                            )

                    with gr.Row():
                        take_profit = gr.Number(
                            label="Take Profit (TP)",
                            info="Exit price for profit (WIN)"
                        )
                        stop_loss = gr.Number(
                            label="Stop Loss (SL)",
                            info="Exit price for loss (LOSS)"
                        )

                    add_btn = gr.Button("Add Signal", variant="primary")
                    result_text = gr.Textbox(label="Result", interactive=False)

                # Tab 2: Active Signals
                with gr.Tab("📋 Active Signals"):
                    gr.Markdown("### Currently Active Signals")
                    signals_table = gr.Dataframe(
                        value=self.get_active_signals(),
                        label="Active Signals",
                        interactive=False
                    )
                    refresh_signals_btn = gr.Button("🔄 Refresh")

                # Tab 3: Channel Statistics
                with gr.Tab("📊 Channel Statistics"):
                    gr.Markdown("### Winrate by Channel")
                    channels_table = gr.Dataframe(
                        value=self.get_channel_statistics(),
                        label="Channel Performance",
                        interactive=False
                    )
                    summary_text = gr.Markdown(value=self.get_summary_statistics())
                    refresh_stats_btn = gr.Button("🔄 Refresh Statistics")

            # Event handlers
            add_btn.click(
                fn=self.add_signal,
                inputs=[
                    signal_name, channel_name, symbol, exchange,
                    target_price, take_profit, stop_loss, condition
                ],
                outputs=[result_text, signals_table, channels_table]
            )

            refresh_signals_btn.click(
                fn=lambda: self.get_active_signals(),
                outputs=[signals_table]
            )

            refresh_stats_btn.click(
                fn=self.refresh_all,
                outputs=[signals_table, channels_table, summary_text]
            )

        return interface

    def launch(self, **kwargs):
        """Launch the Gradio interface"""
        interface = self.create_interface()
        interface.launch(**kwargs)


def create_ui(storage_path: str = "data/signals.json"):
    """Factory function to create UI"""
    ui = SignalStatisticsUI(storage_path)
    return ui.create_interface()
