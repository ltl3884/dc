# Implementation Plan

## Task Overview

地址爬虫功能将按照分层架构逐步构建，从基础环境配置开始，依次实现数据模型、服务层、调度器，最后进行集成测试。每个任务都遵循原子性原则，确保15-30分钟内可完成，便于逐步开发和验证。

## Steering Document Compliance

### 技术标准遵循 (tech.md)
- 使用Python 3.11，遵循PEP 8编码规范
- 采用Flask + SQLAlchemy架构模式
- 使用uv + pyproject.toml进行依赖管理
- 集成APScheduler实现定时任务调度
- 使用Python logging模块进行日志管理

### 项目结构遵循 (structure.md)
- 严格遵循分层架构：models/ → services/ → scheduler/
- 使用snake_case文件命名和PascalCase类名
- 按照导入顺序规范：标准库 → 第三方库 → 本地模块
- 每个文件专注于单一职责，不超过300行代码

## Atomic Task Requirements

**Each task must meet these criteria for optimal agent execution:**
- **File Scope**: Touches 1-3 related files maximum
- **Time Boxing**: Completable in 15-30 minutes
- **Single Purpose**: One testable outcome per task
- **Specific Files**: Must specify exact files to create/modify
- **Agent-Friendly**: Clear input/output with minimal context switching

## Task Format Guidelines

- Use checkbox format: `- [ ] Task number. Task description`
- **Specify files**: Always include exact file paths to create/modify
- **Include implementation details** as bullet points
- Reference requirements using: `_Requirements: X.Y, Z.A_`
- Reference existing code to leverage using: `_Leverage: path/to/file.py, path/to/module.py_`
- Focus only on coding tasks (no deployment, user testing, etc.)
- **Avoid broad terms**: No "system", "integration", "complete" in task titles

## Tasks

### Phase 1: 项目基础配置

- [ ] 1. Create pyproject.toml with project dependencies
  - File: pyproject.toml
  - Define project metadata and dependencies (Flask, SQLAlchemy, APScheduler, requests, python-dotenv)
  - Configure Python version requirement (3.11+)
  - Purpose: Establish project dependency management
  - _Requirements: 1.1_

- [ ] 2. Create main application configuration file
  - File: src/config.py
  - Define database connection settings using environment variables
  - Configure APScheduler settings (timezone, job defaults)
  - Set up logging configuration (level, format, file settings)
  - Purpose: Centralize application configuration
  - _Requirements: 1.2, 5.1_

- [ ] 3. Create Flask application factory
  - File: src/app.py
  - Initialize Flask app with configuration
  - Set up SQLAlchemy database connection
  - Configure Flask-Migrate for database migrations
  - Purpose: Create main Flask application instance
  - _Requirements: 1.3_

- [ ] 4. Set up database connection utilities
  - File: src/utils/database.py
  - Create database initialization function
  - Define database connection parameters
  - Handle connection errors gracefully
  - Purpose: Provide centralized database utilities
  - _Requirements: 1.4, 2.2_

- [ ] 5. Create logging configuration utility
  - File: src/utils/logger.py
  - Set up RotatingFileHandler for log file management
  - Configure console and file log formats
  - Define log level based on configuration
  - Purpose: Provide centralized logging functionality
  - _Requirements: 5.1, 5.2_

### Phase 2: 数据模型层实现

- [ ] 6. Create Task model with SQLAlchemy
  - File: src/models/task.py
  - Define Task class with all required fields (url, method, body, headers, total_num, visited_num, status, timeout, retry_count)
  - Add database constraints and default values
  - Include timestamp fields (created_at, updated_at)
  - Purpose: Define task data structure for database storage
  - _Requirements: 4.1, 4.2_

- [ ] 7. Create AddressInfo model with SQLAlchemy
  - File: src/models/address_info.py
  - Define AddressInfo class with address fields (address, telephone, city, zip_code, state, state_full, country)
  - Add source_url field to track data origin
  - Include timestamp fields (created_at, updated_at)
  - Purpose: Define address data structure for database storage
  - _Requirements: 2.1, 2.2_

