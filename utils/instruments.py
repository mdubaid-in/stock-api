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
        return f"{self.symbol}:{self.exchange}"  # Exchange suffix optional for major stocks

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
        listings = list(
            stock_master.find(
                {},
                {
                    "_id": 1,
                    "crossListings.symbol": 1,
                    "crossListings.exchange": 1,
                    "crossListings.name": 1,
                },
            )
        )

        print(listings)
        return listings
    except Exception as e:
        logger.error(f"Error fetching instruments from MongoDB: {e}")
        return []


def getInstrumentBySymbol(symbol: str) -> Optional[Dict]:
    """
    Get a specific instrument from MongoDB by symbol (searches in instruments array)

    Args:
        symbol: Trading symbol to search for

    Returns:
        Instrument document if found, None otherwise
    """
    try:
        stockMasterCollection = mongo_client.get_collection("stockMaster")

        # First try to find by instruments array
        instrument = stockMasterCollection.find_one({"crossListings.symbol": symbol})

        if instrument:
            logger.debug(f"Found instrument for symbol: {symbol}")
            return instrument

        # Fallback to old structure
        instrument = stockMasterCollection.find_one({"symbol": symbol})
        if instrument:
            logger.debug(f"Found instrument for symbol: {symbol} (old structure)")
        else:
            logger.warning(f"No instrument found for symbol: {symbol}")
        return instrument
    except Exception as e:
        logger.error(f"Error fetching instrument for symbol {symbol}: {e}")
        return None


def getInstrumentByTwelveDataSymbol(twelveDataSymbol: str) -> Optional[Dict]:
    """
    Get a specific instrument from MongoDB by Twelve Data symbol

    Args:
        twelveDataSymbol: Twelve Data symbol to search for

    Returns:
        Instrument document if found, None otherwise
    """
    try:
        stockMasterCollection = mongo_client.get_collection("stockMaster")

        # Search by Twelve Data symbol in crossListings array
        instrument = stockMasterCollection.find_one(
            {"crossListings.symbol": twelveDataSymbol}
        )

        if instrument:
            logger.debug(f"Found instrument for Twelve Data symbol: {twelveDataSymbol}")
        else:
            logger.warning(
                f"No instrument found for Twelve Data symbol: {twelveDataSymbol}"
            )
        return instrument
    except Exception as e:
        logger.error(
            f"Error fetching instrument for Twelve Data symbol {twelveDataSymbol}: {e}"
        )
        return None


def createInstrumentsForBothExchanges(mongoInstrument: Dict) -> List[Instrument]:
    """
    Create Instrument objects from the instruments array in MongoDB document

    Args:
        mongoInstrument: Instrument document from MongoDB with instruments array

    Returns:
        List of Instrument objects from the instruments array
    """
    instruments = []

    # Get instruments array from the document
    cross_listings = mongoInstrument.get("crossListings", [])

    if cross_listings:
        # Process each instrument in the array
        for instrument_data in cross_listings:
            symbol = instrument_data.get("symbol", "")
            exchange = instrument_data.get("exchange", "NSE")
            name = instrument_data.get("name", "")

            if symbol:
                instruments.append(Instrument(symbol, exchange, name))
                logger.debug(f"Created instrument: {symbol} on {exchange}")
    else:
        # If no crossListings found, log a warning
        logger.warning(
            f"No crossListings found for document: {mongoInstrument.get('_id', 'unknown')}"
        )

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
        f"Created instrument manager with {len(manager)} instruments from MongoDB"
    )
    return manager
