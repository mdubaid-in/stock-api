"""
Market Hours Utility
Handles market timing checks and validations for multiple stock markets
"""

from datetime import datetime
from typing import Tuple, Dict, List
from auth.auth import getClient
from zoneinfo import ZoneInfo
from constants.markets import (
    MARKET_EXCHANGES,
    MARKET_CONFIGS,
    MarketState,
    MarketConfig,
)
from log.logging import logger


def get_timezone(tz_name: str):
    """Get timezone object using available library"""
    return ZoneInfo(tz_name)


def check_market_status(market: str, exchange: str) -> Dict:
    """Check market status using Twelve Data API"""
    try:
        client = getClient()
        # Use market status endpoint if available, otherwise use quote
        try:
            # Try market status endpoint first
            market_state = client.custom_endpoint(
                name="market_state", country=market
            ).as_json()

            if market_state and isinstance(market_state, list):
                for exchange_data in market_state:
                    if exchange_data.get("name") == exchange:
                        return exchange_data

        except Exception as e:
            logger.error(f"Error getting market status: {str(e)}")
            return {"error": "Unable to get market status"}

    except Exception as e:
        return {"error": f"API error: {str(e)}"}


def getCurrentTimeIST() -> datetime:
    """Get current time in IST timezone"""
    timezone = get_timezone("Asia/Kolkata")
    return datetime.now(timezone)


def getMarketCurrentTime(market: str = "India") -> datetime:
    """Get current time in the specified market's timezone"""
    if market not in MARKET_CONFIGS:
        raise ValueError(
            f"Unknown market: {market}. Available markets: {list(MARKET_CONFIGS.keys())}"
        )

    timezone = get_timezone(MARKET_CONFIGS[market].timezone)
    return datetime.now(timezone)