- [ ] 8. Create model initialization and imports
  - File: src/models/__init__.py
  - Import Task and AddressInfo models
  - Define model registry for migration tools
  - Set up model-level utility functions
  - Purpose: Provide clean model imports and initialization
  - _Requirements: 2.1_

- [x] 9. Create database migration initialization
  - Execute: flask db init (command setup)
  - Create migrations directory structure
  - Set up initial migration configuration
  - Purpose: Prepare database migration system
  - _Requirements: 2.1, 2.2_

### Phase 3: 服务层实现

- [ ] 10. Create TaskService for task management
  - File: src/services/task_service.py
  - Implement create_task() method with parameter validation
  - Add get_pending_task() to fetch next available task
  - Include update_task_status() for progress tracking
  - Purpose: Provide task lifecycle management functionality
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 11. Create CrawlerService for API interaction
  - File: src/services/crawler_service.py
  - Implement crawl_address() method for API calls
  - Add parse_api_response() for JSON data extraction
  - Include error handling for different HTTP status codes
  - Purpose: Provide address data crawling functionality
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 12. Create data validation service
  - File: src/services/validation_service.py
  - Implement validate_address_data() for required field checking
  - Add check_duplicate_address() for uniqueness validation
  - Include sanitize_telephone() for data cleaning
  - Purpose: Ensure data quality and integrity
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 13. Create data persistence service
  - File: src/services/data_service.py
  - Implement save_address_data() for database storage
  - Add handle_duplicate_data() for conflict resolution
  - Include transaction management for data consistency
  - Purpose: Handle address data storage operations
  - _Requirements: 2.1, 2.2, 2.3, 6.4_

- [ ] 14. Create service initialization and imports
  - File: src/services/__init__.py
  - Import all service classes
  - Define service factory functions
  - Set up service-level error handling
  - Purpose: Provide clean service imports and initialization
  - _Requirements: 3.1_

### Phase 4: 调度器实现

- [ ] 15. Create TaskScheduler with APScheduler
  - File: src/scheduler/task_scheduler.py
  - Initialize APScheduler with BackgroundScheduler
  - Configure job defaults and timezone settings
  - Add scheduler start/stop functionality
  - Purpose: Provide task scheduling infrastructure
  - _Requirements: 3.1, 3.2_

- [ ] 16. Implement task execution logic in scheduler
  - File: src/scheduler/task_scheduler.py (continue)
  - Add execute_pending_tasks() method
  - Implement task selection logic (visited_num < total_num)
  - Purpose: Execute crawler tasks on schedule
  - _Requirements: 3.2, 3.3_

- [x] 17. Create scheduler monitoring and statistics
  - File: src/scheduler/task_scheduler.py (continue)
  - Add task execution statistics tracking
  - Implement success/failure/skip counters
  - Purpose: Provide basic task execution monitoring
  - _Requirements: 7.1, 7.2_

- [ ] 19. Create scheduler initialization
  - File: src/scheduler/__init__.py
  - Import TaskScheduler class
  - Define scheduler configuration constants
  - Set up scheduler-level utilities
  - Purpose: Provide clean scheduler imports and configuration
  - _Requirements: 3.1_

### Phase 5: 集成和配置

- [ ] 20. Create main application runner
  - File: src/main.py
  - Initialize Flask application with all components
  - Set up scheduler startup and shutdown hooks
  - Configure signal handlers for graceful shutdown
  - Purpose: Provide application entry point
  - _Requirements: 1.3, 3.1, 3.2_

- [ ] 21. Create database initialization script
  - File: scripts/init_db.py
  - Implement database creation and table setup
  - Add sample data insertion for testing
  - Include database cleanup utilities
  - Purpose: Provide database setup automation
  - _Requirements: 2.1, 2.2_

- [ ] 22. Create environment configuration template
  - File: .env.example
  - Define database connection parameters
  - Set up API configuration settings
  - Include logging and scheduler configurations
  - Purpose: Provide environment configuration template
  - _Requirements: 1.2, 5.1_

- [ ] 23. Create requirements.txt backup file
  - File: requirements.txt
  - List all project dependencies with versions
  - Include development dependencies
  - Provide alternative installation method
  - Purpose: Backup dependency specification
  - _Requirements: 1.1_

