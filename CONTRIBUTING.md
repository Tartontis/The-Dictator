# Contributing to The-Dictator

Thanks for your interest in contributing! This project uses a doc-first approach with multiple coding agents, so coordination is key.

---

## Quick Links

- [Architecture](docs/architecture.md) — How the system works
- [API Documentation](docs/api.md) — Backend endpoint contract
- [Agent Playbook](docs/agent-playbook.md) — Rules for coding agents

---

## Getting Started

### Prerequisites

- Python 3.10+
- FFmpeg (`sudo apt install ffmpeg`)
- Node.js (optional, for frontend dev)

### Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/The-Dictator.git
cd The-Dictator

# Create Python virtual environment
python -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -e ".[dev]"

# Download a Whisper model
./scripts/download_model.sh small

# Copy example config
cp config.example.toml config/settings.toml

# Start the dev server
./scripts/dev.sh
```

---

## Making Changes

### 1. Check the docs first

Before making changes, read:
- `README.md` for project overview
- `docs/architecture.md` for system design
- `docs/api.md` if touching backend endpoints
- Relevant ADRs in `docs/adr/`

### 2. Create a branch

```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/issue-description
```

### 3. Make your changes

Follow the code style in [Agent Playbook](docs/agent-playbook.md).

### 4. Update documentation

- **Changed an API endpoint?** Update `docs/api.md`
- **Made an architectural decision?** Add an ADR
- **Added a feature?** Update README roadmap

### 5. Write tests

For backend changes, add tests in `tests/`:

```bash
pytest tests/
```

### 6. Commit with conventional commits

```bash
git commit -m "feat: add voice activity detection"
git commit -m "fix: handle empty audio files"
git commit -m "docs: update API docs for /refine"
```

### 7. Open a PR

- Use a descriptive title
- Explain what you changed and why
- Link to any related issues
- Tag relevant reviewers

---

## Code Style

### Python

- Use type hints
- Use Pydantic for data models
- Use pathlib for file paths
- Use f-strings
- Run `ruff check` before committing

### JavaScript

- Use const/let (no var)
- Use async/await (no .then chains)
- Use template literals
- Descriptive function names

---

## Documentation Standards

### API Changes

When changing `docs/api.md`:

1. Include request/response formats
2. Document error cases
3. Add example curl commands
4. Update the changelog at the bottom

### Architecture Decision Records

Use this template for new ADRs:

```markdown
# ADR NNNN: Title

## Status
Proposed | Accepted | Deprecated

## Context
Why are we making this decision?

## Decision
What are we doing?

## Consequences
What are the tradeoffs?
```

---

## Testing

### Backend

```bash
# All tests
pytest

# Specific file
pytest tests/test_transcriber.py

# With coverage
pytest --cov=backend --cov-report=html
```

### Frontend

Manual testing for MVP. Open `frontend/index.html` in Chrome and test the workflows.

---

## PR Review Checklist

Before submitting:

- [ ] Code follows style guidelines
- [ ] Tests pass (`pytest`)
- [ ] Documentation updated (if needed)
- [ ] No hardcoded paths or secrets
- [ ] Commit messages follow conventional commits

---

## Questions?

- Check existing issues and PRs
- Open a new issue for discussion
- Tag maintainers in your PR

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
