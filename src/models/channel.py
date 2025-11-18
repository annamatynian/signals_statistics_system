"""
Channel model for Telegram channels tracking
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Channel(BaseModel):
    """Telegram channel configuration for signal tracking"""
    id: Optional[str] = Field(None, description="Unique channel identifier")
    name: str = Field(..., description="Channel name (required)")
    telegram_url: Optional[str] = Field(None, description="Telegram channel URL")
    description: Optional[str] = Field(None, max_length=500, description="Channel description")

    # Status
    is_active: bool = Field(True, description="Whether channel is active")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def generate_id(self) -> str:
        """
        Generate a unique ID for this channel based on its name.
        Same channel name will always produce the same ID.
        """
        import hashlib
        hash_input = self.name.lower().strip()
        hash_object = hashlib.sha256(hash_input.encode())
        return f"channel#{hash_object.hexdigest()[:16]}"

    class Config:
        """Pydantic config"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChannelStatistics(BaseModel):
    """Statistics for a specific channel"""
    channel_id: str = Field(..., description="Channel identifier")
    channel_name: str = Field(..., description="Channel name")

    # Signal counts
    total_signals: int = Field(0, ge=0, description="Total number of signals")
    active_signals: int = Field(0, ge=0, description="Currently active signals")
    closed_signals: int = Field(0, ge=0, description="Closed signals")

    # Outcomes
    wins: int = Field(0, ge=0, description="Number of winning signals")
    losses: int = Field(0, ge=0, description="Number of losing signals")
    pending: int = Field(0, ge=0, description="Signals still pending")

    # Calculated metrics
    winrate: float = Field(0.0, ge=0.0, le=100.0, description="Win rate percentage")

    # Metadata
    last_updated: datetime = Field(default_factory=datetime.now)

    def calculate_winrate(self) -> float:
        """Calculate winrate percentage"""
        if self.closed_signals == 0:
            return 0.0
        return round((self.wins / self.closed_signals) * 100, 2)

    def update_stats(self):
        """Update calculated statistics"""
        self.winrate = self.calculate_winrate()
        self.last_updated = datetime.now()

    class Config:
        """Pydantic config"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
