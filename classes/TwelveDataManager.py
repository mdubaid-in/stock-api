"""
Twelve Data Manager
Manages real-time data fetching for Indian stocks using Twelve Data API
"""

import time
from threading import Event, Lock
from typing import Optional, Dict
from datetime import datetime
from collections import deque

from twelvedata import TDClient
from auth.auth import getClient
from utils.marketHours import (
    isMarketOpen,
    getTimeUntilMarketOpen,
    getCurrentTimeIST,
)
from utils.instruments import InstrumentManager
from log.logging import logger

# Rate Limiting Configuration
# Free Plan: 8 API credits per minute (1 request = 1 credit for quote)
# Pro Plan: 800 API credits per minute
# Grow Plan: 55 API credits per minute
# Can be configured based on your plan
RATE_LIMIT_PER_MINUTE = 55  # Grow plan limit
POLLING_INTERVAL = 5

# Health check configuration
HEALTH_CHECK_INTERVAL = 60  # seconds
MAX_RECONNECT_ATTEMPTS = 5
INITIAL_RECONNECT_DELAY = 5  # seconds
MAX_RECONNECT_DELAY = 60  # seconds

# Global state - will be set by main.py
shutdown_event = None


class RateLimiter:
    """Rate limiter to ensure API calls stay within Twelve Data Grow plan limits (55 calls/minute)"""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.minute_calls = deque()
        self.lock = Lock()

    def acquire(self) -> None:
        """
        Acquire permission to make an API call
        Blocks if rate limit would be exceeded
        """
        with self.lock:
            now = time.time()

            # Clean up old entries (older than 60 seconds)
            while self.minute_calls and now - self.minute_calls[0] >= 60.0:
                self.minute_calls.popleft()

            # Check per-minute limit
            if len(self.minute_calls) >= self.per_minute:
                sleep_time = 60.0 - (now - self.minute_calls[0])
                if sleep_time > 0:
                    logger.debug(
                        f"⏱️ Rate limit (per minute): sleeping {sleep_time:.2f}s"
                    )
                    time.sleep(sleep_time)
                    now = time.time()
                    # Clean up again after sleeping
                    while self.minute_calls and now - self.minute_calls[0] >= 60.0:
                        self.minute_calls.popleft()

            # Record this call
            self.minute_calls.append(now)


