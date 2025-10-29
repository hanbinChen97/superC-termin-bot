"""
PYTHONPATH=. pytest tests/test_appointment_selector.py
"""

import bs4
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, List
from datetime import datetime

from superc.utils.appointment_selector import select_first_appointment, parse_all_appointments

def test_select_first_appointment_from_saved_page():
    # data/debugPage/step_4_term_available_20251003_152049.html
    # Assuming the test is run from the project root.
    html_path = Path("data/debugPage/step_4_term_available_20251003_152049.html")
    if not html_path.exists():
        # If not in root, try to go up from current file.
        html_path = Path(__file__).resolve().parent.parent / "data/debugPage/step_4_term_available_20251003_152049.html"

    if not html_path.exists():
        print(f"Test file not found at {html_path}, skipping test.")
        return

    suggest_html = html_path.read_text(encoding="utf-8")

    success, message, form_data, appointment_datetime = select_first_appointment(suggest_html)

    print(f"Form data: {form_data}")
    print(f"Appointment datetime: {appointment_datetime}")
    
    assert success, message
    assert form_data is not None
    assert form_data.get("date") == "20251211"
    assert appointment_datetime is not None
    assert appointment_datetime.date() == datetime(2025, 12, 11).date()

def test_parse_all_appointments_from_saved_page():
    html_path = Path("data/debugPage/step_4_term_available_20251003_152049.html")
    if not html_path.exists():
        html_path = Path(__file__).resolve().parent.parent / "data/debugPage/step_4_term_available_20251003_152049.html"

    if not html_path.exists():
        print(f"Test file not found at {html_path}, skipping test.")
        return

    suggest_html = html_path.read_text(encoding="utf-8")
    
    appointments = parse_all_appointments(suggest_html)
    
    assert len(appointments) == 8
