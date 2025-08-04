# Copilot Instructions for Aachen Termin Bot

## Project Overview
The Aachen Termin Bot automates appointment booking for the Aachen Ausländeramt. It monitors appointment availability at two locations (SuperC and Infostelle) and books the first available slot. The bot integrates Azure OpenAI for CAPTCHA recognition and uses a database for managing user profiles and appointment statuses.

## Core Architecture

### Key Components
- **`superc.py` / `infostelle.py`**: Location-specific entry points for monitoring.
- **`appointment_checker.py`**: Orchestrates the appointment checking and booking process.
- **`form_filler.py`**: Handles form submission, including CAPTCHA recognition.
- **`llmCall.py`**: Integrates Azure OpenAI for CAPTCHA text recognition.
- **`db/models.py`**: Defines database models for users and appointments.
- **`db/utils.py`**: Provides database utility functions.
- **`config.py`**: Stores configuration constants (e.g., URLs, file paths).

### Flow Architecture
The appointment booking process follows these steps:
1. Fetch the initial page (Schritt 1-2).
2. Select location type (SuperC/Infostelle).
3. Retrieve location information (Schritt 3).
4. Submit location and check availability (Schritt 4).
5. Select the first available appointment (Schritt 5).
6. Fill out the form with personal data and submit (Schritt 6).

### Data Management
- Personal data is primarily managed via a database.
- Legacy files (`table`, `hanbin`) are still used for older appointments.
- Database integration is the preferred method for scalability and reliability.

## Development Workflows

### Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
uv pip install -r requirements.txt
```

### Running the Bot
```bash
# Monitor SuperC location
nohup python3 superc.py 2>&1 | tee superc.log &

# Monitor Infostelle location
python3 infostelle.py
```

### Testing
- Unit tests are located in `tests/`.
- Run all tests:
  ```bash
  python3 -m unittest discover tests
  ```
- Integration tests are in `tests/integration/`.

### Debugging
- Saved HTML pages for debugging are in `pages/superc/`.
- Logs are stored in `logs/`.

## Project-Specific Conventions
- **Logging**: Python's logging module is used with timestamps for transparency.
- **CAPTCHA Recognition**: Azure OpenAI API is used for CAPTCHA text extraction.
- **File Structure**:
  - `pages/`: Debugging HTML content.
  - `logs/`: Application logs.
  - `db/`: Database models and utilities.

## Integration Points
- **Azure OpenAI**: Used for CAPTCHA recognition via `llmCall.py`.
- **PostgreSQL**: Database backend managed via SQLAlchemy and `psycopg2`.
- **Web Scraping**: HTML parsing with `BeautifulSoup`.

## Known Issues
- Limited error handling for network failures and API rate limits.

## Recommendations for AI Agents
- Focus on modularity when adding new features.
- Follow the 6-step flow architecture for appointment booking.
- Use the database for managing new data instead of legacy files.
- Ensure robust error handling and logging for new components.
- Update tests in `tests/` to maintain coverage for new features.

每个 function 都要明确指出 input type和 output type，确保代码的可读性和可维护性。