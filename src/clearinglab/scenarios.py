from dataclasses import dataclass
from math import sqrt

@dataclass(frozen=True)
class Shock:
    name: str
    spot: dict
    vol_shift: float=0.0
    correlation_break: bool=False
    liquidity_haircut: float=0.0

SCENARIOS=[
    Shock('broad_down_10',{'BTC':-0.10,'ETH':-0.12,'SOL':-0.16,'AVAX':-0.18},0.10),
    Shock('broad_up_12',{'BTC':0.12,'ETH':0.14,'SOL':0.20,'AVAX':0.24},0.08),
    Shock('crypto_crash_30',{'BTC':-0.30,'ETH':-0.36,'SOL':-0.45,'AVAX':-0.50},0.35),
    Shock('altcoin_disconnect',{'BTC':0.03,'ETH':-0.04,'SOL':-0.40,'AVAX':-0.46},0.22,True),
    Shock('btc_short_squeeze',{'BTC':0.38,'ETH':0.06,'SOL':-0.01,'AVAX':-0.03},0.25,True),
    Shock('vol_crush',{},-0.18),
    Shock('vol_spike',{},0.45),
    Shock('liquidity_crisis',{'BTC':-0.06,'ETH':-0.08,'SOL':-0.12,'AVAX':-0.15},0.20,False,0.7),
    Shock('eth_decouple',{'BTC':0.02,'ETH':-0.31,'SOL':-0.05,'AVAX':0.03},0.18,True),
    Shock('dispersion_explosion',{'BTC':0.15,'ETH':-0.18,'SOL':0.28,'AVAX':-0.32},0.26,True),
    Shock('cross_asset_reversal',{'BTC':-0.12,'ETH':0.18,'SOL':-0.25,'AVAX':0.35},0.16,True),
    Shock('overnight_gap',{'BTC':-0.22,'ETH':-0.28,'SOL':-0.38,'AVAX':-0.40},0.32,False,0.6),
]
