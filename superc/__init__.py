# -*- coding: utf-8 -*-
"""
SuperC Termin Bot Package

This package contains the core functionality for the automated appointment 
checking bot for the Aachen Ausländeramt (immigration office).
"""

from .appointment_checker import run_check
from .config import LOCATIONS, LOG_FORMAT

__version__ = "1.0.0"
__all__ = ["run_check", "LOCATIONS", "LOG_FORMAT"]