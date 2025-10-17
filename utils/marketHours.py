"""
Market Hours Utility
Handles market timing checks and validations for Indian stock market
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import Tuple

# Indian Stock Market timings (IST)
MARKET_TIMEZONE = ZoneInfo("Asia/Kolkata")
MARKET_OPEN_TIME = time(9, 15)  # 9:15 AM
MARKET_CLOSE_TIME = time(15, 30)  # 3:30 PM

# Days when market is closed (0=Monday, 6=Sunday)
MARKET_CLOSED_DAYS = {5, 6}  # Saturday, Sunday


def getCurrentTimeIST() -> datetime:
    """Get current time in IST timezone"""
    return datetime.now(MARKET_TIMEZONE)


def isMarketOpen() -> bool:
    """
    Check if market is currently open

    Returns:
        bool: True if market is open, False otherwise
    """
    now = getCurrentTimeIST()

    # Check if it's a weekend
    if now.weekday() in MARKET_CLOSED_DAYS:
        return False

    # Check if time is within market hours
    current_time = now.time()
    return MARKET_OPEN_TIME <= current_time <= MARKET_CLOSE_TIME


def getTimeUntilMarketOpen() -> int:
    """
    Calculate seconds until market opens

    Returns:
        int: Seconds until market open, 0 if market is currently open
    """
    if isMarketOpen():
        return 0

    now = getCurrentTimeIST()

    # Find next market open time
    next_open = now.replace(
        hour=MARKET_OPEN_TIME.hour,
        minute=MARKET_OPEN_TIME.minute,
        second=0,
        microsecond=0,
    )

    # If we're past market close today, move to next day
    if now.time() > MARKET_CLOSE_TIME:
        next_open = next_open.replace(day=next_open.day + 1)

    # Skip weekends
    while next_open.weekday() in MARKET_CLOSED_DAYS:
        next_open = next_open.replace(day=next_open.day + 1)

    return int((next_open - now).total_seconds())


def getTimeUntilMarketClose() -> int:
    """
    Calculate seconds until market closes

    Returns:
        int: Seconds until market close, 0 if market is closed
    """
    if not isMarketOpen():
        return 0

    now = getCurrentTimeIST()
    market_close = now.replace(
        hour=MARKET_CLOSE_TIME.hour,
        minute=MARKET_CLOSE_TIME.minute,
        second=0,
        microsecond=0,
    )

    return int((market_close - now).total_seconds())


def getMarketHoursForToday() -> Tuple[datetime, datetime]:
    """
    Get market open and close times for today

    Returns:
        Tuple[datetime, datetime]: (market_open, market_close) in IST
    """
    now = getCurrentTimeIST()

    market_open = now.replace(
        hour=MARKET_OPEN_TIME.hour,
        minute=MARKET_OPEN_TIME.minute,
        second=0,
        microsecond=0,
    )

    market_close = now.replace(
        hour=MARKET_CLOSE_TIME.hour,
        minute=MARKET_CLOSE_TIME.minute,
        second=0,
        microsecond=0,
    )

    return market_open, market_close
