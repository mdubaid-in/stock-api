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
        name: str,
        company_id: str,
    ):
        self.symbol = symbol
        self.exchange = exchange  # NSE or BSE
        self.name = name
        self.company_id = company_id

    def getSymbolWithExchange(self) -> str:
        """Get symbol in Twelve Data format (SYMBOL.EXCHANGE)"""
        # Twelve Data uses format like: RELIANCE.NSE or TCS.BSE
        return f"{self.symbol}:{self.exchange}"  # Exchange suffix optional for major stocks

    def __repr__(self) -> str:
        return f"Instrument({self.symbol}, {self.exchange})"


class InstrumentManager:
    """Manages instruments and provides utility methods"""

    def __init__(self):
        self.instruments: Dict[str, Instrument] = {}

    def addInstrument(
        self,
        symbol: str,
        exchange: str,
        name: str,
        company_id: str,
    ) -> None:
        """
        Add an instrument to the manager

        Args:
            symbol: Trading symbol (e.g., "RELIANCE", "TCS")
            exchange: Exchange name (NSE or BSE), defaults to NSE
            name: Optional display name
            company_id: Company ID
        """
        instrument = Instrument(symbol, exchange, name, company_id)
        self.instruments[company_id] = instrument

    def getSymbolsList(self) -> List[str]:
        """
        Get list of symbols for Twelve Data API

        Returns:
            List of symbol strings
        """
        return [
            instrument.getSymbolWithExchange()
            for instrument in self.instruments.values()
        ]

    def get_instrument(self, symbol: str) -> Optional[Instrument]:
        """
        Get instrument by symbol

        Args:
            symbol: Symbol to search for

        Returns:
            Instrument if found, None otherwise
        """
        return self.instruments.get(symbol, None)

    def clear(self) -> None:
        """Clear all instruments"""
        self.instruments.clear()

    def __len__(self) -> int:
        return len(self.instruments.values())


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

        return listings
    except Exception as e:
        logger.error(f"Error fetching instruments from MongoDB: {e}")
        return []


def createInstrumentsForBothExchanges(mongoInstrument: Dict) -> List[Instrument]:
    """
    Create Instrument objects from the instruments array in MongoDB document

    Args:
        mongoInstrument: Instrument document from MongoDB with instruments array

    Returns:
        List of Instrument objects from the instruments array
    """
    instruments: Dict[str, Instrument] = {}

    # Get instruments array from the document
    company_id = mongoInstrument.get("_id", "")
    cross_listings = mongoInstrument.get("crossListings", [])

    if cross_listings:
        # Process each instrument in the array
        for instrument_data in cross_listings:
            symbol = instrument_data.get("symbol", "")
            exchange = instrument_data.get("exchange", "NSE")
            name = instrument_data.get("name", "")

            if symbol:
                instruments[symbol] = Instrument(symbol, exchange, name, company_id)
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
        manager.instruments.update(instruments)

    logger.info(
        f"Created instrument manager with {len(manager.instruments)} instruments from MongoDB"
    )
    return manager
