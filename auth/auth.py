"""
Twelve Data API Authentication Module
Simple API key-based authentication for Twelve Data
"""

from typing import Optional
from twelvedata import TDClient
from config.env import env
from log.logging import logger


class TwelveDataAuth:
    """Manages Twelve Data API authentication using API key"""

    _instance = None
    _client: Optional[TDClient] = None

    def __new__(cls):
        """Singleton pattern to ensure single authentication instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize authentication manager"""
        if self._initialized:
            return
        self._initialized = True

    def getClient(self) -> Optional[TDClient]:
        """
        Get authenticated Twelve Data client

        Returns:
            Optional[TDClient]: Twelve Data client if successful, None otherwise
        """
        try:
            # Check if client already exists
            if self._client:
                return self._client

            # Get API key from environment
            api_key = env.getEnvVar("TWELVEDATA_API_KEY")

            if not api_key:
                logger.error(
                    " Missing Twelve Data API key. Please set TWELVEDATA_API_KEY in .env file"
                )
                logger.info(
                    "💡 Get your free API key from: https://twelvedata.com/apikey"
                )
                return None

            # Initialize Twelve Data client
            logger.note("🔐 Initializing Twelve Data client...")
            self._client = TDClient(apikey=api_key)

            logger.success("Successfully authenticated with Twelve Data API")
            return self._client

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def validateApiKey(self) -> bool:
        """
        Validate API key by making a test request

        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            client = self.getClient()
            if not client:
                return False

            # Make a simple test request using a reliable free symbol
            logger.note("Validating API key...")
            test_response = client.price(symbol="AAPL")
            result = test_response.as_json()

            if result and "price" in result:
                logger.success("API key is valid")
                return True
            else:
                logger.error("API key validation failed")
                return False

        except Exception as e:
            logger.error(f"API key validation error: {e}")
            return False

    def refreshClient(self) -> Optional[TDClient]:
        """
        Refresh client (recreate instance)

        Returns:
            Optional[TDClient]: New Twelve Data client if successful
        """
        logger.note("Refreshing Twelve Data client...")
        self._client = None
        return self.getClient()


# Global singleton instance
twelveDataAuth = TwelveDataAuth()


def getClient() -> Optional[TDClient]:
    """
    Convenience function to get Twelve Data client

    Returns:
        Optional[TDClient]: Twelve Data client if successful, None otherwise
    """
    return twelveDataAuth.getClient()


def validateApiKey() -> bool:
    """
    Convenience function to validate API key

    Returns:
        bool: True if API key is valid, False otherwise
    """
    return twelveDataAuth.validateApiKey()
