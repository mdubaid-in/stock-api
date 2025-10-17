"""
Instruments Management Utility
Handles managing trading symbols for Twelve Data API
"""

from typing import List, Dict, Optional
from log.logging import logger


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
        logger.debug("🗑️ Cleared all instruments")

    def __len__(self) -> int:
        return len(self.instruments)


# Predefined popular Indian stocks (NSE)
POPULAR_INSTRUMENTS = {
    # Nifty 50 stocks
    "RELIANCE": Instrument("RELIANCE", "NSE", "Reliance Industries"),
    "TCS": Instrument("TCS", "NSE", "Tata Consultancy Services"),
    "HDFCBANK": Instrument("HDFCBANK", "NSE", "HDFC Bank"),
    "INFY": Instrument("INFY", "NSE", "Infosys"),
    "ICICIBANK": Instrument("ICICIBANK", "NSE", "ICICI Bank"),
    "HINDUNILVR": Instrument("HINDUNILVR", "NSE", "Hindustan Unilever"),
    "ITC": Instrument("ITC", "NSE", "ITC Limited"),
    "SBIN": Instrument("SBIN", "NSE", "State Bank of India"),
    "BHARTIARTL": Instrument("BHARTIARTL", "NSE", "Bharti Airtel"),
    "KOTAKBANK": Instrument("KOTAKBANK", "NSE", "Kotak Mahindra Bank"),
    "LT": Instrument("LT", "NSE", "Larsen & Toubro"),
    "AXISBANK": Instrument("AXISBANK", "NSE", "Axis Bank"),
    "ASIANPAINT": Instrument("ASIANPAINT", "NSE", "Asian Paints"),
    "MARUTI": Instrument("MARUTI", "NSE", "Maruti Suzuki"),
    "WIPRO": Instrument("WIPRO", "NSE", "Wipro"),
    "TATAMOTORS": Instrument("TATAMOTORS", "NSE", "Tata Motors"),
    "TATASTEEL": Instrument("TATASTEEL", "NSE", "Tata Steel"),
    "SUNPHARMA": Instrument("SUNPHARMA", "NSE", "Sun Pharmaceutical"),
    "TITAN": Instrument("TITAN", "NSE", "Titan Company"),
    "ULTRACEMCO": Instrument("ULTRACEMCO", "NSE", "UltraTech Cement"),
    "BAJFINANCE": Instrument("BAJFINANCE", "NSE", "Bajaj Finance"),
    "TECHM": Instrument("TECHM", "NSE", "Tech Mahindra"),
    "POWERGRID": Instrument("POWERGRID", "NSE", "Power Grid Corporation"),
    "NESTLEIND": Instrument("NESTLEIND", "NSE", "Nestle India"),
    "HCLTECH": Instrument("HCLTECH", "NSE", "HCL Technologies"),
}


def createInstrumentManager(symbols: List[str]) -> InstrumentManager:
    """
    Create instrument manager with predefined symbols

    Args:
        symbols: List of trading symbols

    Returns:
        Configured InstrumentManager instance
    """
    manager = InstrumentManager()

    for symbol in symbols:
        if symbol in POPULAR_INSTRUMENTS:
            instrument = POPULAR_INSTRUMENTS[symbol]
            manager.addInstrument(
                instrument.symbol,
                instrument.exchange,
                instrument.name,
            )
        else:
            # Add as custom NSE symbol
            logger.warning(
                f"⚠️ Symbol '{symbol}' not in popular instruments, adding as NSE stock"
            )
            manager.addInstrument(symbol, "NSE", symbol)

    return manager
