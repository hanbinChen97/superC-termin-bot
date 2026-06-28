# SuperC Appointment Checker Program Specification

## Program Overview
SuperC appointment checker is an automated appointment monitoring and booking system specifically designed to monitor appointment availability at the Aachen Auslaenderamt (immigration office) SuperC location and automatically book available appointments when detected.

## Core Functional Flow

### 1. Program Initialization
- Set up logging format and level
- Log program startup information and process PID
- Load SuperC location configuration

### 2. User Profile Management
The program supports two sources of user profiles:

#### Database Profile (Priority)
- Retrieve the first user profile with "waiting" status from database
- Use `get_first_waiting_profile()` function for querying
- Convert database record to `Profile` object
- Log current processing user information

#### Backup Profile (hanbin)
- Load user information from local file `data/hanbin` in JSON format
- Serves as backup option, always kept loaded
- Contains personal information like name, email, phone, birthday, etc.

### 3. Main Monitoring Loop
The program runs in an infinite loop, executing the following steps each iteration:

#### Time Check
- Check if current time is 1 AM
- If yes, automatically exit the program

#### Appointment Check
- Call `run_check() (from superc.appointment_checker)` function to perform appointment checking
- Pass SuperC configuration, current profile, and backup profile
- Returns three values: 
  - has_appointment (bool)
  - message (str)
  - appointment_datetime_str (str)

### 4. Result Processing Logic

#### No Appointment Available
If `has_appointment` is False:
- Wait 60 seconds then continue next round of checking

#### Appointment Available - Error Handling
If `has_appointment` is True and "zu vieler Terminanfragen" error is detected:
- Log error message
- Update database profile status to "error"
- Get next waiting user via unified `get_next_user_profile()` function
- If next user found, continue processing; otherwise exit program

#### Appointment Available - Success Processing
If `has_appointment` is True and no error is detected (appointment success):
- Log success message
- Update database profile status to "booked"
- Save appointment time information
- Get next waiting user via unified `get_next_user_profile()` function
- If next user found, continue processing; otherwise exit program

#### Unified Next User Processing
Both error and success cases use the same logic:
- Call `get_next_user_profile()` function to get next waiting user
- If user found, update current profile variables and continue
- If no user found, exit program gracefully

### 5. Database Interaction
- Use `get_first_waiting_profile()` to get waiting users
- Use `update_appointment_status()` to update user status
- Supported statuses: waiting, booked, error

### 6. Error Handling and Logging
- Log detailed information throughout the process
- Catch and handle various exception scenarios
- Log user information and processing status at key steps

## Key Data Structures

### Profile Class
Contains user personal information:
- Name (vorname, nachname)
- Contact info (email, phone)
- Birthday (geburtsdatum_day/month/year)
- Preferred locations (preferred_locations)

### Configuration Structure
- `LOCATIONS["superc"]` contains SuperC location-specific configuration
- Log format configuration `LOG_FORMAT`

## Program Exit Conditions
1. Automatic exit at 1 AM
2. Exit after detecting frequent submission error
3. Exit after successfully processing all waiting users
4. Exit when getting next user fails
5. Continue running on unexpected exceptions (log errors)

## Dependency Modules
- `superc.appointment_checker` - Core appointment checking logic
- `superc.config` - Configuration information
- `db.utils` - Database operation tools
- `superc.profile` - User profile management