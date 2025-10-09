"""
API Keys Manager
Manages multiple API keys with automatic rotation and error handling
"""

from typing import Dict
from dotenv import load_dotenv, dotenv_values
from log.logging import logger
import os


class ENV:
    """Manages environment variables with dynamic loading from .env file"""

    _instance = None

    def __new__(cls):
        """
        This function implements the singleton pattern for the CredentialManager class.
        When a new instance is requested, it checks if an instance already exists in the class variable _instance.
        If not, it creates a new instance using the superclass's __new__ method and sets an _initialized flag to False.
        It then returns the single instance, ensuring only one CredentialManager exists throughout the application.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize CredentialManager and load environment variables"""
        if self._initialized:
            return

        self.envVars: Dict[str, str] = {}
        self._loadEnvVariables()
        self._initialized = True

    def _loadEnvVariables(self) -> Dict[str, str]:
        "Load all environment variables from .env file dynamically."

        try:
            # Reload .env file to get latest values
            load_dotenv(override=True)

            # Get all keys from .env file
            dotenv_path = os.path.join(os.getcwd(), ".env")
            if os.path.exists(dotenv_path):
                # Load variables from .env file
                env_values = dotenv_values(dotenv_path)

                # Load all environment variables from .env and current environment
                for key, value in env_values.items():
                    if value is not None and not key.startswith("_"):
                        # Get from environment (in case it was overridden)
                        env_value = os.getenv(key, value)
                        self.envVars[key] = env_value
                        # Set as instance attribute for direct access
                        setattr(self, key, env_value)
                        type(self).__annotations__[key] = str

            # # Also include any environment variables not in .env
            # for key, value in os.environ.items():
            #     if key not in self.envVars and not key.startswith("_"):
            #         self.envVars[key] = value
            #         setattr(self, key, value)

            logger.note(
                f"Successfully loaded {len(self.envVars)} environment variables"
            )
            return self.envVars

        except Exception as e:
            logger.error(f"Error loading environment variables: {str(e)}")
            raise

    def getEnvVar(self, key: str, default: str = None) -> str:
        "Get a specific environment variable value."
        return self.envVars.get(key, default) or os.getenv(key, default)

    def reloadEnvVariables(self) -> Dict[str, str]:
        "Reload all environment variables from .env file. Useful when .env file has been updated during runtime."
        # Clear existing attributes
        for key in list(self.envVars.keys()):
            if hasattr(self, key):
                delattr(self, key)

        self.envVars.clear()
        return self._loadEnvVariables()

    def __getattr__(self, name: str) -> str:
        "Fallback for accessing environment variables as attributes."
        if name.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        return self.getEnvVar(name)

    def getAllVars(self) -> Dict[str, str]:
        "Get all loaded environment variables."
        return self.envVars.copy()


env = ENV()
