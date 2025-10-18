"""
Stock Market Data Streaming Application
Streams real-time market data during trading hours (9:15 AM - 3:30 PM IST)
Uses Twelve Data API for Indian stock market data
"""

import time
import signal
import sys
from threading import Thread, Event

from auth.auth import validateApiKey
from utils.marketHours import (
    isMarketOpen,
    getTimeUntilMarketOpen,
    getCurrentTimeIST,
)
from utils.instruments import createInstrumentManager
from log.logging import logger

# ============================================================
# CONFIGURATION - Choose Your Data Source
# ============================================================

# DATA SOURCE SELECTION
USE_WEBSOCKET = False  # <-- Change this to switch between WebSocket and REST API

# Import appropriate manager based on selection
if USE_WEBSOCKET:
    from classes.TwelveDataWebSocket import TwelveDataWebSocket as DataManager
    from classes.TwelveDataWebSocket import healthCheck

    DATA_SOURCE = "WebSocket (Real-time Streaming)"
else:
    from classes.TwelveDataManager import TwelveDataManager as DataManager
    from classes.TwelveDataManager import healthCheck

    DATA_SOURCE = "REST API (Polling)"

# Global state
shutdown_event = Event()


def apiKeyValidationJob():
    """
    API key validation job (runs every hour)

    Checks if the API key is still valid
    """
    while not shutdown_event.is_set():
        # Wait 1 hour between checks
        for _ in range(3600):
            if shutdown_event.is_set():
                return
            time.sleep(1)

        if not shutdown_event.is_set():
            logger.debug("Validating Twelve Data API key...")
            try:
                if not validateApiKey():
                    logger.warning(
                        "  API key validation failed. Please check TWELVEDATA_API_KEY in .env file.\n"
                        "   Get your free API key from: https://twelvedata.com/apikey"
                    )
            except Exception as e:
                logger.error(f"API key validation failed: {e}")


def signalHandler(signal, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"\nReceived signal {signal}. Shutting down gracefully...")
    shutdown_event.set()

    # Force exit after a short delay if threads don't stop
    def force_exit():
        time.sleep(3)  # Give threads 3 seconds to stop
        if not shutdown_event.is_set():
            logger.warning("Forcing exit due to unresponsive threads")
        sys.exit(0)

    # Start force exit thread
    exit_thread = Thread(target=force_exit, daemon=True)
    exit_thread.start()


def main():
    """Main application entry point"""
    logger.info("=" * 70)
    logger.info("Stock Market Data Streaming Application (Twelve Data API)")
    logger.info("=" * 70)
    logger.info(
        f"📅 Current time (IST): {getCurrentTimeIST().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    logger.info(f"Data Source: {DATA_SOURCE}")

    # Register signal handlers
    signal.signal(signal.SIGINT, signalHandler)
    signal.signal(signal.SIGTERM, signalHandler)

    # Validate API key first
    logger.note("Validating Twelve Data API key...")
    if not validateApiKey():
        logger.error("API key validation failed. Please check your .env file.")
        logger.info("Get your free API key from: https://twelvedata.com/apikey")
        sys.exit(1)

    # Check initial market status
    if not isMarketOpen():
        wait_time = getTimeUntilMarketOpen()
        hours = wait_time // 3600
        minutes = (wait_time % 3600) // 60
        logger.info(f"Market is currently closed")
        logger.info(f"Market opens in {hours}h {minutes}m")
        logger.info("Waiting for market to open...")

    # Create instrument manager with configured symbols
    logger.note("Initializing instruments...")
    instrumentManager = createInstrumentManager()
    logger.success(f"Initialized {len(instrumentManager.instruments)} instruments")

    # Initialize data manager (WebSocket or REST API based on configuration)
    data_manager = DataManager(instrumentManager, shutdown_event)

    # Start health check thread
    # health_thread = Thread(target=healthCheck, args=(data_manager,), daemon=True)
    # health_thread.start()

    # Start data fetching (will wait for market hours internally)
    data_thread = Thread(target=data_manager.run, daemon=True)
    data_thread.start()

    # Wait for shutdown
    try:
        while not shutdown_event.is_set():
            time.sleep(0.1)  # Small sleep to prevent busy waiting
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt in main thread")
        shutdown_event.set()

    # Wait for data thread to finish with timeout
    logger.info("Waiting for threads to finish...")
    data_thread.join(timeout=3)  # Give it 3 seconds to finish gracefully

    if data_thread.is_alive():
        logger.warning("Data thread did not stop gracefully, forcing exit")
        # Force stop the data manager
        data_manager.stop()

    # Cleanup
    logger.info("Cleaning up...")
    data_manager.stop()

    logger.info("Application stopped successfully")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