### Phase 6: 日志和监控

- [ ] 24. Implement logging in TaskService
  - File: src/services/task_service.py
  - Add info-level logging for task operations
  - Include error-level logging for task failures
  - Add debug-level logging for troubleshooting
  - Purpose: Provide task service operation logging
  - _Requirements: 5.1, 5.2_

- [ ] 25. Implement logging in CrawlerService
  - File: src/services/crawler_service.py
  - Add info-level logging for API operations
  - Include error-level logging for crawl failures
  - Add debug-level logging for response data
  - Purpose: Provide crawler service operation logging
  - _Requirements: 5.3, 5.4_

- [x] 26. Implement logging in DataService
  - File: src/services/data_service.py
  - Add info-level logging for data operations
  - Include error-level logging for storage failures
  - Add debug-level logging for validation results
  - Purpose: Provide data service operation logging
  - _Requirements: 5.5, 6.1, 6.2, 6.3, 6.4_

- [x] 27. Implement logging in scheduler
  - File: src/scheduler/task_scheduler.py
  - Add scheduler startup/shutdown logging
  - Include task execution statistics logging
  - Purpose: Provide scheduler operation logging
  - _Requirements: 7.1, 7.2_

- [ ] 28. Add performance metrics logging to scheduler
  - File: src/scheduler/task_scheduler.py (continue)
  - Add performance metrics logging
  - Add execution time tracking
  - Purpose: Provide detailed performance monitoring
  - _Requirements: 7.3, 7.4_

- [ ] 29. Create log rotation and cleanup utilities
  - File: src/utils/log_cleanup.py
  - Implement log file size checking
  - Add automatic log rotation functionality
  - Include old log cleanup based on retention policy
  - Purpose: Manage log file lifecycle
  - _Requirements: 5.3, 7.4_

### Phase 7: 测试和验证

- [x] 30. Create basic unit tests for Task model
  - File: tests/test_task_model.py
  - Test Task model creation and validation
  - Test field constraints and default values
  - Include timestamp field verification
  - Purpose: Validate Task model functionality
  - _Requirements: 4.1, 4.2_

- [ ] 31. Create basic unit tests for AddressInfo model
  - File: tests/test_address_model.py
  - Test AddressInfo model constraints
  - Test field length validations
  - Include database relationship tests
  - Purpose: Validate AddressInfo model functionality
  - _Requirements: 2.1, 2.2_

- [ ] 32. Create integration tests for TaskService
  - File: tests/test_task_service.py
  - Test TaskService CRUD operations
  - Test task parameter validation
  - Test task status update functionality
  - Purpose: Validate TaskService functionality
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 33. Create integration tests for CrawlerService
  - File: tests/test_crawler_service.py
  - Test API URL construction
  - Test response parsing logic
  - Test error handling for different status codes
  - Purpose: Validate CrawlerService functionality
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 34. Create integration tests for DataService
  - File: tests/test_data_service.py
  - Test data validation and storage
  - Test duplicate detection logic
  - Test transaction rollback on errors
  - Purpose: Validate data layer functionality
  - _Requirements: 2.1, 2.2, 2.3, 6.1, 6.2, 6.3, 6.4_

- [ ] 35. Create scheduler functionality tests
  - File: tests/test_scheduler.py
  - Test task scheduling and execution
  - Test task selection logic
  - Test exception handling for task failures
  - Purpose: Validate scheduler core functionality
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 36. Create end-to-end workflow tests
  - File: tests/test_workflow.py
  - Test complete task execution: task creation -> API call -> data storage
  - Test error recovery workflow: API failure -> error logging -> next task
  - Test data validation workflow: invalid data -> validation error -> skip
  - Purpose: Validate complete system workflow
  - _Requirements: All_

- [ ] 37. Create test configuration and utilities
  - Files: tests/conftest.py, tests/utils.py
  - Set up test database configuration
  - Create test data fixtures
  - Implement test helper functions
  - Purpose: Provide test infrastructure
  - _Requirements: All_