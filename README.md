# The-Dictator

Local-first dictation that behaves like a tool — not a platform.

**Goal (MVP):** hit a MIDI pad → talk → stop → get clean text → **copy/paste anywhere** → every take appends to a running **session `.md`**.

This repo is **doc-first** on purpose. Multiple coding agents will touch it; the docs are the contract.

---

## What this is (and is not)

✅ **Local transcription** — your voice stays on your machine  
✅ **One user, one instance** — no accounts, no sync, no cloud  
✅ **Physical controls** — MIDI drum pad as command surface (48 buttons)  
✅ **Fast iteration** — simple pipeline, minimal UI, boring MVP  
✅ **Room for upgrades** — actions like "promptify", "send to LLM", routing, tagging  
✅ **Hybrid-ready** — local transcription + optional remote cluster for heavy LLM work

❌ Not a SaaS  
❌ Not a full note-taking system  
❌ Not "auto-type into focused window" on ChromeOS (security boundary, and that's fine)

---

## Architecture: Browser + Backend Split

ChromeOS + Crostini is a sandbox with two pain points:

1. **USB MIDI into the Linux container is unreliable** (often doesn't work at all)
2. **Cross-app keystroke injection is blocked** (and that's good for security)

**The solve:** Web MIDI API works directly in Chrome. So we split:

| Layer | Runs In | Responsibilities |
|-------|---------|------------------|
| **Frontend** | Chrome browser | Web MIDI capture, audio recording (MediaRecorder), transcript display, clipboard copy, button UI |
| **Backend** | Crostini (Python) | ffmpeg normalization, faster-whisper transcription, session `.md` writing, (optional) cluster API relay |

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CHROME BROWSER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │
│  │  Web MIDI   │  │  MediaRec   │  │      Transcript Panel       │ │
│  │  (48 pads)  │  │  (audio)    │  │  [edit] [copy] [append]     │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────────┘ │
│         │                │                       ▲                   │
│         └────────┬───────┘                       │                   │
│                  ▼                               │                   │
│         ┌───────────────┐              ┌────────┴────────┐          │
│         │   WebSocket   │◄────────────►│   REST/WS API   │          │
│         └───────┬───────┘              └─────────────────┘          │
└─────────────────┼───────────────────────────────────────────────────┘
                  │ localhost:8765
┌─────────────────┼───────────────────────────────────────────────────┐
│                 ▼              CROSTINI (Linux)                      │
│         ┌───────────────┐                                            │
│         │  Python API   │                                            │
│         │   (FastAPI)   │                                            │
│         └───────┬───────┘                                            │
│                 │                                                    │
│    ┌────────────┼────────────┬─────────────────┐                    │
│    ▼            ▼            ▼                 ▼                    │
│ ┌──────┐  ┌──────────┐  ┌─────────┐  ┌─────────────────┐           │
│ │ffmpeg│  │ faster-  │  │ Session │  │  Cluster Relay  │           │
│ │ norm │  │ whisper  │  │ Logger  │  │   (optional)    │           │
│ └──────┘  └──────────┘  └─────────┘  └────────┬────────┘           │
│                                               │                     │
└───────────────────────────────────────────────┼─────────────────────┘
                                                │ Tailscale (optional)
                                    ┌───────────▼───────────┐
                                    │      HiveCluster      │
                                    │  (Qwen 72B, deep LLM) │
                                    └───────────────────────┘
```

See: [`docs/architecture.md`](docs/architecture.md) and ADR [`docs/adr/0001-browser-ui-split.md`](docs/adr/0001-browser-ui-split.md)

---

## MVP Features

- [ ] **Record / Stop** — browser button + MIDI pad trigger
- [ ] **Local transcription** — `faster-whisper` (default) or `whisper.cpp` (ARM-friendly)
- [ ] **Transcript panel** — editable text area in browser
- [ ] **Copy button** — clipboard via `navigator.clipboard`
- [ ] **Append to session** — writes to `transcripts/YYYY-MM-DD.md`
- [ ] **Minimal config** — `config.example.toml`

Contract details: [`docs/api.md`](docs/api.md)

---

## Directory Structure (Agent Contract)

> **⚠️ AGENTS:** Adhere strictly to this structure. If you need to change it, update this README and add an ADR.

```
The-Dictator/
├── README.md                    # You are here
├── LICENSE                      # MIT
├── CONTRIBUTING.md              # PR rules, code style
├── pyproject.toml               # Python package config
│
├── config/                      # User configuration (gitignored)
│   ├── settings.toml            # API endpoints, audio device, model choice
│   └── button_map.toml          # MIDI note → action mapping
│
├── docs/                        # The contract
│   ├── architecture.md          # System design deep-dive
│   ├── api.md                   # Backend endpoint specs
│   ├── agent-playbook.md        # Rules for coding agents
│   └── adr/                     # Architecture Decision Records
│       └── 0001-browser-ui-split.md
│
├── frontend/                    # Browser UI (vanilla JS or Svelte)
│   ├── index.html
│   ├── app.js                   # Web MIDI, MediaRecorder, WS client
│   ├── style.css
│   └── components/              # UI components (if using framework)
│
├── backend/                     # Python API server
│   ├── __init__.py
│   ├── main.py                  # FastAPI app, entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py            # /transcribe, /health, /config
│   │   └── websocket.py         # Real-time audio streaming (future)
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── transcriber.py       # faster-whisper wrapper
│   │   ├── normalizer.py        # ffmpeg audio preprocessing
│   │   └── cluster.py           # HiveCluster relay client (optional)
│   ├── output/
│   │   ├── __init__.py
│   │   ├── session_logger.py    # Markdown session file writer
│   │   └── clipboard.py         # wl-copy fallback (if needed)
│   └── config/
│       ├── __init__.py
│       ├── loader.py            # TOML config parser
│       └── models.py            # Pydantic settings models
│
├── transcripts/                 # Session logs (gitignored content)
│   └── .gitkeep
│
├── models/                      # Whisper model weights (gitignored)
│   └── .gitkeep
│
├── scripts/                     # Dev/ops utilities
│   ├── download_model.sh        # Fetch whisper model
│   └── dev.sh                   # Start backend + serve frontend
│
└── tests/
    ├── test_transcriber.py
    ├── test_api.py
    └── test_session_logger.py
```

---

## Repo Rules (So We Don't Melt Down)

1. **Docs are the contract.** If you change an endpoint or payload → update `docs/api.md` in the same PR.

2. **Architectural changes require ADRs.** Add/modify a file in `docs/adr/` explaining the why.

3. **Keep the MVP boring.** Fancy comes after "works every time."

4. **Config is gitignored.** Commit `config.example.toml`, never `config/settings.toml`.

5. **One agent, one module.** If two agents need to touch the same file, coordinate via PR or docs first.

See: [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`docs/agent-playbook.md`](docs/agent-playbook.md)

---

## Quick Start

### Prerequisites

- ChromeOS with Crostini enabled (or any Linux)
- Python 3.10+
- FFmpeg
- Node.js (optional, for frontend dev server)
- MIDI controller (optional, keyboard fallback available)

### Installation

```bash
# Clone
git clone https://github.com/yourusername/The-Dictator.git
cd The-Dictator

# Backend setup
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Download Whisper model
./scripts/download_model.sh small

# Copy example config
cp config.example.toml config/settings.toml

# Run
./scripts/dev.sh
# Opens browser to http://localhost:8000
```

### MIDI Button Map (Default)

| Pad | Note | Action |
|-----|------|--------|
| 1 | 36 | Toggle recording |
| 2 | 37 | Transcribe → Copy |
| 3 | 38 | Transcribe → Refine → Copy |
| 4 | 39 | Append to session |
| 5 | 40 | Send to Claude |
| 6 | 41 | Send to ChatGPT |
| 7 | 42 | Send to Ollama (local) |
| 8 | 43 | Send to HiveCluster |
| 9-12 | 44-47 | Prompt templates |
| 13-16 | 48-51 | Reserved / Quit |

Full mapping: `config/button_map.toml`

---

## Roadmap

### Phase 1: MVP (Current)
- [ ] Backend: `/transcribe` endpoint with faster-whisper
- [ ] Backend: Session logger (`transcripts/YYYY-MM-DD.md`)
- [ ] Frontend: Record/Stop button
- [ ] Frontend: Transcript panel with Copy button
- [ ] Frontend: Web MIDI integration
- [ ] Config: `settings.toml` + `button_map.toml`

### Phase 2: Polish
- [ ] Audio normalization (ffmpeg preprocessing)
- [ ] VAD (voice activity detection) for auto-stop
- [ ] WebSocket for real-time partial transcripts
- [ ] Settings UI in browser

### Phase 3: LLM Integration
- [ ] Anthropic API client
- [ ] OpenAI API client
- [ ] Ollama (local) client
- [ ] HiveCluster relay for Qwen 72B
- [ ] Prompt template system (Jinja2)
- [ ] "Deep Research Prompt" action

### Phase 4: Advanced
- [ ] Multiple transcription backends (whisper.cpp)
- [ ] Speaker diarization
- [ ] Export formats (SRT, VTT)
- [ ] Browser extension for "paste into active tab"

---

## Tech Stack

| Component | Choice | Why |
|-----------|--------|-----|
| Backend framework | FastAPI | Async, WebSocket support, Pydantic |
| Transcription | faster-whisper | 4x faster than OpenAI Whisper, int8 CPU |
| Audio processing | ffmpeg | Battle-tested, handles any format |
| Frontend | Vanilla JS (MVP) | No build step, works everywhere |
| MIDI | Web MIDI API | Works in Chrome, bypasses Crostini |
| Config | TOML | Human-readable, Python-native |
| Session logs | Markdown | Portable, version-controllable |

---

## License

MIT — see [LICENSE](LICENSE)

---

## Acknowledgments

- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — The engine
- [whisper-writer](https://github.com/savbell/whisper-writer) — Inspiration
- [nerd-dictation](https://github.com/ideasman42/nerd-dictation) — Simplicity goals
