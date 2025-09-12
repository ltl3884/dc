# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Address Crawler - A Flask-based web crawler application with scheduling capabilities for automated address data collection.

## Common Development Commands

### Environment Setup
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt
# Or for development
uv pip install -r requirements-dev.txt
```

### Running the Application
```bash
# Run development server (from project root)
python src/main.py

# Run with specific configuration
FLASK_ENV=production python src/main.py

# Run production server (auto-detects gunicorn/waitress)
FLASK_ENV=production python src/main.py
```

### Database Operations
```bash
# Initialize database migrations
flask db init

# Create migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Downgrade migrations
flask db downgrade
```

### Testing
```bash
# Run all tests
python run_tests.py

# Run specific test pattern
python run_tests.py --pattern "test_crawler*.py"

# Run specific test module
python run_tests.py --module test_task_model

# Run with verbose output
python run_tests.py --verbose
```

### Code Quality
```bash
# Format code with black
black src/ tests/

# Type checking
mypy src/

# Run linting
flake8 src/ tests/
```

## High-Level Architecture

### Application Structure
The application follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Flask Application                        │
├─────────────────────────────────────────────────────────────┤
│  Presentation Layer  │  Service Layer  │  Data Layer       │
│                      │                 │                   │
│  • API Routes        │  • TaskService  │  • Task Model     │
│  • Error Handlers    │  • CrawlerSvc   │  • Address Model  │
│  • Request/Response  │  • DataService  │  • SQLAlchemy     │
│                      │  • Validation   │  • Database       │
├─────────────────────────────────────────────────────────────┤
│              APScheduler Task Scheduler                     │
├─────────────────────────────────────────────────────────────┤
│              External API (meiguodizhi.com)                 │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

**Models Layer** (`src/models/`)
- `task.py`: Task model for managing crawling tasks with status tracking
- `address_info.py`: AddressInfo model for storing crawled address data
- Both models inherit from SQLAlchemy Model with standardized fields (id, created_at, updated_at)

**Services Layer** (`src/services/`)
- `task_service.py`: Manages task lifecycle (create, update, delete, status transitions)
- `crawler_service.py`: Handles external API calls and data extraction logic
- `data_service.py`: Abstracts database operations for address data persistence
- `validation_service.py`: Validates crawled data integrity and format

**Scheduler Layer** (`src/scheduler/`)
- `task_scheduler.py`: APScheduler wrapper managing task execution timing
- Configurable execution intervals (default: every 5 seconds)
- Supports concurrent task execution with instance limits

**Application Factory** (`src/app.py`)
- Implements Flask application factory pattern
- Handles extension initialization (SQLAlchemy, Migrate)
- Configures logging, error handlers, and blueprints

### Data Flow

1. **Task Creation**: TaskService creates tasks with pending status
2. **Scheduler Execution**: APScheduler triggers CrawlerService at configured intervals
3. **Data Collection**: CrawlerService calls external API and parses response
4. **Data Validation**: ValidationService checks data integrity
5. **Data Storage**: DataService persists validated address information
6. **Status Update**: TaskService updates task status (success/failed)

### Configuration Management

Environment-based configuration using python-dotenv:
- `.env` file contains all configuration (copy from `.env.example`)
- Config classes in `src/config.py` handle different environments
- Database URL, API endpoints, scheduler settings are configurable

### Error Handling Strategy

- **Application Level**: Centralized error handlers in app factory
- **Service Level**: Try-catch blocks with specific exception types
- **Database Level**: SQLAlchemy integrity constraints and rollback handling
- **API Level**: Request timeout and retry mechanisms
- **Logging**: Structured logging with different levels per module

### Key Design Patterns

1. **Factory Pattern**: Flask app creation with `create_app()`
2. **Service Layer Pattern**: Business logic separation from data access
3. **Repository Pattern**: DataService abstracts database operations
4. **Observer Pattern**: Scheduler triggers service execution
5. **Strategy Pattern**: Configurable validation and processing strategies

This architecture ensures maintainability, testability, and clear separation between web framework, business logic, and data persistence layers.