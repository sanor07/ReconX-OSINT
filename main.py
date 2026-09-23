"""
ReconX – OSINT Intelligence Framework
Entry point for the application.
"""

import sys
import os
import logging

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.dashboard import ReconXDashboard
from utils.logger import setup_logger

def main():
    """Main entry point for ReconX."""
    # Initialize the logging system
    logger = setup_logger()
    logger.info("ReconX OSINT Framework starting up...")

    try:
        app = ReconXDashboard()
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("ReconX terminated by user.")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