def getMarketState(market: str = "India") -> Dict:
    """
    Get comprehensive market state information

    Args:
        market: Market identifier (India, US, UK, etc.)
        auto_detect_holidays: Whether to automatically detect holidays using Twelve Data API

    Returns:
        Dict containing:
        - state: MarketState enum value
        - is_open: Boolean indicating if market is open for trading
        - current_time: Current time in market timezone
        - market_open_time: Next market open time
        - market_close_time: Next market close time
        - time_until_open: Seconds until market opens (0 if open)
        - time_until_close: Seconds until market closes (0 if closed)
        - reason: Human-readable reason for current state
    """
    if market not in MARKET_CONFIGS:
        raise ValueError(
            f"Unknown market: {market}. Available markets: {list(MARKET_CONFIGS.keys())}"
        )

    config = MARKET_CONFIGS[market]
    now = getMarketCurrentTime(market)
    current_time = now.time()
    weekday = now.weekday()

    # Check if it's a weekend
    if weekday in config.closed_days:
        return {
            "state": MarketState.WEEKEND,
            "is_open": False,
            "current_time": now,
            "market_open_time": _getNextMarketOpen(now, config),
            "market_close_time": None,
            "time_until_open": _getSecondsUntilNextOpen(now, config),
            "time_until_close": 0,
            "reason": "Market closed due to weekend",
            "market_name": config.name,
        }

    # Check market hours
    if config.open_time <= current_time <= config.close_time:
        # Market should be open according to local time - verify with API
        close_time_today = now.replace(
            hour=config.close_time.hour,
            minute=config.close_time.minute,
            second=0,
            microsecond=0,
        )

        # Check with Twelve Data API to verify if market is actually open
        api_verified_open = True
        api_reason = "Market is currently open for trading"

        if market in MARKET_EXCHANGES:
            try:
                # Check all exchanges for the market at once

                exchange = list(MARKET_EXCHANGES[market].keys())[0]
                api_status = check_market_status(market, exchange)
                if "error" not in api_status and api_status.get("success"):
                    exchanges_data = api_status.get("exchanges", [])

                    # Check if any exchange reports market as closed
                    for exchange_data in exchanges_data:
                        exchange_name = exchange_data.get("name", "Unknown")
                        is_market_open = exchange_data.get("is_market_open", True)

                        if not is_market_open:
                            api_verified_open = False
                            api_reason = f"Market closed due to holiday (verified via {exchange_name} API)"
                            break

            except Exception as e:
                logger.error(f"Error checking market status for {market}: {e}")
                # If API check fails, continue with local calculation
                pass

        return {
            "state": MarketState.OPEN if api_verified_open else MarketState.HOLIDAY,
            "is_open": api_verified_open,
            "current_time": now,
            "market_open_time": None,
            "market_close_time": close_time_today,
            "time_until_open": 0,
            "time_until_close": (
                int((close_time_today - now).total_seconds())
                if api_verified_open
                else 0
            ),
            "reason": api_reason,
            "market_name": config.name,
        }

    # Check pre-market hours
    if (
        config.pre_market_start
        and config.pre_market_start <= current_time < config.open_time
    ):
        next_open = now.replace(
            hour=config.open_time.hour,
            minute=config.open_time.minute,
            second=0,
            microsecond=0,
        )
        return {
            "state": MarketState.PRE_MARKET,
            "is_open": False,
            "current_time": now,
            "market_open_time": next_open,
            "market_close_time": None,
            "time_until_open": int((next_open - now).total_seconds()),
            "time_until_close": 0,
            "reason": "Market is in pre-market session",
            "market_name": config.name,
        }

    # Check post-market hours
    if (
        config.post_market_end
        and config.close_time < current_time <= config.post_market_end
    ):
        next_open = _getNextMarketOpen(now, config)
        return {
            "state": MarketState.POST_MARKET,
            "is_open": False,
            "current_time": now,
            "market_open_time": next_open,
            "market_close_time": None,
            "time_until_open": _getSecondsUntilNextOpen(now, config),
            "time_until_close": 0,
            "reason": "Market is in post-market session",
            "market_name": config.name,
        }

    # Market is closed (outside trading hours)
    next_open = _getNextMarketOpen(now, config)
    return {
        "state": MarketState.CLOSED,
        "is_open": False,
        "current_time": now,
        "market_open_time": next_open,
        "market_close_time": None,
        "time_until_open": _getSecondsUntilNextOpen(now, config),
        "time_until_close": 0,
        "reason": "Market is closed outside trading hours",
        "market_name": config.name,
    }


def _getNextMarketOpen(now: datetime, config: MarketConfig) -> datetime:
    """Get the next market open time"""
    next_open = now.replace(
        hour=config.open_time.hour,
        minute=config.open_time.minute,
        second=0,
        microsecond=0,
    )

    # If we're past market close today, move to next day
    if now.time() > config.close_time:
        next_open = next_open.replace(day=next_open.day + 1)

    # Skip weekends and holidays
    while next_open.weekday() in config.closed_days:
        next_open = next_open.replace(day=next_open.day + 1)

    return next_open


def _getSecondsUntilNextOpen(now: datetime, config: MarketConfig) -> int:
    """Calculate seconds until next market open"""
    next_open = _getNextMarketOpen(now, config)
    return int((next_open - now).total_seconds())


def isMarketOpen(market: str = "India") -> bool:
    """
    Check if market is open for trading (main session only)

    Args:
        market: Market identifier

    Returns:
        bool: True if market is open for trading, False otherwise
    """
    market_state = getMarketState(market)
    return market_state["state"] == MarketState.OPEN


def isMarketActive(market: str = "India") -> bool:
    """
    Check if market is active (including pre-market and post-market sessions)

    Args:
        market: Market identifier

    Returns:
        bool: True if market is active (any session), False otherwise
    """
    market_state = getMarketState(market)
    return market_state["state"] in [
        MarketState.OPEN,
        MarketState.PRE_MARKET,
        MarketState.POST_MARKET,
    ]


