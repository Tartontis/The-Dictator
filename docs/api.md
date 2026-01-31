# API Documentation

This document defines the contract between the frontend and backend. **If you change an endpoint, update this file in the same PR.**

---

## Base URL

```
http://127.0.0.1:8765/api
```

---

## Endpoints

### Health Check

```
GET /health
```

Returns server status and core configuration info.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "transcription_model": "small",
  "session_directory": "./transcripts"
}
```

---

### Transcribe Audio

```
POST /transcribe
Content-Type: multipart/form-data
```

Accepts an audio file and returns the transcribed text.

**Request:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | yes | Audio file (wav, webm, mp3, ogg, m4a, etc.) |

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:8765/api/transcribe \
  -F "file=@recording.webm"
```

**Response (200):**
```json
{
  "text": "This is the transcribed text from the audio."
}
```

**Response (500):**
```json
{
  "detail": "<error message>"
}
```

---

### Refine Text with LLM

```
POST /refine
Content-Type: application/json
```

Sends text to an LLM with a prompt template.

**Request:**
```json
{
  "text": "the text to refine",
  "template": "fix_grammar",
  "provider": "anthropic"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Text to refine |
| `template` | string | yes | Template name (e.g. fix_grammar, summarize) |
| `provider` | string | no | LLM provider (anthropic, openai, ollama). Default: from config |

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:8765/api/refine \
  -H "Content-Type: application/json" \
  -d '{"text": "i want too go too the store", "template": "fix_grammar"}'
```

**Response (200):**
```json
{
  "text": "I want to go to the store."
}
```

**Response (500):**
```json
{
  "detail": "<error message>"
}
```

---

### Append to Session

```
POST /session/append
Content-Type: application/json
```

Appends text to today's session markdown file.

**Request:**
```json
{
  "text": "The text to append to the session log."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Text to append |

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:8765/api/session/append \
  -H "Content-Type: application/json" \
  -d '{"text": "Remember to call Bob about the project."}'
```

**Response (200):**
```json
{
  "status": "success",
  "file": "transcripts/2025-01-31.md"
}
```

**Response (500):**
```json
{
  "detail": "<error message>"
}
```

---

### Get Configuration

```
GET /config
```

Returns the current configuration as loaded from `config/settings.toml` (or the example file when missing).

**Response:**
```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 8765
  },
  "audio": {
    "sample_rate": 16000,
    "channels": 1,
    "normalize": true
  },
  "transcription": {
    "model": "small",
    "device": "cpu",
    "compute_type": "int8",
    "language": "en"
  },
  "vad": {
    "enabled": true,
    "threshold": 0.5,
    "min_speech_duration": 0.25,
    "min_silence_duration": 1.0
  },
  "session": {
    "directory": "./transcripts",
    "date_format": "%Y-%m-%d",
    "include_timestamps": true
  },
  "llm": {
    "default_provider": "anthropic",
    "anthropic": {
      "model": "claude-sonnet-4-20250514",
      "max_tokens": 1024
    },
    "openai": {
      "model": "gpt-4o",
      "max_tokens": 1024
    },
    "ollama": {
      "base_url": "http://localhost:11434",
      "model": "llama3.2"
    }
  },
  "cluster": {
    "enabled": false,
    "endpoint": "http://hivecluster.local:8080"
  },
  "templates": {
    "directory": "./prompts",
    "default": "fix_grammar"
  }
}
```

---

## WebSocket (Future: Phase 2)

### Streaming Transcription

```
WS /ws/transcribe
```

Real-time streaming transcription (not implemented yet).

---

## CORS

Backend allows requests from any origin (configured via `allow_origins=["*"]`).

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01-31 | Initial API definition (aligned to current endpoints) |
