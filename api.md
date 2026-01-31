# API Documentation

This document defines the contract between the frontend and backend. **If you change an endpoint, update this file in the same PR.**

---

## Base URL

```
http://127.0.0.1:8765
```

---

## Endpoints

### Health Check

```
GET /health
```

Returns server status and configuration info.

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

Accepts audio file, returns transcribed text.

**Request:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `audio` | file | yes | Audio file (wav, webm, mp3, ogg, m4a) |
| `language` | string | no | Language code (default: from config, or "auto") |
| `normalize` | boolean | no | Run ffmpeg normalization (default: true) |

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:8765/transcribe \
  -F "audio=@recording.webm" \
  -F "language=en"
```

**Response (200):**
```json
{
  "text": "This is the transcribed text from the audio.",
  "language": "en",
  "duration_seconds": 4.2,
  "processing_time_ms": 850
}
```

**Response (400):**
```json
{
  "error": "invalid_audio",
  "message": "Could not decode audio file"
}
```

**Response (500):**
```json
{
  "error": "transcription_failed",
  "message": "Whisper model failed to process audio"
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
| `template` | string | yes | Template name (fix_grammar, summarize, deep_research, etc.) |
| `provider` | string | no | LLM provider (anthropic, openai, ollama, cluster). Default: from config |

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:8765/refine \
  -H "Content-Type: application/json" \
  -d '{"text": "i want too go too the store", "template": "fix_grammar"}'
```

**Response (200):**
```json
{
  "text": "I want to go to the store.",
  "template": "fix_grammar",
  "provider": "anthropic",
  "model": "claude-sonnet-4-20250514",
  "processing_time_ms": 1200
}
```

**Response (400):**
```json
{
  "error": "invalid_template",
  "message": "Template 'unknown_template' not found"
}
```

**Response (503):**
```json
{
  "error": "provider_unavailable",
  "message": "Could not connect to Anthropic API"
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
  "text": "The text to append to the session log.",
  "tags": ["meeting", "idea"]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `text` | string | yes | Text to append |
| `tags` | array[string] | no | Optional tags for the entry |

**Example (curl):**
```bash
curl -X POST http://127.0.0.1:8765/session/append \
  -H "Content-Type: application/json" \
  -d '{"text": "Remember to call Bob about the project."}'
```

**Response (200):**
```json
{
  "success": true,
  "file": "transcripts/2025-01-31.md",
  "entry_number": 5,
  "timestamp": "2025-01-31T14:32:15Z"
}
```

**Session file format:**
```markdown
# Session: 2025-01-31

---

## Entry 1 — 09:15:32

Remember to pick up groceries.

---

## Entry 2 — 10:42:18 `#meeting` `#idea`

The text to append to the session log.

---
```

---

### Get Session

```
GET /session?date=YYYY-MM-DD
```

Returns contents of a session file.

**Query Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | string | no | Date in YYYY-MM-DD format (default: today) |

**Response (200):**
```json
{
  "date": "2025-01-31",
  "file": "transcripts/2025-01-31.md",
  "entries": [
    {
      "number": 1,
      "timestamp": "2025-01-31T09:15:32Z",
      "text": "Remember to pick up groceries.",
      "tags": []
    },
    {
      "number": 2,
      "timestamp": "2025-01-31T10:42:18Z",
      "text": "The text to append to the session log.",
      "tags": ["meeting", "idea"]
    }
  ],
  "entry_count": 2
}
```

**Response (404):**
```json
{
  "error": "session_not_found",
  "message": "No session file for 2025-01-30"
}
```

---

### Get Configuration

```
GET /config
```

Returns current configuration (without sensitive values).

**Response:**
```json
{
  "transcription": {
    "model": "small",
    "device": "cpu",
    "compute_type": "int8",
    "language": "en"
  },
  "session": {
    "directory": "./transcripts",
    "date_format": "%Y-%m-%d"
  },
  "llm": {
    "default_provider": "anthropic",
    "available_providers": ["anthropic", "openai", "ollama"],
    "templates": ["fix_grammar", "summarize", "deep_research", "expand"]
  },
  "cluster": {
    "enabled": false
  }
}
```

---

### List Templates

```
GET /templates
```

Returns available prompt templates.

**Response:**
```json
{
  "templates": [
    {
      "name": "fix_grammar",
      "description": "Fix grammar and spelling errors",
      "category": "refine"
    },
    {
      "name": "summarize",
      "description": "Summarize in 2-3 sentences",
      "category": "refine"
    },
    {
      "name": "deep_research",
      "description": "Convert to detailed research prompt",
      "category": "transform"
    },
    {
      "name": "expand",
      "description": "Expand brief notes into full text",
      "category": "transform"
    }
  ]
}
```

---

## WebSocket (Future: Phase 2)

### Streaming Transcription

```
WS /ws/transcribe
```

Real-time streaming transcription.

**Client → Server messages:**
```json
{"type": "start", "language": "en"}
{"type": "audio", "data": "<base64-encoded-audio-chunk>"}
{"type": "end"}
```

**Server → Client messages:**
```json
{"type": "partial", "text": "This is a partial..."}
{"type": "final", "text": "This is the final transcription.", "duration_seconds": 4.2}
{"type": "error", "message": "..."}
```

---

## Error Format

All errors follow this format:

```json
{
  "error": "error_code",
  "message": "Human-readable description"
}
```

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `invalid_audio` | 400 | Audio file could not be decoded |
| `invalid_template` | 400 | Requested template doesn't exist |
| `invalid_request` | 400 | Malformed request body |
| `session_not_found` | 404 | Session file doesn't exist |
| `transcription_failed` | 500 | Whisper failed |
| `provider_unavailable` | 503 | LLM provider unreachable |
| `cluster_unavailable` | 503 | HiveCluster unreachable |

---

## Rate Limits

No rate limits for local use. If you're somehow hitting this API so fast that it matters, you have bigger problems.

---

## CORS

Backend allows requests from:
- `http://localhost:*`
- `http://127.0.0.1:*`
- `file://` (for local HTML files)

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-01-31 | Initial API definition |
