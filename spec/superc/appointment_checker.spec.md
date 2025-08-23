# Appointment Checker Logic Specification

## Overview
The appointment checker orchestrates a 6-page appointment booking flow for the Aachen Ausländeramt system. It handles the complete process from initial page access to final booking confirmation using the `enter_schritt_x_page` pattern.

## Core Flow Architecture

### Main Entry Point: `run_check()`
- **Purpose**: Executes one complete appointment checking cycle
- **Parameters**: 
  - `location_config`: Configuration for the specific location (SuperC/Infostelle)
  - `current_profile`: User profile for appointments >= October
  - `hanbin_profile`: User profile for appointments < October
- **Returns**: `(success: bool, message: str, appointment_datetime_str: Optional[str])`

### 6-Page Flow Process

#### Page 2: Service and Location Selection (`enter_schritt_2_page()`)
- **Purpose**: Enter Schritt 2 page and complete service/location type selection
- **Page Entry**: GET `{BASE_URL}/select2?md=1`
- **Page Operations**:
  1. Validate page contains "Schritt 2" title
  2. Parse HTML to find header containing `selection_text`
  3. Extract the first `<li>` element's ID
  4. Build URL with format: `location?mdt=89&select_cnc=1&cnc-{id}=1`
- **Returns**: `(success: bool, url: str)`

#### Page 3: Location Information (`enter_schritt_3_page()`)
- **Purpose**: Enter Schritt 3 page and extract location information
- **Page Entry**: GET URL from Step 2
- **Page Operations**:
  1. Validate page contains "Schritt 3" title
  2. Extract `loc` value from hidden input field
- **Returns**: `(success: bool, loc: str)`

#### Page 4: Appointment Availability (`enter_schritt_4_page()`)
- **Purpose**: Enter Schritt 4 page and check appointment availability
- **Page Entry**: POST location data to enter Schritt 4
- **Page Operations**:
  1. POST location payload to enter page
  2. Validate page contains "Schritt 4" title
  3. GET `/suggest` endpoint to check availability
  4. Look for "Kein freier Termin verfügbar" message
  5. Parse available appointments using `select_appointment_and_choose_profile()`
  6. Extract form data and select profile based on appointment date
- **Returns**: `(success: bool, message: str, form_data: Optional[dict], profile: Optional[Profile], datetime_str: Optional[str])`

#### Page 5: Appointment Selection and Form Filling (`enter_schritt_5_page()`)
- **Purpose**: Enter Schritt 5 page and complete both appointment selection and form filling
- **Page Entry**: POST form data from Step 4 to `/suggest`
- **Page Operations**:
  1. POST form data to submit appointment selection
  2. Validate entry to Schritt 5 page
  3. Fill personal information form using `fill_form_with_captcha_retry()`
  4. Handle CAPTCHA with up to 3 retry attempts
- **Profile Usage**: Uses profile selected in Step 4
- **Returns**: `(success: bool, message: str, soup: Optional[bs4.BeautifulSoup])`

#### Page 6: Booking Confirmation (`enter_schritt_6_page()`)
- **Purpose**: Enter Schritt 6 page and complete booking confirmation
- **Page Entry**: Implicit - reached after successful form submission
- **Page Operations**:
  1. Handle email confirmation process
  2. Complete final booking steps
- **Current State**: Placeholder implementation assuming form submission completes booking
- **Returns**: `(success: bool, message: str)`

## Profile Selection Logic

### Module: `appointment_selector.py`
The profile selection logic has been extracted to a separate module for better code organization.

#### `select_appointment_and_choose_profile()`
- **Purpose**: Parse appointment data and select appropriate profile
- **Input**: HTML response text, current_profile, hanbin_profile
- **Logic**:
  1. Parse appointments from `details_suggest_times` or `sugg_accordion`
  2. Extract form data from first available appointment
  3. Extract date and time information
  4. Call `choose_profile_by_date()` to select profile
- **Returns**: `(success: bool, message: str, form_data: Optional[dict], profile: Optional[Profile], datetime_str: Optional[str])`

