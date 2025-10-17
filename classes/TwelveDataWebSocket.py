"""
Twelve Data WebSocket Manager
Manages real-time WebSocket streaming for Indian stocks using Twelve Data API
"""

import time
import json
from threading import Event, Thread
from typing import Optional, List, Dict, Callable
from datetime import datetime

from twelvedata import TDClient
from auth.auth import getClient
from utils.marketHours import (
    isMarketOpen,
    getTimeUntilMarketOpen,
    getCurrentTimeIST,
)
from utils.instruments import InstrumentManager
from log.logging import logger

# WebSocket Configuration
# Grow Plan: 8 WebSocket connections
MAX_WEBSOCKET_CONNECTIONS = 8
MAX_SYMBOLS_PER_CONNECTION = 10  # Recommended limit per connection

# Health check configuration
HEALTH_CHECK_INTERVAL = 60  # seconds
MAX_RECONNECT_ATTEMPTS = 5
INITIAL_RECONNECT_DELAY = 5  # seconds
MAX_RECONNECT_DELAY = 60  # seconds

# Global state - will be set by main.py
shutdown_event = None


class WebSocketConnection:
    """Manages a single WebSocket connection"""

    def __init__(self, client: TDClient, symbols: List[str], connection_id: int):
        self.client = client
        self.symbols = symbols
        self.connection_id = connection_id
        self.ws = None
        self.is_connected = False
        self.last_message_time: Optional[datetime] = None

    def onEvent(self, event: Dict) -> None:
        """
        Handle incoming WebSocket events

        Args:
            event: Event data from WebSocket
        """
        try:
            self.last_message_time = getCurrentTimeIST()

            # Parse event data
            if isinstance(event, dict):
                event_type = event.get("event", "")

                # Handle price update events
                if event_type == "price":
                    symbol = event.get("symbol", "Unknown")
                    price = event.get("price")
                    timestamp = event.get("timestamp")

                    if price:
                        logger.info(
                            f"📊 [WS-{self.connection_id}] {symbol}: Price={price} @ {timestamp}"
                        )

                        # TODO: Save to database here
                        # from db.mongoClient import mongoClient
                        # collection = mongoClient.get_collection('market_data')
                        # collection.insert_one({
                        #     'symbol': symbol,
                        #     'price': price,
                        #     'timestamp': getCurrentTimeIST(),
                        #     'source': 'websocket'
                        # })

                # Handle heartbeat events
                elif event_type == "heartbeat":
                    logger.debug(f"💓 [WS-{self.connection_id}] Heartbeat received")

                # Handle subscribe confirmation
                elif event_type == "subscribe-status":
                    status = event.get("status")
                    logger.info(
                        f"📡 [WS-{self.connection_id}] Subscribe status: {status}"
                    )

                # Handle errors
                elif event_type == "error":
                    error_msg = event.get("message", "Unknown error")
                    logger.error(
                        f"❌ [WS-{self.connection_id}] WebSocket error: {error_msg}"
                    )

                else:
                    logger.debug(f"📨 [WS-{self.connection_id}] Event: {event_type}")

        except Exception as e:
            logger.error(f"[WS-{self.connection_id}] Error processing event: {e}")

    def connect(self) -> bool:
        """
        Establish WebSocket connection

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            logger.note(
                f"📡 [WS-{self.connection_id}] Connecting to WebSocket for symbols: {', '.join(self.symbols)}"
            )

            # Create WebSocket instance
            # Debug: Print symbols to understand the format
            logger.debug(
                f"Symbols being passed: {self.symbols}, type: {type(self.symbols)}"
            )

            # Try different approaches based on the symbols count
            if len(self.symbols) == 1:
                # Single symbol
                self.ws = self.client.websocket(symbol=self.symbols[0])
            elif len(self.symbols) == 2:
                # Two symbols
                self.ws = self.client.websocket(
                    symbol=self.symbols[0], symbol2=self.symbols[1]
                )
            elif len(self.symbols) == 3:
                # Three symbols
                self.ws = self.client.websocket(
                    symbol=self.symbols[0],
                    symbol2=self.symbols[1],
                    symbol3=self.symbols[2],
                )
            elif len(self.symbols) == 4:
                # Four symbols
                self.ws = self.client.websocket(
                    symbol=self.symbols[0],
                    symbol2=self.symbols[1],
                    symbol3=self.symbols[2],
                    symbol4=self.symbols[3],
                )
            elif len(self.symbols) == 5:
                # Five symbols
                self.ws = self.client.websocket(
                    symbol=self.symbols[0],
                    symbol2=self.symbols[1],
                    symbol3=self.symbols[2],
                    symbol4=self.symbols[3],
                    symbol5=self.symbols[4],
                )
            else:
                # Fallback to original approach
                self.ws = self.client.websocket(symbols=self.symbols)

            # Subscribe with event handler
            self.ws.subscribe(self.onEvent)

            # Connect (non-blocking)
            self.ws.connect()

            self.is_connected = True
            self.last_message_time = getCurrentTimeIST()

            logger.success(
                f"✅ [WS-{self.connection_id}] Connected! Streaming {len(self.symbols)} symbols"
            )
            return True

        except Exception as e:
            logger.error(f"[WS-{self.connection_id}] Connection error: {e}")
            self.is_connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect WebSocket"""
        try:
            if self.ws:
                self.ws.disconnect()
                logger.info(f"🔌 [WS-{self.connection_id}] Disconnected")
            self.is_connected = False
        except Exception as e:
            logger.error(f"[WS-{self.connection_id}] Disconnect error: {e}")

    def keepAlive(self) -> None:
        """Keep WebSocket connection alive"""
        while self.is_connected and not self.shutdown_event.is_set():
            # Check if we received messages recently
            if self.last_message_time:
                time_since_last_msg = (
                    getCurrentTimeIST() - self.last_message_time
                ).total_seconds()

                if time_since_last_msg > 300:  # 5 minutes
                    logger.warning(
                        f"⚠️ [WS-{self.connection_id}] No messages for {time_since_last_msg:.0f}s"
                    )

            time.sleep(10)  # Check every 10 seconds