def getMarketStatusSummary(market: str = "India") -> str:
    """
    Get a human-readable summary of market status

    Args:
        market: Market identifier

    Returns:
        str: Human-readable market status summary
    """
    state_info = getMarketState(market)
    state = state_info["state"]
    reason = state_info["reason"]

    if state == MarketState.OPEN:
        time_until_close = state_info["time_until_close"]
        hours = time_until_close // 3600
        minutes = (time_until_close % 3600) // 60
        return f"[OPEN] {reason}. Closes in {hours}h {minutes}m"

    elif state == MarketState.CLOSED:
        time_until_open = state_info["time_until_open"]
        hours = time_until_open // 3600
        minutes = (time_until_open % 3600) // 60
        return f"[CLOSED] {reason}. Opens in {hours}h {minutes}m"

    elif state == MarketState.PRE_MARKET:
        time_until_open = state_info["time_until_open"]
        minutes = time_until_open // 60
        return f"[PRE-MARKET] {reason}. Opens in {minutes}m"

    elif state == MarketState.POST_MARKET:
        time_until_open = state_info["time_until_open"]
        hours = time_until_open // 3600
        minutes = (time_until_open % 3600) // 60
        return f"[POST-MARKET] {reason}. Opens in {hours}h {minutes}m"

    else:
        return f"[{state.value}] {reason}"


def getTimeUntilMarketOpen(market: str = "India") -> int:
    """
    Calculate seconds until market opens (backward compatibility)

    Note: This function is deprecated. Use getMarketState() instead.

    Returns:
        int: Seconds until market open, 0 if market is currently open
    """
    market_state = getMarketState(market)
    return market_state["time_until_open"]


def getTimeUntilMarketClose(market: str = "India") -> int:
    """
    Calculate seconds until market closes (backward compatibility)

    Note: This function is deprecated. Use getMarketState() instead.

    Returns:
        int: Seconds until market close, 0 if market is closed
    """
    market_state = getMarketState(market)
    return market_state["time_until_close"]


def getMarketHoursForToday(market: str = "India") -> Tuple[datetime, datetime]:
    """
    Get market open and close times for today (backward compatibility)

    Note: This function is deprecated. Use getMarketState() instead.

    Returns:
        Tuple[datetime, datetime]: (market_open, market_close) in market timezone
    """
    if market not in MARKET_CONFIGS:
        raise ValueError(
            f"Unknown market: {market}. Available markets: {list(MARKET_CONFIGS.keys())}"
        )

    config = MARKET_CONFIGS[market]
    now = getMarketCurrentTime(market)

    market_open = now.replace(
        hour=config.open_time.hour,
        minute=config.open_time.minute,
        second=0,
        microsecond=0,
    )

    market_close = now.replace(
        hour=config.close_time.hour,
        minute=config.close_time.minute,
        second=0,
        microsecond=0,
    )

    return market_open, market_close


def getAvailableMarkets() -> List[str]:
    """
    Get list of available markets

    Returns:
        List[str]: List of market identifiers
    """
    return list(MARKET_CONFIGS.keys())


def getMarketInfo(market: str) -> Dict:
    """
    Get information about a specific market

    Args:
        market: Market identifier

    Returns:
        Dict: Market configuration information
    """
    if market not in MARKET_CONFIGS:
        raise ValueError(
            f"Unknown market: {market}. Available markets: {list(MARKET_CONFIGS.keys())}"
        )

    config = MARKET_CONFIGS[market]
    return {
        "name": config.name,
        "timezone": config.timezone,
        "open_time": config.open_time.strftime("%H:%M"),
        "close_time": config.close_time.strftime("%H:%M"),
        "pre_market_start": (
            config.pre_market_start.strftime("%H:%M")
            if config.pre_market_start
            else None
        ),
        "post_market_end": (
            config.post_market_end.strftime("%H:%M") if config.post_market_end else None
        ),
        "closed_days": [
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ][day]
            for day in sorted(config.closed_days)
        ],
    }
