#!/usr/bin/env python3
"""
Timetable Generator - Main Application Entry Point

A comprehensive desktop application for generating timetables for CSE Department
using PyQt6 with SQLite database backend.

Author: CSE Department
Version: 1.0.0
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.views.main_window import MainWindow
from src.database.database_manager import DatabaseManager


def main():
    """Main application entry point"""

    # QApplication setup
    app = QApplication(sys.argv)
    app.setApplicationName("Timetable Generator")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CSE Department")

    app.setStyle('Fusion')

    # Initialize DB (tables are created inside __init__)
    db_manager = DatabaseManager()
    # NO initialize_database() needed

    # Create and show main window
    main_window = MainWindow()
    main_window.show()

    # Event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