class TwelveDataWebSocket:
    """Manages Twelve Data WebSocket connections for real-time streaming"""

    def __init__(self, instrumentManager: InstrumentManager, shutdown_event: Event):
        self.instrumentManager = instrumentManager
        self.shutdown_event = shutdown_event
        self.client: Optional[TDClient] = None
        self.connections: List[WebSocketConnection] = []
        self.reconnect_attempts = 0
        self.is_running = False
        # Debug: Check the symbols list
        symbols_list = instrumentManager.getSymbolsList()
        logger.debug(
            f"Raw symbols from manager: {symbols_list}, type: {type(symbols_list)}"
        )
        self.symbols = symbols_list

    def createConnections(self) -> bool:
        """
        Create WebSocket connections for all symbols

        Returns:
            bool: True if connections created successfully
        """
        try:
            if not self.symbols:
                logger.error("No symbols to stream")
                return False

            # Split symbols into groups for multiple connections
            symbols_per_connection = min(MAX_SYMBOLS_PER_CONNECTION, len(self.symbols))

            # Calculate how many connections we need
            num_connections = min(
                (len(self.symbols) + symbols_per_connection - 1)
                // symbols_per_connection,
                MAX_WEBSOCKET_CONNECTIONS,
            )

            logger.info(
                f"📊 Creating {num_connections} WebSocket connection(s) for {len(self.symbols)} symbols"
            )

            # Split symbols into chunks
            symbol_chunks = []
            for i in range(num_connections):
                start_idx = i * symbols_per_connection
                end_idx = min(start_idx + symbols_per_connection, len(self.symbols))
                symbol_chunks.append(self.symbols[start_idx:end_idx])

            # Create WebSocket connections
            for idx, symbol_chunk in enumerate(symbol_chunks):
                connection = WebSocketConnection(self.client, symbol_chunk, idx + 1)
                self.connections.append(connection)

            logger.success(
                f"✅ Created {len(self.connections)} WebSocket connection(s)"
            )
            return True

        except Exception as e:
            logger.error(f"Error creating connections: {e}")
            return False

    def connect(self) -> bool:
        """
        Initialize WebSocket connections

        Returns:
            bool: True if all connections successful, False otherwise
        """
        try:
            # Check if market is open
            if not isMarketOpen():
                logger.warning("Market is closed. Waiting for market to open...")
                return False

            # Get Twelve Data client
            logger.note("🔐 Getting Twelve Data client for WebSocket...")
            self.client = getClient()

            if not self.client:
                logger.error("Failed to get Twelve Data client")
                return False

            # Create connections
            if not self.createConnections():
                return False

            # Connect all WebSocket connections
            all_connected = True
            for connection in self.connections:
                if not connection.connect():
                    all_connected = False
                time.sleep(1)  # Small delay between connections

            if all_connected:
                logger.success(
                    f"✅ All {len(self.connections)} WebSocket(s) connected successfully"
                )
                self.is_running = True
                self.reconnect_attempts = 0
                return True
            else:
                logger.error("Some WebSocket connections failed")
                return False

        except Exception as e:
            logger.error(f"Error connecting WebSockets: {e}")
            return False

    def run(self) -> None:
        """Run WebSocket streaming with automatic reconnection"""
        logger.info("Starting Twelve Data WebSocket Manager...")

        while not self.shutdown_event.is_set():
            # Check market hours
            if not isMarketOpen():
                wait_time = getTimeUntilMarketOpen()
                hours = wait_time // 3600
                minutes = (wait_time % 3600) // 60
                logger.info(f"Market closed. Next open in {hours}h {minutes}m")

                # Sleep in chunks to respond to shutdown
                for _ in range(0, wait_time, 10):
                    if self.shutdown_event.is_set():
                        return
                    time.sleep(min(10, wait_time))

                continue

            # Connect
            if not self.connect():
                self.handleReconnect()
                continue

            # Keep connections alive
            try:
                logger.info(
                    "✅ WebSocket streaming active. Receiving real-time data..."
                )

                # Start keep-alive threads for each connection
                threads = []
                for connection in self.connections:
                    thread = Thread(target=connection.keepAlive, daemon=True)
                    thread.start()
                    threads.append(thread)

                # Monitor while market is open
                while (
                    self.is_running
                    and isMarketOpen()
                    and not self.shutdown_event.is_set()
                ):
                    time.sleep(1)

                # Stop threads
                for connection in self.connections:
                    connection.is_connected = False

            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                break

            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                self.handleReconnect()

            # Check if we should continue (market hours)
            if not isMarketOpen():
                logger.info("Market closed. Stopping WebSocket streaming.")
                break

    def handleReconnect(self) -> None:
        """Handle reconnection with exponential backoff"""
        if self.shutdown_event.is_set():
            return

        self.reconnect_attempts += 1

        if self.reconnect_attempts > MAX_RECONNECT_ATTEMPTS:
            logger.error(
                f"❌ Max reconnection attempts ({MAX_RECONNECT_ATTEMPTS}) reached"
            )

            # Reset after waiting
            time.sleep(60)
            self.reconnect_attempts = 0
            return

        # Exponential backoff
        delay = min(
            INITIAL_RECONNECT_DELAY * (2 ** (self.reconnect_attempts - 1)),
            MAX_RECONNECT_DELAY,
        )

        logger.warning(
            f"🔄 Reconnecting in {delay}s (attempt {self.reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS})"
        )

        # Disconnect existing connections
        self.stop()

        for _ in range(int(delay)):
            if self.shutdown_event.is_set():
                return
            time.sleep(1)

    def stop(self) -> None:
        """Stop all WebSocket connections gracefully"""
        self.is_running = False

        for connection in self.connections:
            connection.disconnect()

        self.connections.clear()
        logger.info("All WebSocket connections stopped")


def healthCheck(ws_manager: TwelveDataWebSocket) -> None:
    """Monitor WebSocket health and market hours"""
    while not ws_manager.shutdown_event.is_set():
        time.sleep(HEALTH_CHECK_INTERVAL)

        if ws_manager.shutdown_event.is_set():
            break

        # Check if market should close
        if not isMarketOpen() and ws_manager.is_running:
            logger.info("Market hours ended. Shutting down WebSockets...")
            ws_manager.stop()
            break

        # Check connection health
        if ws_manager.is_running and ws_manager.connections:
            for connection in ws_manager.connections:
                if connection.last_message_time:
                    time_since_last_msg = (
                        getCurrentTimeIST() - connection.last_message_time
                    ).total_seconds()

                    if time_since_last_msg > 180:  # 3 minutes
                        logger.warning(
                            f"⚠️ [WS-{connection.connection_id}] No messages for {time_since_last_msg:.0f}s"
                        )
