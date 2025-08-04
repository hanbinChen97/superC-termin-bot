# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an automated appointment checking bot for the Aachen Ausländeramt (immigration office). The bot monitors appointment availability at two locations (SuperC and Infostelle) and automatically books the first available slot when one becomes available.

## Core Architecture

### Main Components

- **superc.py / infostelle.py**: Location-specific entry points that run continuous monitoring loops
- **appointment_checker.py**: Core appointment checking logic that orchestrates the entire flow
- **form_filler.py**: Handles final form submission with personal data and CAPTCHA recognition
- **utils.py**: Utility functions for page content saving and CAPTCHA image downloading
- **llmCall.py**: Azure OpenAI integration for CAPTCHA text recognition
- **config.py**: Configuration constants including locations, URLs, and file paths
- **db/models.py**: Defines database models for users and appointment profiles
- **db/utils.py**: Database utility functions for querying and updating appointment profiles

### Flow Architecture

The appointment booking follows a 6-step process:
1. Get initial page (Schritt 1-2)
2. Select location type (SuperC/Infostelle)
3. Get location info (Schritt 3)
4. Submit location and check availability (Schritt 4)
5. Select first available appointment (Schritt 5)
6. Fill form with personal data and submit (Schritt 6)

### Personal Data Management

- Personal information is stored in files named `table` or `hanbin` (deprecated, use database instead now)
- The system dynamically selects which file to use based on appointment date (before September uses `hanbin`, September+ uses `table`)
- Database integration is now the primary method for managing user profiles and appointment statuses

## Development Commands

### Environment Setup
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
uv pip install -r requirements.txt
```

### Running the Bot
```bash
# For SuperC location monitoring
nohup python3 superc.py 2>&1 | tee superc.log

# For Infostelle location monitoring  
python3 infostelle.py

# Background process
source .venv/bin/activate && nohup python app.py > app.log 2>&1 &
```

### Key Dependencies
- requests>=2.31.0 - HTTP requests and web scraping
- beautifulsoup4>=4.12.0 - HTML parsing
- python-dotenv==1.0.0 - Environment variables
- openai>=1.0.0 - CAPTCHA recognition via Azure OpenAI API
- sqlalchemy>=2.0.0 - Database ORM
- psycopg2-binary>=2.9.0 - PostgreSQL adapter

## File Structure Notes

- `pages/` - Directory for saved HTML content during debugging
- `logs/` - Application logs and saved HTML responses
- `table` / `hanbin` - Personal information files (JSON format)
- `requirements.txt` - Dependencies (note: contains Unicode BOM characters)
- `db/` - Database models and utility functions

## Important Configuration

- Base URL: `https://termine.staedteregion-aachen.de/auslaenderamt/`
- Locations are configured in `config.py` with specific selection and submit text
- User agent is configured to mimic Chrome browser
- The bot saves page content at each step for debugging purposes

## Monitoring and Logs

The application uses Python's logging module with timestamps and runs in continuous loops with 60-second intervals between checks. Each location runs independently and exits when an appointment is successfully booked.