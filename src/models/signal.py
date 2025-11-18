"""
Signal-related data models
"""
import hashlib
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class ExchangeType(str, Enum):
    """Supported exchanges"""
    BINANCE = "binance"
    BYBIT = "bybit"  # Добавлен Bybit
    COINBASE = "coinbase"
    OKEX = "okex"
    KRAKEN = "kraken"


class SignalCondition(str, Enum):
    """Signal trigger conditions"""
    ABOVE = "above"
    BELOW = "below"
    EQUAL = "equal"
    PERCENT_CHANGE = "percent_change"


class SignalStatus(str, Enum):
    """Signal status states"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"
    EXPIRED = "expired"
    CLOSED = "closed"  # Signal closed (win or loss)


class SignalOutcome(str, Enum):
    """Signal final outcome"""
    WIN = "win"
    LOSS = "loss"
    PENDING = "pending"


class TakeProfitTarget(BaseModel):
    """Single take profit target in a ladder"""
    price: float = Field(..., gt=0, description="TP price level")
    percentage: float = Field(..., gt=0, le=100, description="% of position to close at this TP")
    closed_at: Optional[datetime] = Field(None, description="When this TP was hit")
    amount_closed: Optional[float] = Field(None, ge=0, description="Amount closed at this TP (USD/USDT)")


class SignalTarget(BaseModel):
    """Configuration for a price signal"""
    id: Optional[str] = Field(None, description="Unique signal identifier")
    name: str = Field(..., description="Human-readable signal name")
    exchange: Optional[ExchangeType] = Field(None, description="Target exchange (optional - uses available exchange if not specified)")
    symbol: str = Field(..., pattern=r'^[A-Z]{5,15}$', description="Trading pair symbol")
    target_price: float = Field(..., gt=0, description="Target price")
    condition: SignalCondition = Field(..., description="Trigger condition")

    # Statistics tracking fields (NEW)
    channel_name: str = Field(..., description="Telegram channel name")

    # Take profit can be single level or ladder (tp1, tp2, tp3...)
    take_profit: Optional[float] = Field(None, gt=0, description="Single take profit price level (deprecated, use take_profit_targets)")
    take_profit_targets: list[TakeProfitTarget] = Field(default_factory=list, description="TP ladder (tp1, tp2, tp3...)")

    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price level")

    # Optional fields
    percentage_threshold: Optional[float] = Field(None, gt=0, le=100, description="For percent_change condition")
    active: bool = Field(True, description="Whether signal is active")
    max_triggers: Optional[int] = Field(None, gt=0, description="Maximum number of triggers")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    triggered_count: int = Field(0, ge=0)
    last_triggered_at: Optional[datetime] = None

    # Signal outcome tracking (NEW)
    status: SignalStatus = Field(SignalStatus.ACTIVE, description="Current signal status")
    outcome: SignalOutcome = Field(SignalOutcome.PENDING, description="Final outcome (win/loss)")
    closed_at: Optional[datetime] = Field(None, description="When signal was closed")

    # Position tracking (NEW)
    position_open_date: Optional[datetime] = Field(None, description="Position open timestamp")
    position_entry_amount: Optional[float] = Field(None, gt=0, description="Entry amount (USD/USDT)")

    # User context
    user_id: Optional[str] = Field(None, description="User identifier")
    notes: Optional[str] = Field(None, max_length=500, description="User notes")

    @validator('symbol')
    def validate_symbol(cls, v):
        """Validate trading pair symbol format"""
        if not v.isupper():
            raise ValueError('Symbol must be uppercase')
        return v
    
    
    def is_expired(self) -> bool:
        """Check if signal has reached maximum triggers"""
        return (
            self.max_triggers is not None and 
            self.triggered_count >= self.max_triggers
        )
    
    def can_trigger(self) -> bool:
        """Check if signal can be triggered"""
        return (
            self.active and 
            not self.is_expired()
        )
    
    def generate_id(self) -> str:
        """
        Generate a unique, deterministic ID for this signal based on its key attributes.
        Same signal configuration will always produce the same ID.
        """
        # Create string from key attributes
        exchange_str = self.exchange.value if self.exchange else "any"
        components = [
            exchange_str,
            self.symbol,
            self.condition.value,
            str(self.target_price),
            self.user_id or "default"
        ]
        
        # Generate deterministic hash (БЕЗ префикса signal# - он добавится в storage)
        hash_input = "|".join(components)
        hash_object = hashlib.sha256(hash_input.encode())
        return hash_object.hexdigest()[:16]  # Возвращаем только хеш без префикса


class SignalResult(BaseModel):
    """Result of a signal check"""
    signal: SignalTarget
    current_price: float
    triggered: bool
    trigger_reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Additional context
    price_change_percent: Optional[float] = None
    volume_24h: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
