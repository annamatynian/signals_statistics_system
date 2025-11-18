"""
Channel Manager Service
Manages telegram channels and their metadata
"""
import logging
from typing import List, Optional
from datetime import datetime

from ..models.channel import Channel, ChannelStatistics
from ..storage.base import StorageBase

logger = logging.getLogger(__name__)


class ChannelManager:
    """Service for managing telegram channels"""

    def __init__(self, storage: StorageBase):
        """
        Initialize ChannelManager

        Args:
            storage: Storage backend for persisting channels
        """
        self.storage = storage

    async def add_channel(
        self,
        name: str,
        telegram_url: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Channel]:
        """
        Add a new telegram channel

        Args:
            name: Channel name (required)
            telegram_url: Telegram channel URL (optional)
            description: Channel description (optional)

        Returns:
            Channel object if successful, None otherwise
        """
        try:
            # Check if channel already exists
            existing = await self.storage.get_channel_by_name(name)
            if existing:
                logger.warning(f"Channel '{name}' already exists")
                return None

            # Create new channel
            channel = Channel(
                name=name,
                telegram_url=telegram_url,
                description=description
            )

            # Generate ID
            channel.id = channel.generate_id()

            # Save to storage
            success = await self.storage.save_channel(channel.model_dump())
            if success:
                logger.info(f"Added new channel: {name}")
                return channel
            else:
                logger.error(f"Failed to save channel: {name}")
                return None

        except Exception as e:
            logger.error(f"Error adding channel: {e}")
            return None

    async def get_all_channels(self, active_only: bool = False) -> List[Channel]:
        """
        Get all channels

        Args:
            active_only: If True, return only active channels

        Returns:
            List of Channel objects
        """
        try:
            channels_data = await self.storage.load_channels()
            channels = [Channel.model_validate(ch) for ch in channels_data]

            if active_only:
                channels = [ch for ch in channels if ch.is_active]

            return channels

        except Exception as e:
            logger.error(f"Error loading channels: {e}")
            return []

    async def get_channel(self, name: str) -> Optional[Channel]:
        """
        Get channel by name

        Args:
            name: Channel name

        Returns:
            Channel object if found, None otherwise
        """
        try:
            channel_data = await self.storage.get_channel_by_name(name)
            if channel_data:
                return Channel.model_validate(channel_data)
            return None

        except Exception as e:
            logger.error(f"Error getting channel '{name}': {e}")
            return None

    async def get_channel_stats(self, channel_name: str) -> Optional[ChannelStatistics]:
        """
        Get statistics for a specific channel

        Args:
            channel_name: Channel name

        Returns:
            ChannelStatistics object if found, None otherwise
        """
        try:
            # Get statistics from storage
            stats_data = await self.storage.get_channel_statistics(channel_name)

            if stats_data:
                return ChannelStatistics.model_validate(stats_data)

            # If no stats exist, create empty stats
            return ChannelStatistics(
                channel_id=f"channel#{channel_name}",
                channel_name=channel_name,
                total_signals=0,
                active_signals=0,
                closed_signals=0,
                wins=0,
                losses=0,
                pending=0,
                winrate=0.0
            )

        except Exception as e:
            logger.error(f"Error getting channel stats for '{channel_name}': {e}")
            return None

    async def get_all_channels_with_stats(self) -> List[tuple[Channel, ChannelStatistics]]:
        """
        Get all channels with their statistics

        Returns:
            List of tuples (Channel, ChannelStatistics)
        """
        try:
            channels = await self.get_all_channels()
            result = []

            for channel in channels:
                stats = await self.get_channel_stats(channel.name)
                if stats:
                    result.append((channel, stats))

            return result

        except Exception as e:
            logger.error(f"Error getting channels with stats: {e}")
            return []
