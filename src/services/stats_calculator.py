"""
Statistics Calculator Service
Calculates and updates channel winrate statistics
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from ..models.channel import ChannelStatistics
from ..models.signal import SignalTarget, SignalStatus, SignalOutcome
from ..storage.base import StorageBase

logger = logging.getLogger(__name__)


class StatsCalculator:
    """Service for calculating channel statistics"""

    def __init__(self, storage: StorageBase):
        """
        Initialize StatsCalculator

        Args:
            storage: Storage backend for signals and statistics
        """
        self.storage = storage

    async def calculate_channel_stats(self, channel_name: str) -> Optional[ChannelStatistics]:
        """
        Calculate statistics for a specific channel

        Args:
            channel_name: Channel name

        Returns:
            ChannelStatistics object with calculated stats
        """
        try:
            # Get all signals for this channel
            signals = await self.storage.get_signals_by_channel(channel_name)

            # Initialize counters
            total_signals = len(signals)
            active_signals = 0
            closed_signals = 0
            wins = 0
            losses = 0
            pending = 0

            # Count signals by outcome
            for signal in signals:
                if signal.status == SignalStatus.CLOSED:
                    closed_signals += 1
                    if signal.outcome == SignalOutcome.WIN:
                        wins += 1
                    elif signal.outcome == SignalOutcome.LOSS:
                        losses += 1
                elif signal.status == SignalStatus.ACTIVE:
                    active_signals += 1
                    pending += 1
                else:
                    # TRIGGERED, PAUSED, EXPIRED
                    if signal.outcome == SignalOutcome.PENDING:
                        pending += 1

            # Create statistics object
            stats = ChannelStatistics(
                channel_id=f"channel#{channel_name}",
                channel_name=channel_name,
                total_signals=total_signals,
                active_signals=active_signals,
                closed_signals=closed_signals,
                wins=wins,
                losses=losses,
                pending=pending
            )

            # Calculate winrate
            stats.update_stats()

            logger.info(
                f"Calculated stats for '{channel_name}': "
                f"{total_signals} total, {wins} wins, {losses} losses, "
                f"{stats.winrate}% winrate"
            )

            return stats

        except Exception as e:
            logger.error(f"Error calculating stats for '{channel_name}': {e}")
            return None

    async def update_all_statistics(self) -> bool:
        """
        Recalculate and update statistics for all channels

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all channels
            channels_data = await self.storage.load_channels()

            if not channels_data:
                logger.info("No channels found, nothing to update")
                return True

            # Calculate stats for each channel
            all_stats = {}
            for channel_data in channels_data:
                channel_name = channel_data.get("name")
                if channel_name:
                    stats = await self.calculate_channel_stats(channel_name)
                    if stats:
                        all_stats[channel_name] = stats.model_dump()

            # Save all statistics
            success = await self.storage.save_statistics(all_stats)

            if success:
                logger.info(f"Updated statistics for {len(all_stats)} channels")
                return True
            else:
                logger.error("Failed to save statistics")
                return False

        except Exception as e:
            logger.error(f"Error updating all statistics: {e}")
            return False

    async def update_channel_statistics(self, channel_name: str) -> bool:
        """
        Update statistics for a single channel

        Args:
            channel_name: Channel name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate stats for this channel
            stats = await self.calculate_channel_stats(channel_name)
            if not stats:
                logger.error(f"Failed to calculate stats for '{channel_name}'")
                return False

            # Load existing statistics
            all_stats = await self.storage.load_statistics()

            # Update this channel's stats
            all_stats[channel_name] = stats.model_dump()

            # Save updated statistics
            success = await self.storage.save_statistics(all_stats)

            if success:
                logger.info(f"Updated statistics for '{channel_name}'")
                return True
            else:
                logger.error(f"Failed to save statistics for '{channel_name}'")
                return False

        except Exception as e:
            logger.error(f"Error updating statistics for '{channel_name}': {e}")
            return False

    async def get_summary_stats(self) -> Dict[str, any]:
        """
        Get summary statistics across all channels

        Returns:
            Dictionary with summary stats
        """
        try:
            all_stats = await self.storage.load_statistics()

            summary = {
                "total_channels": len(all_stats),
                "total_signals": 0,
                "total_wins": 0,
                "total_losses": 0,
                "total_pending": 0,
                "overall_winrate": 0.0,
                "best_channel": None,
                "worst_channel": None
            }

            if not all_stats:
                return summary

            best_winrate = 0.0
            worst_winrate = 100.0

            for channel_name, stats_data in all_stats.items():
                summary["total_signals"] += stats_data.get("total_signals", 0)
                summary["total_wins"] += stats_data.get("wins", 0)
                summary["total_losses"] += stats_data.get("losses", 0)
                summary["total_pending"] += stats_data.get("pending", 0)

                winrate = stats_data.get("winrate", 0.0)
                closed = stats_data.get("closed_signals", 0)

                # Only consider channels with at least 5 closed signals
                if closed >= 5:
                    if winrate > best_winrate:
                        best_winrate = winrate
                        summary["best_channel"] = {
                            "name": channel_name,
                            "winrate": winrate,
                            "wins": stats_data.get("wins", 0),
                            "losses": stats_data.get("losses", 0)
                        }
                    if winrate < worst_winrate:
                        worst_winrate = winrate
                        summary["worst_channel"] = {
                            "name": channel_name,
                            "winrate": winrate,
                            "wins": stats_data.get("wins", 0),
                            "losses": stats_data.get("losses", 0)
                        }

            # Calculate overall winrate
            total_closed = summary["total_wins"] + summary["total_losses"]
            if total_closed > 0:
                summary["overall_winrate"] = round(
                    (summary["total_wins"] / total_closed) * 100, 2
                )

            return summary

        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return {}
