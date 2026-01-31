# Architecture

This document describes The-Dictator's system architecture, design decisions, and component interactions.

---

## Design Philosophy

1. **Local-first** — Your voice data never leaves your machine (unless you explicitly send it to an LLM API)
2. **Browser + Backend split** — Solve ChromeOS limitations by putting MIDI/audio in the browser
3. **Doc-first** — Multiple agents work on this codebase; documentation is the contract
4. **Boring MVP** — Get the basic flow working before adding fancy features

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CHROME BROWSER                               │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                        Frontend (app.js)                      │  │
│  │                                                               │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │  │
│  │  │  Web MIDI   │  │ MediaRec    │  │   State Manager     │  │  │
│  │  │  Handler    │  │ Handler     │  │   (recording,       │  │  │
│  │  │             │  │             │  │    transcript)      │  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │  │
│  │         │                │                     │             │  │
│  │         └────────────────┼─────────────────────┘             │  │
│  │                          ▼                                    │  │
│  │                 ┌─────────────────┐                          │  │
│  │                 │  Action Router  │                          │  │
│  │                 │  (button_map)   │                          │  │
│  │                 └────────┬────────┘                          │  │
│  │                          │                                    │  │
│  │         ┌────────────────┼────────────────┐                  │  │
│  │         ▼                ▼                ▼                  │  │
│  │  ┌───────────┐   ┌───────────┐   ┌────────────────┐         │  │
│  │  │  Record   │   │   Copy    │   │  Send to API   │         │  │
│  │  │  Toggle   │   │ Clipboard │   │  (transcribe)  │         │  │
│  │  └───────────┘   └───────────┘   └───────┬────────┘         │  │
│  │                                          │                   │  │
│  └──────────────────────────────────────────┼───────────────────┘  │
│                                             │                       │
└─────────────────────────────────────────────┼───────────────────────┘
                                              │
                              HTTP POST /transcribe (multipart audio)
                              WebSocket /ws (future: streaming)
                                              │
┌─────────────────────────────────────────────┼───────────────────────┐
│                    CROSTINI (Linux Container)                        │
│                                             │                        │
│  ┌──────────────────────────────────────────▼───────────────────┐   │
│  │                     Backend (FastAPI)                         │   │
│  │                                                               │   │
│  │  ┌─────────────────────────────────────────────────────────┐ │   │
│  │  │                    API Routes                            │ │   │
│  │  │                                                          │ │   │
│  │  │  POST /transcribe     - Accept audio, return text        │ │   │
│  │  │  POST /refine         - Send text to LLM, return refined │ │   │
│  │  │  POST /session/append - Append to session markdown       │ │   │
│  │  │  GET  /health         - Healthcheck                      │ │   │
│  │  │  GET  /config         - Return current config            │ │   │
│  │  │  WS   /ws             - (future) streaming audio         │ │   │
│  │  │                                                          │ │   │
│  │  └──────────────────────────┬──────────────────────────────┘ │   │
│  │                             │                                 │   │
│  │         ┌───────────────────┼───────────────────┐            │   │
│  │         ▼                   ▼                   ▼            │   │
│  │  ┌────────────┐     ┌────────────┐     ┌─────────────┐       │   │
│  │  │ Normalizer │     │Transcriber │     │ LLM Clients │       │   │
│  │  │  (ffmpeg)  │     │ (faster-   │     │ (anthropic, │       │   │
│  │  │            │     │  whisper)  │     │  openai,    │       │   │
│  │  └────────────┘     └────────────┘     │  ollama)    │       │   │
│  │                                        └──────┬──────┘       │   │
│  │                                               │              │   │
│  │                                    ┌──────────▼──────────┐   │   │
│  │                                    │   Cluster Relay     │   │   │
│  │                                    │   (HiveCluster)     │   │   │
│  │                                    └──────────┬──────────┘   │   │
│  │                                               │              │   │
│  └───────────────────────────────────────────────┼──────────────┘   │
│                                                  │                   │
└──────────────────────────────────────────────────┼───────────────────┘
                                                   │
                                        Tailscale mesh (optional)
                                                   │
                                    ┌──────────────▼──────────────┐
                                    │        HiveCluster          │
                                    │   (Qwen 72B, heavy LLM)     │
                                    │   4-node heterogeneous GPU  │
                                    └─────────────────────────────┘
