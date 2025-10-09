import logging
import sys
from colorlog import ColoredFormatter
from typing import Any
from pathlib import Path
from datetime import datetime


home_dir = Path.home()
log_folder = home_dir / "SocialMediaJobs"
log_folder.mkdir(exist_ok=True)  # Create folder if it doesn't exist
log_file = (
    log_folder / f'social_media_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
)

# Define custom log level for SUCCESS
SUCCESS_LEVEL = 25
logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

# Define custom log level for NOTE
NOTE_LEVEL = 26
logging.addLevelName(NOTE_LEVEL, "NOTE")

LOG_LEVEL = logging.DEBUG
LOGFORMAT = (
    "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
)
# Enhanced format for threaded operations (includes thread info)
LOGFORMAT_THREADED = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s[%(threadName)s] %(message)s%(reset)s"

# Custom color configuration
LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "white",  # Changed from default blue to normal gray/white
    "SUCCESS": "green",  # Custom success level with green color
    "NOTE": "blue",  # Custom highlight level with bright magenta/purple color
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "red",
}

logging.root.setLevel(LOG_LEVEL)
formatter = ColoredFormatter(LOGFORMAT, log_colors=LOG_COLORS)

# Configure stdout to use UTF-8 encoding to handle Unicode characters
if sys.stdout.encoding != "utf-8":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
stream.setFormatter(formatter)


# Create custom logger class with convenience methods
class CustomLogger(logging.Logger):

    def _safe_message(self, message: Any) -> str:
        """Ensure message can be safely encoded for logging"""
        try:
            # Convert any type to string first
            if not isinstance(message, str):
                message = str(message)

            # Try to encode the message to catch potential issues early
            message.encode("utf-8")
            return message
        except (UnicodeEncodeError, AttributeError):
            # If there are encoding issues or other errors, use a safe representation
            try:
                return str(message).encode("utf-8", errors="replace").decode("utf-8")
            except Exception:
                # Fallback for any other unexpected issues
                return repr(message)

    # Log a success message with green color
    def success(self, message: Any, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(SUCCESS_LEVEL):
            safe_message = self._safe_message(message)
            self._log(SUCCESS_LEVEL, safe_message, args, **kwargs)

    # Log a debug message with cyan color
    def debug(self, message: Any, *args: Any, **kwargs: Any) -> None:
        safe_message = self._safe_message(message)
        super().debug(safe_message, *args, **kwargs)

    # Log an info message with white color
    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        safe_message = self._safe_message(message)
        super().info(safe_message, *args, **kwargs)

    # Log a highlighted message with yellow color
    def note(self, message: Any, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(NOTE_LEVEL):
            safe_message = self._safe_message(message)
            self._log(NOTE_LEVEL, safe_message, args, **kwargs)

    # Log a warning message with yellow color
    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        safe_message = self._safe_message(message)
        super().warning(safe_message, *args, **kwargs)

    # Log an error message with red color
    def error(self, message: Any, *args: Any, **kwargs: Any) -> None:
        safe_message = self._safe_message(message)
        super().error(safe_message, *args, **kwargs)

    # Log a critical message with red color
    def critical(self, message: Any, *args: Any, **kwargs: Any) -> None:
        safe_message = self._safe_message(message)
        super().critical(safe_message, *args, **kwargs)

    def enable_threaded_format(self) -> None:
        """Enable threaded logging format for console output"""
        # Update console handler to show thread names
        threaded_formatter = ColoredFormatter(LOGFORMAT_THREADED, log_colors=LOG_COLORS)
        for handler in self.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setFormatter(threaded_formatter)
                break

    def disable_threaded_format(self) -> None:
        """Disable threaded logging format for console output"""
        # Revert console handler to normal format
        normal_formatter = ColoredFormatter(LOGFORMAT, log_colors=LOG_COLORS)
        for handler in self.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setFormatter(normal_formatter)
                break


# Set the custom logger class
logging.setLoggerClass(CustomLogger)
logger: CustomLogger = logging.getLogger("pythonConfig")  # type: ignore
logger.setLevel(LOG_LEVEL)
logger.addHandler(stream)

# Add file handler to the custom logger with UTF-8 encoding
file_handler = logging.FileHandler(log_file, encoding="utf-8")
# Include thread information in file logs for multi-threaded operations
file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s-%(thread)d] - %(message)s"
)
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)
