# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django-based poker tournament management system that provides real-time tournament control, player registration, table management, and blind level timing. The application follows a traditional Django MVC pattern with a REST-like JSON API for dynamic frontend interactions.

## Development Commands

### Setup and Running
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python manage.py runserver

# Create/apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin access
python manage.py createsuperuser

# Run tests
python manage.py test core

# Run specific test
python manage.py test core.tests.TestClassName

# Run Telegram bot
python manage.py runbot
```

### Database
- Uses SQLite by default (`db.sqlite3` in root directory)
- All models defined in `core/models.py`

## Architecture

### App Structure
- **Project:** `poker_system/` - Django project configuration
- **App:** `core/` - Main application containing all business logic
- **App:** `bot/` - Telegram bot integration for player registration and login
- Working directory: Project root (all Django commands run from root directory)

### Data Model Hierarchy

**Tournament Templates → Tournaments → Registrations/Tables**

1. **TournamentTemplate & TemplateLevel**: Reusable tournament configurations with predefined blind structures
2. **Tournament & TournamentLevel**: Active tournament instances with their own blind levels (copied from templates or generated)
3. **Player**: Players identified by telegram_id (unique), with optional username/name fields
4. **Registration**: Links players to tournaments, tracks status (REGISTERED/ELIMINATED), rebuys, addons, table assignments, and final placement
5. **Table**: Tournament tables with seat assignments via Registration.table foreign key
6. **Payout, GameEvent, SystemSettings**: Supporting models for prize distribution, event logging, and global settings

### Timer System Architecture

The tournament timer is managed through a combination of database state and server-side calculations:

**State Fields (in Tournament model):**
- `current_level_index`: Current blind level (0-based index)
- `level_started_at`: Timestamp when current level started running
- `timer_seconds`: Remaining seconds when paused, or initial duration
- `status`: SCHEDULED/RUNNING/PAUSED/FINISHED/BREAK

**Timer Logic:**
- When RUNNING: Calculate remaining time as `timer_seconds - (now - level_started_at)`
- When PAUSED: Use stored `timer_seconds` value
- API endpoint `/api/tournament/<id>/status/` provides real-time timer state
- Frontend polls this endpoint to update display

**Key API endpoints (in core/api.py):**
- `start_timer`: Sets `level_started_at = now`, status = RUNNING
- `pause_timer`: Calculates elapsed time, updates `timer_seconds`, clears `level_started_at`
- `next_level/prev_level`: Advances/rewinds level, resets timer to new level's duration
- `get_status`: Returns current level info and calculated remaining seconds

### URL Structure

**Views (core/views.py):**
- `/` - Dashboard listing all tournaments
- `/tournament/add/` - Create new tournament
- `/tournament/<id>/control/` - Tournament control interface
- `/tournament/<id>/display/` - Public tournament display screen
- `/tournament/<id>/info/` - Tournament information page for players
- `/profile/` - Player profile with statistics and tournament history
- `/templates/` - List tournament templates
- `/templates/add/` - Create template with blind levels
- `/templates/<id>/edit/` - Edit template
- `/templates/<id>/delete/` - Delete template

**API (core/api.py):**
All API endpoints return JSON and use @csrf_exempt for easier integration:
- Timer: `/api/tournament/<id>/timer/{start,pause}/`, `/api/tournament/<id>/level/{next,prev}/`
- Status: `/api/tournament/<id>/status/`
- Players: `/api/tournament/<id>/{players,register,eliminate,rebuy,addon}/`, `/api/players/search/`
- Tables: `/api/tournament/<id>/tables/{generate,clear}/`, `/api/tournament/<id>/tables/move/`
- Blind Structure: `/api/tournament/<id>/levels/`, `/api/tournament/<id>/level/{add,update,delete}/`
- Payouts: `/api/tournament/<id>/payouts/{get,generate,add,update,delete}/`

### Template System

Templates are in `templates/`:
- `base.html` - Base template with common structure
- `core/` subdirectory for app-specific templates
- Forms use shadcn-style Tailwind CSS classes (see `core/forms.py` widgets)

Static files in `static/`:
- `css/globals.css` - Global styles
- `js/timer.js` - Timer polling and display logic
- `js/players.js` - Player registration/elimination
- `js/tables.js` - Table generation and seating
- `js/blinds.js` - Blind structure management
- `js/payouts.js` - Payout management
- `js/main.js` - Common utilities

### Forms and Formsets

- **TournamentTemplateForm**: Creates templates with basic info
- **TemplateLevelFormSet**: Inline formset for adding multiple blind levels to a template
- **TournamentForm**: Creates tournaments, includes optional template selection field that pre-populates levels

## Key Implementation Patterns

### Template-to-Tournament Flow
When creating a tournament from a template (views.py:125-167):
1. User selects template in TournamentForm
2. Tournament is saved with template's settings
3. Template's TemplateLevel objects are copied to TournamentLevel objects for the new tournament
4. If no template selected, default levels are generated (exponential blind structure)

### Table Generation Algorithm
`api.py:generate_tables()` implements balanced seating:
1. Delete existing tables
2. Calculate needed tables (ceil(player_count / MAX_SEATS))
3. Create Table objects
4. Shuffle registrations randomly
5. Distribute players evenly across tables (handles uneven distribution)
6. Assign seat_number and table foreign key to each Registration

### Player Elimination Placement
When a player is eliminated (api.py:326-440):
1. Set Registration.status = 'ELIMINATED'
2. Calculate place as (remaining_players + 1)
3. Clear table assignment
4. Place is based on how many players are still REGISTERED
5. For FREE tournaments: Calculate points using special formula
6. For PAID tournaments: Assign payout if player finishes in prize-paying position
7. For FREE tournaments only: Automatically advance to next blind level while preserving timer

### Points Calculation (FREE Tournaments)
Points calculation logic for FREE tournaments (api.py:349-384):
- Last place gets 1 point
- Second to last gets 2 points
- For places 4 and below: `(total_players - place + 1)`
- 3rd place: 4th place points + 3
- 2nd place: 3rd place points + 3
- 1st place: 4th place points * 2
- Bounty points are added to base points

### Payout Generation
`api.py:generate_payouts()` creates payout structure (api.py:860-917):
- 1-10 players: Top 2 places paid (70%/30%)
- 11-20 players: Top 3 places paid (50%/30%/20%)
- 21-30 players: Top 4 places paid (45%/27%/18%/10%)
- 31+ players: Top 5 places paid (40%/25%/17%/11%/7%)

## Telegram Bot Integration

### Bot Commands
- `/start` - Register or welcome back player
- `/login` - Generate one-time login link for web interface
- `/tournaments` - List available tournaments with registration buttons

### Bot Architecture (bot/management/commands/runbot.py)
- Uses python-telegram-bot library
- Async handlers with `sync_to_async` for database operations
- Main keyboard with "🎰 Турниры" and "🔐 Логин" buttons
- Callback handlers for inline buttons (e.g., tournament registration)

### Login Flow
1. User sends `/login` in Telegram
2. Bot creates LoginToken (bot/models.py)
3. Bot sends one-time link to user
4. User clicks link, handled by `bot/views.py:bot_login()`
5. Token is validated and marked as used
6. Session is created with player_id

## Django Admin

All models are registered in `core/admin.py` for basic CRUD operations via `/admin/`. Use this for:
- Quick data inspection
- Manual player/tournament creation
- Debugging registrations and table assignments

## Session Management

Player authentication is handled through Django sessions:
- `player_id` stored in `request.session`
- Context processor `core/context_processors.py:player_context` adds player to all templates
- `/logout/` clears session
