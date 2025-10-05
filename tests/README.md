# EmailMCP Test Suite

Comprehensive test suite for the EmailMCP server covering all core functionalities.

## Test Coverage

### 1. OAuth Authentication Tests (`test_oauth_flow.py`)
- OAuth URL generation
- OAuth callback token exchange
- Token refresh flows
- Token expiry detection and handling
- Invalid token handling
- Invalid authorization code handling

### 2. Email Provider Tests (`test_email_providers.py`)
- **Gmail API Provider:**
  - Email sending (plain text and HTML)
  - CC and BCC support
  - API error handling
  - Network error handling
  - Configuration validation
  - Message creation (base64 encoding)
  
- **SMTP Provider:**
  - Email sending via SMTP
  - HTML email support
  - SMTP connection errors
  - Configuration validation

- **Provider Factory:**
  - Automatic provider selection
  - Manual provider selection
  - Provider fallback mechanisms
  - Available provider detection

### 3. Token Storage Tests (`test_token_storage.py`)
- Storing user tokens in GCP Secret Manager
- Storing user tokens in AWS Secrets Manager
- Retrieving user credentials
- Token storage with expiration metadata
- Multi-user token management
- Token update after refresh
- Secret existence checking

### 4. Integration Tests (`test_integration.py`)
- Complete end-to-end email flows
- OAuth to email sending flow
- Multi-tenant user flows
- Token refresh during email send
- API endpoint integration
- Error handling across the system
- Provider fallback mechanisms
- Concurrent operations
- Concurrent token refresh

### 5. API Route Tests (`test_api_routes.py`)
- Request validation (missing fields, invalid formats)
- Authentication and authorization
- Response format validation
- Error response formats
- CORS headers
- X-Request-ID header handling
- Security (SQL injection attempts, length validation)
- API documentation endpoints

## Running the Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Specific Test File
```bash
pytest tests/test_oauth_flow.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_oauth_flow.py::TestGmailOAuthFlow -v
```

### Run Specific Test Method
```bash
pytest tests/test_oauth_flow.py::TestGmailOAuthFlow::test_generate_oauth_url -v
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=src/mcp --cov-report=term-missing --cov-report=html
```

### Run Tests in Parallel (faster)
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

## Test Configuration

Test configuration is in `conftest.py` which includes:
- Pytest fixtures for common test data
- Mock settings
- Sample email requests
- Mock OAuth tokens
- Mock secrets managers

## Test Requirements

Required packages (already in requirements.txt or pyproject.toml):
- pytest >= 8.3.0
- pytest-asyncio >= 0.24.0
- pytest-cov >= 5.0.0
- httpx >= 0.27.0

## Coverage Report

After running tests with coverage, view the HTML report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared fixtures and configuration
├── test_oauth_flow.py       # OAuth authentication tests
├── test_email_providers.py  # Email provider implementation tests
├── test_token_storage.py    # Token storage and database tests
├── test_integration.py      # End-to-end integration tests
└── test_api_routes.py       # API route and validation tests
```

## Writing New Tests

When adding new tests:

1. Use existing fixtures from `conftest.py`
2. Follow the naming convention: `test_*.py` for files, `Test*` for classes, `test_*` for methods
3. Use descriptive test names that explain what is being tested
4. Add docstrings to explain the test purpose
5. Use `@pytest.mark.asyncio` for async tests
6. Mock external dependencies (HTTP calls, database operations)

Example:
```python
@pytest.mark.asyncio
async def test_my_feature(sample_email_request, mock_settings):
    """Test description"""
    # Test implementation
    assert result == expected
```

## CI/CD Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-asyncio pytest-cov
    pytest tests/ --cov=src/mcp --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Test Data

Tests use mocked data and do not require:
- Live Gmail API credentials
- Live SMTP servers
- Live database connections
- Live AWS/GCP secrets managers

All external dependencies are mocked for isolated unit testing.
