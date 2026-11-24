from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

def D(x):
    if isinstance(x, Decimal): return x
    return Decimal(str(x))

@dataclass(frozen=True)
class Instrument:
    instrument_id: str
    underlying: str
    kind: str  # PERP, FUT, CALL, PUT
    strike: Decimal = Decimal('0')
    expiry_day: int = 0
    multiplier: Decimal = Decimal('1')
    tick_size: Decimal = Decimal('0.01')

@dataclass
class Position:
    instrument_id: str
    quantity: Decimal = Decimal('0')
    average_entry: Decimal = Decimal('0')
    realized_pnl: Decimal = Decimal('0')

@dataclass
class Account:
    account_id: str
    cash: Decimal = Decimal('0')
    positions: dict = field(default_factory=dict)
    bankrupt: bool = False

@dataclass(frozen=True)
class Fill:
    event_id: str
    day: int
    account_id: str
    instrument_id: str
    quantity: Decimal
    price: Decimal
    fee: Decimal = Decimal('0')

@dataclass(frozen=True)
class CashEvent:
    event_id: str
    day: int
    account_id: str
    amount: Decimal
    reason: str

@dataclass(frozen=True)
class RiskLimits:
    leverage_cap: float = 8.0
    concentration_surcharge: float = 0.05
    minimum_margin_rate: float = 0.06
    maintenance_fraction: float = 0.65

@dataclass
class RiskReport:
    equity: float
    initial_margin: float
    maintenance_margin: float
    excess_equity: float
    breached: bool
    greeks: dict
    worst_loss: float
    scenario_losses: dict
    gross_notional: float
    diagnostics: dict = field(default_factory=dict)