```

---

## Component Details

### Frontend (Browser)

**Location:** `frontend/`

**Responsibilities:**
- Web MIDI API integration (48-button drum pad)
- Audio recording via MediaRecorder API
- Clipboard operations via `navigator.clipboard`
- UI state management
- HTTP/WebSocket communication with backend

**Why browser?**
- Web MIDI works in Chrome, bypassing Crostini's USB MIDI limitation
- MediaRecorder gives us good audio quality with minimal code
- Clipboard API is reliable across platforms
- No build step needed for MVP (vanilla JS)

**Key files:**
- `index.html` — Single-page UI
- `app.js` — Main application logic
- `midi.js` — Web MIDI handling
- `recorder.js` — MediaRecorder wrapper

### Backend (Crostini)

**Location:** `backend/`

**Responsibilities:**
- Audio preprocessing (ffmpeg normalization)
- Speech-to-text (faster-whisper)
- Session markdown file management
- LLM API relay (optional)
- Cluster relay to HiveCluster (optional)

**Why Python/FastAPI?**
- faster-whisper is Python-native
- FastAPI handles async well for future WebSocket streaming
- Pydantic for config validation
- Easy to test

**Key modules:**
- `api/routes.py` — HTTP endpoints
- `engine/transcriber.py` — faster-whisper wrapper
- `engine/normalizer.py` — ffmpeg preprocessing
- `engine/cluster.py` — HiveCluster relay
- `output/session_logger.py` — Markdown file writer

---

## Data Flow

### Basic Transcription

```
1. User presses MIDI pad (or clicks Record button)
2. Frontend starts MediaRecorder
3. User speaks
4. User presses pad again (or clicks Stop)
5. Frontend stops MediaRecorder, gets audio Blob
6. Frontend POSTs audio to backend /transcribe
7. Backend runs ffmpeg normalization
8. Backend runs faster-whisper
9. Backend returns { "text": "transcribed text" }
10. Frontend displays in transcript panel
11. User clicks Copy → clipboard
12. User clicks Append → POST /session/append
```

### LLM Refinement

```
1. User has transcription in panel
2. User presses "Refine" MIDI pad
3. Frontend POSTs to /refine with text + template name
4. Backend loads prompt template
5. Backend calls LLM API (or HiveCluster)
6. Backend returns refined text
7. Frontend updates transcript panel
```

---

## Configuration

### settings.toml

```toml
[server]
host = "127.0.0.1"
port = 8765

[audio]
sample_rate = 16000
channels = 1

[transcription]
model = "small"           # tiny, base, small, medium, large-v3
device = "cpu"            # cpu or cuda
compute_type = "int8"     # int8, float16, float32
language = "en"           # or "auto"

[session]
directory = "./transcripts"
date_format = "%Y-%m-%d"

[llm.anthropic]
model = "claude-sonnet-4-20250514"
# API key from ANTHROPIC_API_KEY env var

[llm.ollama]
base_url = "http://localhost:11434"
model = "llama3.2"

[cluster]
enabled = false
endpoint = "http://hivecluster.local:8080"
# Auth via CLUSTER_API_KEY env var
```

### button_map.toml

```toml
[midi]
36 = "toggle_recording"
37 = "transcribe"
38 = "copy"
39 = "append_session"
40 = "refine:fix_grammar"
41 = "refine:summarize"
42 = "refine:deep_research"
43 = "send_to:claude"
44 = "send_to:chatgpt"
45 = "send_to:ollama"
46 = "send_to:cluster"

[keyboard]
"ctrl+shift+r" = "toggle_recording"
"ctrl+shift+t" = "transcribe"
"ctrl+shift+c" = "copy"
```

---

## Security Considerations

1. **Audio stays local** — Never sent to cloud unless explicitly configured for LLM APIs
2. **No auth on localhost** — Backend only listens on 127.0.0.1
3. **API keys in env vars** — Never in config files or code
4. **Cluster connection via Tailscale** — Encrypted mesh, no public exposure

---

## Future Considerations

### WebSocket Streaming (Phase 2)

Replace HTTP POST with WebSocket for real-time partial transcripts:

```
Frontend                    Backend
   │                           │
   │──── WS connect ──────────►│
   │                           │
   │◄─── connected ────────────│
   │                           │
   │──── audio chunk ─────────►│
   │                           │
   │◄─── partial text ─────────│
   │                           │
   │──── audio chunk ─────────►│
   │                           │
   │◄─── partial text ─────────│
   │                           │
   │──── end stream ──────────►│
   │                           │
   │◄─── final text ───────────│
```

### Multiple Transcription Backends (Phase 4)

Abstract the transcriber interface to support:
- faster-whisper (default)
- whisper.cpp (for ARM/low-memory)
- OpenAI API (for comparison/fallback)

```python
class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> str: ...
    
class FasterWhisperTranscriber:
    def transcribe(self, audio_path: Path) -> str: ...
    
class WhisperCppTranscriber:
    def transcribe(self, audio_path: Path) -> str: ...
```
