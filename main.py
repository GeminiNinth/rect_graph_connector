"""
Main entry point for the Rectangular Graph Connector application.
"""

import sys
from PyQt5.QtWidgets import QApplication
from rect_graph_connector.gui.main_window import MainWindow


def main():
    """
    Initialize and run the application.

    This function creates the QApplication instance,
    instantiates the main window, and starts the event loop.

    Returns:
        int: Application exit code
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
