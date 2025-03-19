"""
Main entry point for the Rectangular Graph Connector application.
"""

import sys
from PyQt5.QtWidgets import QApplication
from rect_graph_connector.gui.main_window import MainWindow
from rect_graph_connector.utils.logging_utils import setup_logging, get_logger


def main() -> int:
    """
    Initialize and run the application.

    This function creates the QApplication instance,
    instantiates the main window, and starts the event loop.

    Returns:
        int: Application exit code
    """
    # Initialize logging
    setup_logging()
    logger = get_logger(__name__)

    logger.info("Starting Rectangular Graph Connector application")

    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        logger.info("Application window initialized and shown")

        exit_code = app.exec_()
        logger.info(f"Application exiting with code: {exit_code}")
        return exit_code

    except Exception as e:
        logger.error(f"Application crashed: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    sys.exit(main())
