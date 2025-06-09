# Contributing to HoistScraper

Thank you for your interest in contributing to HoistScraper! This document provides guidelines and setup instructions for contributors.

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/hoistscraper.git
   cd hoistscraper
   ```

2. **Set up Python environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. **Set up Node.js environment**
   ```bash
   cd frontend
   npm install
   ```

4. **Install pre-commit hooks**
   ```bash
   # From project root
   pip install pre-commit
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

## Code Quality Tools

We use several tools to maintain code quality and consistency:

### Python (Backend)

- **Black**: Code formatting
- **Ruff**: Fast linting and import sorting
- **MyPy**: Type checking
- **Pytest**: Testing

### JavaScript/TypeScript (Frontend)

- **Prettier**: Code formatting
- **ESLint**: Linting
- **TypeScript**: Type checking
- **Vitest**: Testing

### Pre-commit Configuration

Create `.pre-commit-config.yaml` in the project root:

```yaml
repos:
  # Python formatting and linting
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        files: ^backend/
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        files: ^backend/
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
        files: ^backend/

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        files: ^backend/
        additional_dependencies: [types-requests, types-PyYAML]

  # JavaScript/TypeScript formatting and linting
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        files: ^frontend/
        types_or: [javascript, jsx, ts, tsx, json, css, scss, markdown]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: ^frontend/
        types: [file]
        types_or: [javascript, jsx, ts, tsx]
        additional_dependencies:
          - eslint@8.56.0
          - eslint-config-next@14.2.0

  # General hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  # Conventional commits
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.0.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [optional-scope]
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Changes

- Write code following the established patterns
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests Locally

**Backend tests:**
```bash
cd backend
pytest
```

**Frontend tests:**
```bash
cd frontend
npm test
```

**E2E tests:**
```bash
npm run test:e2e
```

### 4. Format and Lint

Pre-commit hooks will run automatically, but you can also run them manually:

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific tools
black backend/
ruff check backend/ --fix
prettier --write frontend/
```

### 5. Commit Changes

Use conventional commit format:

```bash
git add .
git commit -m "feat: add new crawling feature"
```

**Commit message format:**
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style Guidelines

### Python

- Follow PEP 8 (enforced by Black and Ruff)
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions small and focused
- Use meaningful variable names

**Example:**
```python
async def fetch_opportunities(
    site_config: dict[str, Any],
    max_pages: int = 5
) -> list[Opportunity]:
    """Fetch job opportunities from a configured site.
    
    Args:
        site_config: Site-specific configuration dictionary
        max_pages: Maximum number of pages to crawl
        
    Returns:
        List of extracted opportunities
        
    Raises:
        CrawlError: If crawling fails
    """
    # Implementation here
```

### TypeScript/JavaScript

- Use TypeScript for all new code
- Follow the existing component patterns
- Use meaningful component and variable names
- Write JSDoc comments for complex functions
- Prefer functional components with hooks

**Example:**
```typescript
interface OpportunityCardProps {
  opportunity: Opportunity;
  onSelect?: (id: string) => void;
}

/**
 * Displays a job opportunity card with title, company, and actions.
 */
export function OpportunityCard({ 
  opportunity, 
  onSelect 
}: OpportunityCardProps) {
  // Implementation here
}
```

## Testing Guidelines

### Backend Tests

- Write unit tests for all business logic
- Use pytest fixtures for common test data
- Mock external dependencies
- Test error conditions and edge cases

```python
def test_crawler_handles_captcha():
    """Test that crawler properly detects and handles CAPTCHA."""
    # Test implementation
```

### Frontend Tests

- Write component tests using Testing Library
- Test user interactions and state changes
- Mock API calls
- Test accessibility features

```typescript
test('displays opportunity details when clicked', async () => {
  // Test implementation
});
```

### E2E Tests

- Test critical user journeys
- Use realistic test data
- Test across different browsers
- Include error scenarios

## Documentation

- Update README.md for user-facing changes
- Add/update docstrings for code changes
- Update architecture diagrams if needed
- Include examples in documentation

## Performance Considerations

- **Backend**: Use async/await for I/O operations
- **Frontend**: Implement proper loading states and error boundaries
- **Database**: Use appropriate indexes and query optimization
- **Crawling**: Respect rate limits and implement proper delays

## Security Guidelines

- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all user inputs
- Follow OWASP security guidelines
- Respect robots.txt and terms of service

## Getting Help

- Check existing issues and discussions
- Ask questions in GitHub Discussions
- Review the architecture documentation
- Look at existing code for patterns

## Release Process

1. Update CHANGELOG.md
2. Bump version using `bumpversion`
3. Create release PR
4. Tag release after merge
5. Deploy to production

Thank you for contributing to HoistScraper! 🚀 