from datetime import time
from typing import Optional
from enum import Enum
from dataclasses import dataclass


MARKET_EXCHANGES = {
    "India": {
        "NSE": {"code": "XNSE", "symbol": "NIFTY50"},
        "BSE": {"code": "XBOM", "symbol": "SENSEX"},
    },
    "US": {
        "NYSE": {"code": "NYSE", "symbol": "AAPL"},
        "NASDAQ": {"code": "NASDAQ", "symbol": "AAPL"},
    },
    "UK": {"LSE": {"code": "LSE", "symbol": "TSCO"}},
}


# Market State Enum
class MarketState(Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    PRE_MARKET = "PRE_MARKET"
    POST_MARKET = "POST_MARKET"
    HOLIDAY = "HOLIDAY"
    WEEKEND = "WEEKEND"


# Market Configuration Class
@dataclass
class MarketConfig:
    """Configuration for a specific market"""

    name: str
    timezone: str
    open_time: time
    close_time: time
    pre_market_start: Optional[time] = None
    post_market_end: Optional[time] = None
    closed_days: set = None

    def __post_init__(self):
        if self.closed_days is None:
            self.closed_days = {5, 6}  # Default: Saturday, Sunday


# Default Market Configurations
MARKET_CONFIGS = {
    "India": MarketConfig(
        name="India (NSE/BSE)",
        timezone="Asia/Kolkata",
        open_time=time(9, 15),  # 9:15 AM
        close_time=time(18, 30),  # 3:30 PM
        pre_market_start=time(9, 0),  # 9:00 AM
        post_market_end=time(19, 0),  # 4:00 PM
        closed_days={5, 6},  # Saturday, Sunday
    ),
    "US": MarketConfig(
        name="US (NYSE/NASDAQ)",
        timezone="America/New_York",
        open_time=time(9, 30),  # 9:30 AM EST
        close_time=time(16, 0),  # 4:00 PM EST
        pre_market_start=time(4, 0),  # 4:00 AM EST
        post_market_end=time(20, 0),  # 8:00 PM EST
        closed_days={5, 6},  # Saturday, Sunday
    ),
    "UK": MarketConfig(
        name="UK (LSE)",
        timezone="Europe/London",
        open_time=time(8, 0),  # 8:00 AM GMT
        close_time=time(16, 30),  # 4:30 PM GMT
        pre_market_start=time(7, 0),  # 7:00 AM GMT
        post_market_end=time(17, 0),  # 5:00 PM GMT
        closed_days={5, 6},  # Saturday, Sunday
    ),
}
