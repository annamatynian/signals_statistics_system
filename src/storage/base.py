"""Base Storage Interface"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..models.signal import SignalTarget

class StorageBase(ABC):
    """Base storage interface"""

    # Signal methods
    @abstractmethod
    async def load_signals(self) -> List[SignalTarget]:
        """Load all signals"""
        pass

    @abstractmethod
    async def save_signal(self, signal: SignalTarget) -> bool:
        """Save single signal"""
        pass

    @abstractmethod
    async def delete_signal(self, signal_id: str) -> bool:
        """Delete signal by ID"""
        pass

    @abstractmethod
    async def update_signal(self, signal: SignalTarget) -> bool:
        """Update existing signal"""
        pass

    @abstractmethod
    async def get_signals_by_channel(self, channel_name: str) -> List[SignalTarget]:
        """Get all signals for a specific channel"""
        pass

    # Channel methods
    @abstractmethod
    async def load_channels(self) -> List[Dict[str, Any]]:
        """Load all channels"""
        pass

    @abstractmethod
    async def save_channel(self, channel: Dict[str, Any]) -> bool:
        """Save single channel"""
        pass

    @abstractmethod
    async def get_channel_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get channel by name"""
        pass

    # Statistics methods
    @abstractmethod
    async def load_statistics(self) -> Dict[str, Any]:
        """Load all statistics"""
        pass

    @abstractmethod
    async def save_statistics(self, stats: Dict[str, Any]) -> bool:
        """Save statistics"""
        pass

    @abstractmethod
    async def get_channel_statistics(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific channel"""
        pass

    # User methods (deprecated - kept for backward compatibility)
    @abstractmethod
    async def get_user_data(self, user_id: str) -> Dict[str, Any]:
        """Get user data by ID (deprecated)"""
        pass
