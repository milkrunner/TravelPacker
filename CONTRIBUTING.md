# Contributing to NikNotes

Thank you for your interest in contributing to NikNotes! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (recommended)
- A Google Gemini API key (for AI features)

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/your-username/TravelPacker.git
cd TravelPacker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env with your API keys

# Run the app
python web_app.py
```

### Docker Setup

```bash
cp .env.example .env
docker compose up -d
```

## Development Workflow

1. **Create a branch** from `main` for your changes
2. **Make your changes** following the code style guidelines below
3. **Run tests** to ensure nothing is broken
4. **Submit a pull request** with a clear description

## Code Style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting.

```bash
# Check formatting
ruff format --check .

# Auto-format
ruff format .

# Lint
ruff check .

# Lint with auto-fix
ruff check --fix .
```

Key conventions:
- Python 3.12+ syntax (StrEnum, type unions)
- Double quotes for strings
- 120 character line length
- Type hints where practical

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/security/
```

## Project Structure

```
src/
├── blueprints/    # Route handlers (main, auth, trips, api)
├── database/      # SQLAlchemy models & repositories
├── models/        # Pydantic validation models
├── services/      # Business logic layer
└── utils/         # Logging, rate limiting, security helpers
```

## Submitting Changes

- Keep PRs focused on a single concern
- Include tests for new features or bug fixes
- Update documentation if needed
- Ensure CI passes before requesting review

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include steps to reproduce for bugs
- Provide context about your environment (OS, Python version, Docker)

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
