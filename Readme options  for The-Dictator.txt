Readme options. for The-Dictator

# padscribe

Local-first dictation that behaves like a tool — not a platform.

**Goal (MVP):** hit a MIDI pad → talk → stop → get clean text → **copy/paste anywhere** → and every take gets appended into a running **session `.md`**.

This repo is **doc-first** on purpose. Multiple coding agents will touch it; the docs are the contract.

---

## What this is (and is not)

✅ **Local transcription** (no “upload your brain to someone else”)  
✅ **One user, one instance**  
✅ **Fast iteration** (simple pipeline, minimal UI)  
✅ **Room for upgrades** (actions like “promptify”, “open LLM”, routing, tagging)

❌ Not a SaaS  
❌ Not trying to be a full note system  
❌ Not “auto-type into the focused window” on ChromeOS (security boundary)

---

## Why browser UI on Chromebook

ChromeOS + Linux (Crostini) is a sandbox. Two pain points matter:

- **USB MIDI into the Linux container is unreliable**.
- **Cross-app keystroke injection is blocked** (and that’s good).

So the most reliable approach is:

- **Frontend (Browser):** Web MIDI + recording + clipboard ergonomics  
- **Backend (Linux container):** ffmpeg normalize + local Whisper transcription + file writing

See: `docs/architecture.md` and ADR `docs/adr/0001-browser-ui-split.md`.

---

## MVP features

- Record / stop (button + MIDI mapping)
- Local transcription engine
  - default: `faster-whisper`
  - optional: `whisper.cpp` (CPU/ARM-friendly)
- Transcript panel (editable)
- **Copy** button (clipboard)
- **Append to session** button (writes to `transcripts/YYYY-MM-DD.md`)
- Minimal config file (`config.example.toml`)

Contract details live in `docs/api.md`.

---

## Repo rules (so we don’t melt down)

- If you change an endpoint or payload: **update `docs/api.md`** in the same PR.
- If you change an architectural decision: add/modify an **ADR** in `docs/adr/`.
- Keep the MVP boring. Fancy comes after “works every time”.

See `CONTRIBUTING.md` and `docs/agent-playbook.md`.

---

## Planned structure (once code scaffolding lands)






# The-Dictator

Local-first dictation that behaves like a tool — not a platform.

**Goal (MVP):** hit a MIDI pad → talk → stop → get clean text → **copy/paste anywhere** → and every take gets appended into a running **session `.md`**.

This repo is **doc-first** on purpose. Multiple coding agents will touch it; the docs are the contract.

---

## What this is (and is not)

✅ **Local transcription** (no “upload your brain to someone else”)  
✅ **One user, one instance**  
✅ **Fast iteration** (simple pipeline, minimal UI)  
✅ **Room for upgrades** (actions like “promptify”, “open LLM”, routing, tagging)

❌ Not a SaaS  
❌ Not trying to be a full note system  
❌ Not “auto-type into the focused window” on ChromeOS (security boundary)

---

## Why browser UI on Chromebook

ChromeOS + Linux (Crostini) is a sandbox. Two pain points matter:

- **USB MIDI into the Linux container is unreliable**.
- **Cross-app keystroke injection is blocked** (and that’s good).

So the most reliable approach is:

- **Frontend (Browser):** Web MIDI + recording + clipboard ergonomics  
- **Backend (Linux container):** ffmpeg normalize + local Whisper transcription + file writing

See: `docs/architecture.md` and ADR `docs/adr/0001-browser-ui-split.md`.

---

## MVP features

- Record / stop (button + MIDI mapping)
- Local transcription engine
  - default: `faster-whisper`
  - optional: `whisper.cpp` (CPU/ARM-friendly)
- Transcript panel (editable)
- **Copy** button (clipboard)
- **Append to session** button (writes to `transcripts/YYYY-MM-DD.md`)
- Minimal config file (`config.example.toml`)

Contract details live in `docs/api.md`.

---

## Repo rules (so we don’t melt down)

- If you change an endpoint or payload: **update `docs/api.md`** in the same PR.
- If you change an architectural decision: add/modify an **ADR** in `docs/adr/`.
- Keep the MVP boring. Fancy comes after “works every time”.

See `CONTRIBUTING.md` and `docs/agent-playbook.md`.

---

## Planned structure (once code scaffolding lands)



# The-Dictator

**The-Dictator** is a modular, hybrid-local voice command center designed for Linux (specifically ChromeOS Crostini) that integrates local transcription with remote high-performance compute clusters.

It uses a MIDI drum pad as a physical control surface to trigger dictation, AI refinement, and system automation.

## 🏗 Architecture

The system operates on a **Hybrid Architecture**:
1.  **Local Node (The Client):**
    * **Hardware:** Chromebook / Linux Laptop + MIDI Controller.
    * **Responsibility:** Audio capture, MIDI event listening, `faster-whisper` (Small/Base) transcription, Clipboard injection.
    * **Latency:** Critical (<200ms target).
2.  **Remote Node (The Brain):**
    * **Hardware:** Custom "Dual-Wired Airlock" Compute Cluster.
    * **Responsibility:** Heavy lifting. Receives raw text, applies LLM (Qwen 2.5 72B) logic for "Deep Research" prompt refinement, and returns structured data.

## 📂 Directory Structure (Agent Contract)

**ATTENTION AGENTS:** Please adhere strictly to this structure to prevent conflicts.

```text
The-Dictator/
├── config/             # User configuration (GitIgnored)
│   ├── settings.yaml   # API endpoints, Audio device IDs
│   └── key_map.yaml    # MIDI Note mapping
├── src/
│   ├── capture/        # Input handling
│   │   ├── audio.py    # PyAudio/SoundDevice logic
│   │   └── midi.py     # Mido/RtMidi listener loops
│   ├── engine/         # Processing logic
│   │   ├── transcriber.py # Local Faster-Whisper implementation
│   │   └── cluster.py  # API client for Remote LLM (Qwen)
│   ├── output/         # System interaction
│   │   ├── injector.py # Keyboard/Clipboard injection (wl-copy)
│   │   └── logger.py   # Markdown session logging
│   └── utils/          # Shared helpers
├── models/             # Local model weights (GitIgnored)
├── logs/               # Application logs
├── main.py             # Entry point / Event Orchestrator
└── requirements.txt