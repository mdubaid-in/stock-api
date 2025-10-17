"""
Instruments Management Utility
Handles managing trading symbols for Twelve Data API
"""

from typing import List, Dict, Optional
from log.logging import logger
from db.mongoClient import mongo_client


class Instrument:
    """Represents a trading instrument for Indian stocks"""

    def __init__(
        self,
        symbol: str,
        exchange: str,
        name: Optional[str] = None,
    ):
        self.symbol = symbol
        self.exchange = exchange  # NSE or BSE
        self.name = name or symbol

    def getSymbolWithExchange(self) -> str:
        """Get symbol in Twelve Data format (SYMBOL.EXCHANGE)"""
        # Twelve Data uses format like: RELIANCE.NSE or TCS.BSE
        return f"{self.symbol}"  # Exchange suffix optional for major stocks

    def __repr__(self) -> str:
        return f"Instrument({self.symbol}, {self.exchange})"


class InstrumentManager:
    """Manages instruments and provides utility methods"""

    def __init__(self):
        self.instruments: List[Instrument] = []

    def addInstrument(
        self,
        symbol: str,
        exchange: str = "NSE",
        name: Optional[str] = None,
    ) -> None:
        """
        Add an instrument to the manager

        Args:
            symbol: Trading symbol (e.g., "RELIANCE", "TCS")
            exchange: Exchange name (NSE or BSE), defaults to NSE
            name: Optional display name
        """
        instrument = Instrument(symbol, exchange, name)
        self.instruments.append(instrument)
        logger.debug(f"➕ Added instrument: {instrument}")

    def getSymbolsList(self) -> List[str]:
        """
        Get list of symbols for Twelve Data API

        Returns:
            List of symbol strings
        """
        return [instrument.getSymbolWithExchange() for instrument in self.instruments]

    def getInstrumentBySymbol(self, symbol: str) -> Optional[Instrument]:
        """
        Get instrument by trading symbol

        Args:
            symbol: Trading symbol to search for

        Returns:
            Instrument if found, None otherwise
        """
        for instrument in self.instruments:
            if instrument.symbol == symbol:
                return instrument
        return None

    def clear(self) -> None:
        """Clear all instruments"""
        self.instruments.clear()
        logger.debug("Cleared all instruments")

    def __len__(self) -> int:
        return len(self.instruments)


def fetchInstrumentsFromMongo() -> List[Dict]:
    """
    Fetch all instruments from MongoDB stockMaster collection

    Returns:
        List of instrument documents from MongoDB
    """
    try:
        stock_master = mongo_client.get_collection("stockMaster")
        instruments = list(stock_master.find({}))
        return instruments
    except Exception as e:
        logger.error(f"Error fetching instruments from MongoDB: {e}")
        return []


def getInstrumentBySymbol(symbol: str) -> Optional[Dict]:
    """
    Get a specific instrument from MongoDB by symbol

    Args:
        symbol: Trading symbol to search for

    Returns:
        Instrument document if found, None otherwise
    """
    try:
        stockMasterCollection = mongo_client.get_collection("stockMaster")
        instrument = stockMasterCollection.find_one({"symbol": symbol})
        if instrument:
            logger.debug(f"Found instrument for symbol: {symbol}")
        else:
            logger.warning(f"No instrument found for symbol: {symbol}")
        return instrument
    except Exception as e:
        logger.error(f"Error fetching instrument for symbol {symbol}: {e}")
        return None


def createInstrumentsForBothExchanges(mongoInstrument: Dict) -> List[Instrument]:
    """
    Create Instrument objects for NSE and BSE based on available exchange IDs

    Args:
        mongoInstrument: Instrument document from MongoDB

    Returns:
        List of Instrument objects (one for each available exchange)
    """
    instruments = []
    symbol = mongoInstrument["symbol"]
    name = mongoInstrument.get("listedName") or mongoInstrument.get("companyName")

    # Add NSE instrument if nseId exists
    if mongoInstrument.get("nseId"):
        instruments.append(Instrument(symbol, "NSE", name))

    # Add BSE instrument if bseId exists
    if mongoInstrument.get("bseId"):
        bse_id = mongoInstrument.get("bseId")
        instruments.append(Instrument(bse_id, "XBOM", name))

    # If no exchange IDs found, add as NSE by default
    if not instruments:
        instruments.append(Instrument(symbol, "NSE", name))
        logger.warning(f"No exchange IDs found for {symbol}, added as NSE")

    return instruments


def createInstrumentManager() -> InstrumentManager:
    """
    Create instrument manager with symbols from MongoDB stockMaster collection
    Returns:
        Configured InstrumentManager instance with both NSE and BSE instruments
    """
    manager = InstrumentManager()

    # Fetch all instruments from MongoDB
    mongoInstruments = fetchInstrumentsFromMongo()
    logger.info(f"Processing {len(mongoInstruments)} instruments from MongoDB")

    for mongoInstrument in mongoInstruments:
        # Always create instruments for both exchanges if available
        instruments = createInstrumentsForBothExchanges(mongoInstrument)
        for instrument in instruments:
            manager.instruments.append(instrument)

    logger.info(
        f" Created instrument manager with {len(manager)} instruments from MongoDB"
    )
    return manager
