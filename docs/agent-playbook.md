# Agent Playbook

Rules and guidelines for coding agents (Claude, GPT, Cursor, etc.) working on The-Dictator.

---

## The Prime Directive

**Docs are the contract.** If you're unsure about something, check the docs first. If the docs don't answer your question, ask before assuming.

---

## Before You Write Code

1. **Read the relevant docs:**
   - `README.md` — Project overview and structure
   - `docs/architecture.md` — System design
   - `docs/api.md` — Backend API contract
   - Any relevant ADRs in `docs/adr/`

2. **Check the directory structure** in README.md. Your files go in specific places.

3. **Check for existing code** that does something similar. Don't duplicate.

---

## File Ownership

To prevent merge conflicts when multiple agents work simultaneously:

| Module | Primary Responsibility |
|--------|------------------------|
| `frontend/app.js` | UI state, main coordination |
| `frontend/midi.js` | Web MIDI handling only |
| `frontend/recorder.js` | MediaRecorder handling only |
| `backend/api/routes.py` | HTTP endpoint definitions |
| `backend/engine/transcriber.py` | faster-whisper wrapper |
| `backend/engine/normalizer.py` | ffmpeg wrapper |
| `backend/engine/cluster.py` | HiveCluster relay |
| `backend/output/session_logger.py` | Markdown file operations |

**Rule:** If you need to modify a file another agent is working on, coordinate first (via PR description or docs).

---

## Code Style

### Python (Backend)

```python
# Use type hints
def transcribe(audio_path: Path, language: str = "en") -> str:
    ...

# Use Pydantic for data models
from pydantic import BaseModel

class TranscribeResponse(BaseModel):
    text: str
    language: str
    duration_seconds: float
    processing_time_ms: int

# Use pathlib, not os.path
from pathlib import Path
audio_file = Path("./audio.wav")

# Use f-strings
message = f"Transcribed {duration:.2f} seconds of audio"

# Async where it makes sense (FastAPI routes)
@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile) -> TranscribeResponse:
    ...
```

### JavaScript (Frontend)

```javascript
// Use const/let, never var
const audioContext = new AudioContext();
let isRecording = false;

// Use async/await, not .then() chains
async function transcribe(audioBlob) {
  const response = await fetch('/transcribe', {
    method: 'POST',
    body: createFormData(audioBlob)
  });
  return await response.json();
}

// Use template literals
const message = `Transcribed ${duration} seconds`;

// Descriptive function names
function handleMidiNoteOn(note, velocity) { ... }
function updateTranscriptPanel(text) { ... }
```

---

## Documentation Requirements

### When changing an API endpoint:

Update `docs/api.md` in the same PR. Include:
- Request format
- Response format
- Error cases
- Example curl command

### When making an architectural decision:

Add an ADR to `docs/adr/`. Use the template:

```markdown
# ADR NNNN: Title

## Status
Proposed | Accepted | Deprecated | Superseded by ADR XXXX

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?
```

### When adding a new feature:

Update README.md roadmap checkboxes.

---

## Testing

### Backend

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_transcriber.py

# Run with coverage
pytest --cov=backend
```

Write tests for:
- Happy path
- Error cases
- Edge cases (empty audio, very long audio, etc.)

### Frontend

MVP uses manual testing. Future: add Playwright tests.

---

## Commit Messages

Use conventional commits:

```
feat: add LLM refinement endpoint
fix: handle empty audio files gracefully
docs: update API docs for /refine endpoint
refactor: extract ffmpeg logic to normalizer module
test: add tests for session logger
chore: update dependencies
```

---

## PR Guidelines

1. **One feature/fix per PR** — Keep PRs focused and reviewable.

2. **Update docs** — If you change behavior, update the relevant docs.

3. **Include tests** — For backend changes, include tests.

4. **Describe what you did** — PR description should explain the change.

5. **Link to issues** — If fixing a bug or implementing a feature request.

---

## Common Pitfalls

### Don't

- ❌ Modify `config/settings.toml` (it's gitignored)
- ❌ Hardcode paths (use config or Path objects)
- ❌ Add API keys to code or config files
- ❌ Make breaking API changes without updating docs
- ❌ Add dependencies without updating requirements
- ❌ Assume MIDI works in Crostini (it doesn't)

### Do

- ✅ Use `config.example.toml` as reference
- ✅ Use `config/settings.example.toml` as reference
- ✅ Use environment variables for secrets
- ✅ Keep the MVP boring and working
- ✅ Ask if you're unsure about architecture
- ✅ Test on ChromeOS/Crostini if possible

---

## Getting Help

1. Check the docs first
2. Check existing code for patterns
3. If still stuck, ask in the PR or issue

---

## Quick Reference

### Project Structure
```
The-Dictator/
├── frontend/          # Browser UI
├── backend/           # Python API
├── docs/              # Documentation (the contract)
├── config/            # User config (gitignored)
├── transcripts/       # Session logs (gitignored)
├── models/            # Whisper models (gitignored)
└── tests/             # Test files
```

### Key Files
- `docs/api.md` — API contract
- `docs/architecture.md` — System design
- `config.example.toml` — Config template
- `config/settings.example.toml` — Config template
- `backend/main.py` — Entry point

### Commands
```bash
# Start dev server
./scripts/dev.sh

# Run tests
pytest

# Download Whisper model
./scripts/download_model.sh small
```