class TwelveDataManager:
    """Manages Twelve Data API connection with automatic polling and market hours awareness"""

    def __init__(self, instrumentManager: InstrumentManager, shutdown_event: Event):
        self.instrumentManager = instrumentManager
        self.shutdown_event = shutdown_event
        self.client: Optional[TDClient] = None
        self.reconnect_attempts = 0
        self.is_running = False
        self.last_update_time: Optional[datetime] = None
        self.rate_limiter = RateLimiter(RATE_LIMIT_PER_MINUTE)
        self.symbols = instrumentManager.getSymbolsList()

    def fetchData(self) -> None:
        """
        Fetch latest data for all instruments
        """
        try:
            if not self.symbols:
                logger.warning("No symbols to fetch data for")
                return

            # Use rate limiter before API call
            self.rate_limiter.acquire()

            # Fetch quote for symbols (batch if multiple)
            if len(self.symbols) == 1:
                # Single symbol
                symbol = self.symbols[0]
                logger.debug(f"Fetching data for {symbol}...")

                quote = self.client.quote(symbol=symbol)
                result = quote.as_json()

                if result:
                    self.processQuoteData(result)
                    self.last_update_time = getCurrentTimeIST()
            else:
                # Multiple symbols - fetch with optimized rate limiting for Grow plan
                # With 55 calls/minute, we can fetch all 5 symbols quickly
                for symbol in self.symbols:
                    if self.shutdown_event.is_set():
                        break

                    self.rate_limiter.acquire()
                    logger.debug(f"Fetching data for {symbol}...")

                    try:
                        quote = self.client.quote(symbol=symbol)
                        result = quote.as_json()

                        if result:
                            self.processQuoteData(result)
                    except Exception as e:
                        logger.error(f"Error fetching {symbol}: {e}")

                    # Reduced delay for Grow plan - more responsive data
                    time.sleep(0.2)

                self.last_update_time = getCurrentTimeIST()

        except Exception as e:
            logger.error(f"Error fetching data: {e}")

    def processQuoteData(self, data: Dict) -> None:
        """
        Process and log quote data

        Args:
            data: Quote data from Twelve Data API
        """
        try:
            symbol = data.get("symbol", "Unknown")
            price = data.get("close") or data.get("price")
            volume = data.get("volume")
            change = data.get("change")
            percent_change = data.get("percent_change")
            timestamp = data.get("timestamp", "")

            if price:
                logger.info(
                    f"📊 {symbol}: Price={price}, Volume={volume}, "
                    f"Change={change} ({percent_change}%)"
                )

                # TODO: Save to database here
                # from db.mongoClient import mongoClient
                # collection = mongoClient.get_collection('market_data')
                # collection.insert_one({
                #     'symbol': symbol,
                #     'price': price,
                #     'volume': volume,
                #     'change': change,
                #     'percent_change': percent_change,
                #     'timestamp': getCurrentTimeIST()
                # })

        except Exception as e:
            logger.error(f"Error processing quote data: {e}")

    def connect(self) -> bool:
        """
        Initialize Twelve Data client

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Check if market is open
            # if not isMarketOpen():
            #     logger.warning("Market is closed. Waiting for market to open...")
            #     return False

            # Get Twelve Data client
            logger.note(" Getting Twelve Data client...")
            self.client = getClient()

            if not self.client:
                logger.error("Failed to get Twelve Data client")
                return False

            if not self.symbols:
                logger.error("No instruments to track")
                return False

            logger.success(
                f" Successfully connected. Tracking {len(self.symbols)} symbols"
            )

            self.is_running = True
            self.reconnect_attempts = 0
            self.last_update_time = getCurrentTimeIST()

            return True

        except Exception as e:
            logger.error(f"Error connecting: {e}")
            return False

    def run(self) -> None:
        """Run data fetching loop with automatic polling"""
        logger.info("Starting Twelve Data Manager...")

        while not self.shutdown_event.is_set():
            # Check market hours
            # if not isMarketOpen():
            #     wait_time = getTimeUntilMarketOpen()
            #     hours = wait_time // 3600
            #     minutes = (wait_time % 3600) // 60
            #     logger.info(f"Market closed. Next open in {hours}h {minutes}m")

            #     # Sleep in chunks to respond to shutdown
            #     for _ in range(0, wait_time, 10):
            #         if shutdown_event.is_set():
            #             return
            #         time.sleep(min(10, wait_time))

            #     continue

            # Connect
            if not self.connect():
                self.handleReconnect()
                continue

            # Polling loop
            try:
                logger.info("Connected. Starting data polling...")

                while (
                    self.is_running
                    and isMarketOpen()
                    and not self.shutdown_event.is_set()
                ):
                    # Fetch latest data
                    self.fetchData()

                    # Wait for next polling interval
                    for _ in range(POLLING_INTERVAL):
                        if self.shutdown_event.is_set() or not isMarketOpen():
                            break
                        time.sleep(1)

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break

            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                self.handleReconnect()

            # # Check if we should continue (market hours)
            # if not isMarketOpen():
            #     logger.info("Market closed. Stopping data fetching.")
            #     break

    def handleReconnect(self) -> None:
        """Handle reconnection with exponential backoff"""
        if self.shutdown_event.is_set():
            return

        self.reconnect_attempts += 1

        if self.reconnect_attempts > MAX_RECONNECT_ATTEMPTS:
            logger.error(
                f" Max reconnection attempts ({MAX_RECONNECT_ATTEMPTS}) reached"
            )

            # Reset after waiting (with shutdown check)
            for _ in range(60):
                if self.shutdown_event.is_set():
                    return
                time.sleep(1)
            self.reconnect_attempts = 0
            return

        # Exponential backoff
        delay = min(
            INITIAL_RECONNECT_DELAY * (2 ** (self.reconnect_attempts - 1)),
            MAX_RECONNECT_DELAY,
        )

        logger.warning(
            f" Reconnecting in {delay}s (attempt {self.reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS})"
        )

        for _ in range(int(delay)):
            if self.shutdown_event.is_set():
                return
            time.sleep(1)

    def stop(self) -> None:
        """Stop data fetching gracefully"""
        self.is_running = False
        logger.info("Twelve Data Manager stopped")


def healthCheck(manager: TwelveDataManager) -> None:
    """Monitor data fetching health and market hours"""
    while not manager.shutdown_event.is_set():
        time.sleep(HEALTH_CHECK_INTERVAL)

        if manager.shutdown_event.is_set():
            break

        # Check if market should close
        if not isMarketOpen() and manager.is_running:
            logger.info("Market hours ended. Shutting down...")
            manager.stop()
            break

        # Check last update time
        if manager.is_running and manager.last_update_time:
            time_since_last_update = (
                getCurrentTimeIST() - manager.last_update_time
            ).total_seconds()

            if time_since_last_update > 300:  # 5 minutes
                logger.warning(
                    f" No updates received for {time_since_last_update:.0f}s"
                )