#### `choose_profile_by_date()`
- **Cutoff Month**: October (month 10)
- **Rule**: 
  - Month < 10: Use `hanbin_profile`
  - Month >= 10: Use `current_profile`
- **Fallback**: If preferred profile unavailable, fallback to alternative profile
- **Date Parsing**: Extracts month from format "Mittwoch, 27.08.2025"
- **Error Handling**: Defaults to `current_profile` if date parsing fails

## Architecture Pattern: `enter_schritt_x_page`

### Design Philosophy
Each `enter_schritt_x_page()` function encapsulates both:
1. **Page Entry**: HTTP requests to navigate to the page
2. **Page Operations**: All actions performed on that specific page

### Function Responsibilities
- **`enter_schritt_2_page`**: Page entry + service/location selection
- **`enter_schritt_3_page`**: Page entry + location info extraction
- **`enter_schritt_4_page`**: Page entry + availability check + appointment parsing + profile selection
- **`enter_schritt_5_page`**: Page entry + appointment submission + form filling
- **`enter_schritt_6_page`**: Page entry + booking confirmation

### Key Architectural Benefits
1. **Single Responsibility**: One function per page with complete functionality
2. **Clear Boundaries**: Each page's logic is self-contained
3. **Easy Debugging**: Page-specific issues can be isolated quickly
4. **Maintainable**: Changes to page logic are localized to single functions

## Data Flow and State Management

### Session Management
- Single `requests.Session` instance throughout entire flow
- User-Agent header set from config
- Session state preserved across all pages

### Inter-Page Data Flow
- **Page 2 → Page 3**: URL for next page navigation
- **Page 3 → Page 4**: Location value (`loc`) for form submission
- **Page 4 → Page 5**: Form data dict + selected profile + appointment datetime
- **Page 5 → Page 6**: BeautifulSoup object after successful form submission

### Error Handling Strategy
- **Early Termination**: Any page failure stops the entire flow
- **Page Validation**: Each page validates expected content using `validate_page_step()`
- **Comprehensive Logging**: Page-specific logging with clear context
- **Null Checks**: Proper handling of None values between page transitions

## Key Dependencies

### Internal Modules
- `config`: URLs, user agent, logging settings
- `utils`: Page validation (`validate_page_step`) and content saving utilities
- `form_filler`: Form submission with CAPTCHA handling (`fill_form_with_captcha_retry`)
- `profile`: User profile data structures
- `appointment_selector`: Appointment parsing and profile selection logic

### External Dependencies
- `requests`: HTTP session management
- `beautifulsoup4`: HTML parsing and form extraction
- `logging`: Structured logging throughout flow
- `urllib.parse`: URL construction with `urljoin()`

## Return Value Patterns

### Consistent Function Signatures
All `enter_schritt_x_page()` functions return tuples with:
1. **Success boolean**: `True` for success, `False` for failure
2. **Message string**: Descriptive success/error message
3. **Additional data**: Page-specific return values (URLs, form data, soup objects)

### Error Message Format
- Include page context: "Schritt X页面失败: {specific_error}"
- Descriptive and actionable error information
- Logged at appropriate levels (INFO for status, ERROR for failures)

## Configuration Dependencies

### Location Configuration
```python
{
    "name": str,           # Location identifier
    "selection_text": str, # Text to find in service selection
    "submit_text": str     # Submit button text for location
}
```

### URL Structure
- **Base URL**: Configured in `config.BASE_URL`
- **Endpoints**: `select2`, `location`, `suggest`
- **URL Building**: Uses `urllib.parse.urljoin()` for proper URL construction

## Debugging and Monitoring

### Page Content Saving
- Debug feature saves page content at key steps
- Filename format: `{step}_{description}_{location_name}`
- Controlled by configuration settings

### Verbose Logging
- `log_verbose()` function for detailed debugging information
- Controlled by `config.VERBOSE_LOGGING` setting
- Provides step-by-step flow visibility for troubleshooting