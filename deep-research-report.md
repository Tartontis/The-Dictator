# Local-First, MIDI-Triggered Dictation on ChromeOS: Monorepo Research, Architecture, and Repo Foundations

## Design goals distilled from the user context

The target app is a personal “instrument,” not a platform: a minimal dictation loop that optimizes for *speed-to-text* and *low friction*, while keeping clear seams for future automation. The core workflow is:

A 16-pad MIDI drum controller (three banks) triggers “voice notes.” Each note is recorded, transcribed locally (preferably with **faster-whisper** or **whisper.cpp**), then presented in a minimal UI for quick edits and copying. Each session accumulates a running Markdown log with all dictations appended in order.

ChromeOS changes the implementation strategy, not the intent. The architecture must embrace two processes:

- A **Chrome-side PWA/web app**: MIDI input, mic capture, clipboard writing, UI editing/copying, and session UX.
- A **Crostini-side backend service**: ffmpeg normalization, Whisper engine execution, model loading/management, and durable session file storage.

The rest of the repository work (contracts, CI, governance) is primarily about ensuring that multiple agents (human and automated) can collaborate without causing interface drift, duplicated logic, or “mystery behavior.”

## ChromeOS technical limitations and validated workarounds

ChromeOS’s Linux environment (Crostini) runs in a VM-to-container stack designed around strong isolation. That isolation is the reason your Linux-era conveniences (clipboard automation, MIDI passthrough) become unreliable or intentionally blocked unless you move the right responsibilities to the Chrome-side process.

### Clipboard automation from Crostini is intentionally blocked

The ChromeOS Linux FAQ states that only limited copy/paste formats are supported (currently only `text/plain`) and—critically—that **reading/writing the clipboard automatically from inside the VM is “Currently, no,”** due to the risk of untrusted code silently extracting user clipboard contents. It further notes that local X tools may maintain a local buffer but *won’t automatically sync with the system clipboard*. citeturn5view0

**Workaround:** perform clipboard writes on the **Chrome-side web app**. The browser Clipboard API supports writing with either `clipboard-write` permission or transient activation, and if the permission is granted it can persist (reducing friction for repeated dictation). citeturn10search3

### Native messaging across the ChromeOS host ↔ Crostini boundary is not dependable

Chrome extensions can generally use native messaging to talk to native host binaries on supported desktop platforms. citeturn1search9  
However, a Chromium Extensions discussion attributes ChromeOS failures to the container/VM design: **“Chrome OS cannot directly access the resources required for native messaging due to the security boundary between VMs and the host OS.”** citeturn1search1

**Workaround:** use **localhost HTTP/WebSocket** bridging instead of native messaging.

### Localhost tunneling into Crostini is supported and documented

Chromium OS security documentation explicitly states that ChromeOS will forward ports from `localhost` into Crostini, enabling the host browser to access a development server inside the container. citeturn0search0  
ChromeOS developer documentation also describes the user-facing port forwarding controls for exposing a Linux dev server to other devices when needed (though a dictation backend should default to localhost-only). citeturn0search6

**Workaround:** run the transcription backend inside Crostini and expose it on a localhost-forwarded port. The PWA calls it as a local service.

### USB MIDI passthrough to Crostini is unreliable; Web MIDI is the robust control plane

A Chromium OS discussion thread reports a common failure mode: USB MIDI controllers are visible to Chrome, but **do not appear as shareable USB devices** to the Linux container in Settings—undercutting any “Linux listens to raw MIDI” MVP assumption. citeturn8search3  
Independent investigation from McLaren Labs also reports that external USB MIDI devices (at least in their testing) do not pass through events to the Linux environment, reinforcing “don’t bet the MVP on Crostini MIDI.” citeturn8search2

**Workaround:** handle MIDI on the Chrome side using Web MIDI, then forward *commands* (start/stop/transcribe/bank select) to the backend.

Web MIDI is designed with an explicit security model; user agents may require approval before granting access to MIDI devices. citeturn0search2  
Chrome’s rollout tightened this further: starting in Chrome 124, access to the Web MIDI API is gated behind a permission prompt. citeturn0search1turn0search4  
MDN additionally notes Web MIDI must be called in a secure context and permission must be granted (or previously granted). citeturn0search11

### Secure context and “localhost” practicality for a local PWA

Many “powerful features” require a secure context. The W3C Secure Contexts spec notes user agents **may treat localhost as potentially trustworthy** (subject to resolution rules). citeturn11search0  
Older but still widely-cited “powerful features” criteria explicitly special-case `localhost` and `127.0.0.0/8` as potentially trustworthy origins. citeturn11search16

**Workaround:** serve the PWA from `http://localhost` (or a local HTTPS origin) via the same backend process so both Web MIDI and Clipboard API constraints are easier to satisfy.

### Crostini lifecycle implications for “daily driver” tooling

ChromeOS’s container/VM runtime is intentionally non-persistent across logout: processes don’t survive logout and do not autorun at login or boot to reduce persistent exploit risk. citeturn12view0  
Additionally, container content requires the container to be running to access it through “Linux Files.” citeturn5view0

**Workaround:** provide a one-command developer script (`./scripts/dev_chromeos.sh`) that starts backend + serves the PWA, rather than assuming a background daemon.

## Two-process architecture and data flow

The architecture below is shaped directly by the constraints above: the browser owns MIDI + clipboard; Crostini owns models + ffmpeg + durable logs; localhost bridging replaces native messaging.

### Architecture diagram

```mermaid
flowchart LR
  subgraph Host[ChromeOS (Host)]
    Pad[MIDI Drum Pad\n16 pads × 3 banks]
    PWA[Installed PWA / Web App\nWeb MIDI + Mic capture\nEdit + Copy UI\nClipboard write]
    Pad -->|Web MIDI| PWA
  end

  subgraph Crostini[Crostini (Linux container in VM)]
    API[STT Backend Service\nHTTP on localhost port]
    FFMPEG[ffmpeg normalize\n(16kHz mono PCM)]
    Engine[STT Engine Adapter\nfaster-whisper or whisper.cpp]
    Store[Session Store\nMarkdown logs + metadata]
    API --> FFMPEG --> Engine --> API
    API --> Store
  end

  PWA <--> |localhost tunneled port| API
```

This is the “Chrome-first control plane” model: ChromeOS forwards localhost ports into Crostini, allowing the host browser to access the backend. citeturn0search0  
It also avoids native messaging pitfalls on ChromeOS. citeturn1search1

### Event and data sequence (pad hit → transcript → clipboard + session log)

```mermaid
sequenceDiagram
  participant MIDI as MIDI Pad (Web MIDI)
  participant UI as PWA UI (Chrome)
  participant S as Backend Service (Crostini)
  participant F as ffmpeg
  participant E as Engine (fw/whisper.cpp)
  participant L as Session Log (.md)

  MIDI->>UI: NoteOn (bank/pad mapped action)
  UI->>UI: start recording (MediaRecorder)
  MIDI->>UI: NoteOn (stop/transcribe)
  UI->>UI: stop recording -> audio blob (webm/opus)
  UI->>S: POST /v1/transcribe (blob + settings + session_id)
  S->>F: normalize audio format
  F->>E: feed normalized audio
  E-->>S: transcript + segments + metadata
  S->>L: append transcript entry to session.md
  S-->>UI: transcript + note_id + log path
  UI->>UI: edit box + quick actions
  UI->>UI: clipboard write (auto if permitted; else Copy button)
```

Clipboard automation is intentionally blocked inside Crostini, so the PWA must handle clipboard writes. citeturn5view0turn10search3  
MIDI must be handled in Chrome due to unreliable Crostini USB MIDI passthrough in practice. citeturn8search3turn8search2

## Transcription pipeline, engines, and resource trade-offs

### Audio preprocessing must be deterministic

Whisper’s paper describes the input pipeline: audio is resampled to **16,000 Hz** and converted to an **80-channel log-Mel spectrogram** computed on 25 ms windows with 10 ms stride. citeturn11search15  
ffmpeg is a “universal media converter” that can read many inputs, filter, and transcode—making it a pragmatic normalizer for whatever the browser records. citeturn6search1

This suggests a backend invariant:

- Accept browser blobs (often WebM/Opus)
- Normalize via ffmpeg to 16 kHz mono PCM/WAV for engine input
- Transcribe via engine adapter
- Return text + optional segments
- Append to session Markdown log

### Engine comparison table (speed, accuracy positioning, resource usage)

The following table focuses on **faster-whisper**, **whisper.cpp**, and the **OpenAI Speech-to-Text API** as requested. Where a metric is inherently network-dependent (cloud API latency), the table emphasizes operational characteristics and sourcing.

| Engine | Local-first | Speed evidence | Accuracy positioning | Resource usage evidence | Operational implications on ChromeOS |
|---|---|---|---|---|---|
| faster-whisper (CTranslate2) | Yes | Claims “up to 4× faster than openai/whisper for the same accuracy” and provides benchmark tables. citeturn7search9turn1search14 | Same-accuracy claim explicitly stated (with efficiency improved via quantization). citeturn7search9 | Benchmark table reports time + RAM; e.g., “Small model on CPU” includes faster-whisper int8 (time + RAM). citeturn1search14 | Strong default for CPU-constrained devices; adapter-friendly; pairs well with VAD options already present in the project. citeturn7search9turn7search20 |
| whisper.cpp (ggml/gguf) | Yes | Included in comparative benchmarks referenced by faster-whisper table; also supports multiple acceleration backends depending on platform. citeturn1search14turn1search3 | Uses Whisper-family weights; accuracy depends on model size and decoding settings (beam/search). Whisper input pipeline defined in paper. citeturn11search15turn1search3 | Provides explicit memory usage by model size (tiny→large). citeturn1search3 | Single-binary style and predictable memory sizing can be useful for Chromebooks; works well as a CLI/subprocess backend with ffmpeg normalization. citeturn1search3turn6search1 |
| OpenAI Speech-to-Text API | No (cloud) | Latency depends on network and model; offers transcription endpoints and supports higher quality model snapshots; also supports realtime approaches via related APIs. citeturn11search1turn11search17 | Historically backed by open-source Whisper (`whisper-1`), with additional model options for higher quality and diarization. citeturn11search1 | No local RAM/model storage; operational cost moves to network, API quotas, and privacy boundary. citeturn11search1 | Useful as an optional “cloud mode” plugin for specific scenarios, but not aligned with strict local-first privacy. citeturn11search1 |

Benchmark values for faster-whisper and whisper.cpp (time and RAM usage on CPU) are published in the faster-whisper benchmarking table (also mirrored on the project’s PyPI page). citeturn1search14turn7search9  
whisper.cpp’s memory usage table by model size is published in its repository. citeturn1search3

### Model sizing and Chromebook realities

whisper.cpp publishes approximate memory usage per model tier, which is directly relevant for Chromebooks with limited RAM: tiny (~273 MB), base (~388 MB), small (~852 MB), medium (~2.1 GB), large (~3.9 GB). citeturn1search3  
faster-whisper emphasizes that efficiency can be improved via 8-bit quantization across CPU/GPU. citeturn7search9

A practical ChromeOS default is: **small.en or base.en** as baseline, with a “model ladder” preference that can be changed per bank/pad mapping as your device allows.

### Licensing implications of ffmpeg integration

FFmpeg is licensed under LGPL v2.1+ by default, but optional components can make the combined build GPL; the FFmpeg project explicitly warns that if GPL parts are used, the GPL applies to all of FFmpeg. citeturn6search0  
This matters primarily if the project distributes bundled ffmpeg binaries. If the repo simply calls a user-installed ffmpeg executable, your code license can remain permissive, while distribution documentation must be clear about ffmpeg licensing. citeturn6search0turn6search4

## Monorepo structure, shared contracts, and reusable OSS patterns

### Reusable patterns from existing open-source projects

Several established projects provide strong precedents for your repo’s modular boundaries and future roadmap:

- **Buzz** demonstrates how a mature offline transcription app organizes multi-backend support (and optional advanced processing like separation/identification) without collapsing everything into one engine-specific code path. citeturn6search2turn6search15  
- **Whispering** embodies the “shortcut → speak → get text” ethos and is oriented toward local-first workflows; it’s useful as a UX reference even if ChromeOS constraints change implementation. citeturn7search0  
- **Handy** explicitly describes a local pipeline where silence is filtered with VAD (Silero) and transcription uses selectable models—useful as a pattern for pipeline stages and configuration surfaces. citeturn6search3turn6search12  
- **OpenWhispr** positions itself as a dictation app with both local and cloud processing options—a direct reference model for your future plugin/adapter strategy. citeturn7search1turn7search8  
- **WhisperTux** is a clear example of Linux text injection into the focused app using a ydotool daemon after whisper.cpp transcription—valuable as a future “optional injection” module. citeturn8search1  
- **WhisperNow** demonstrates a lightweight “record → faster-whisper → text” workflow in Linux; useful as a reference for minimal pipeline implementations and glue code. citeturn7search2turn7search6  

### Monorepo layout optimized for modular development

A ChromeOS-ready monorepo should separate concerns by runtime environment and keep *contract definitions* as a first-class, centrally-owned artifact:

```text
midi-dictation-chromeos/
  docs/
    architecture.md
    chromeos-constraints.md
    midi-mapping.md
    security.md
    adr/
  contracts/
    openapi/
      v1.yaml
    schemas/
      transcript.schema.json
      session.schema.json
      midi.schema.json
  apps/
    pwa/
      src/
      public/
      package.json
  services/
    stt-backend/
      app/
      tests/
      pyproject.toml
  tools/
    model-manager/
  scripts/
  .github/
    workflows/
    CODEOWNERS
```

### Why OpenAPI + JSON Schema are the right contract strategy

OpenAPI 3.1.0 defines that an OpenAPI document must contain at least one of `paths`, `components`, or `webhooks`. citeturn10search4  
JSON Schema Draft 2020-12 is the current stable dialect referenced as the current version by the JSON Schema site. citeturn10search9  
The OpenAPI Initiative notes that OpenAPI 3.1.0 supports compatibility with JSON Schema 2020-12. citeturn10search16

**Practical recommendation:** define request/response bodies as JSON Schema (Draft 2020-12), and embed them in OpenAPI 3.1.0 for tooling and documentation. This minimizes ambiguity when multiple agents implement clients/servers simultaneously.

### Minimal but extensible API endpoints

The v1 API should remain intentionally small, but structured so pipeline stages can expand without breaking clients:

- `GET /v1/health`
- `POST /v1/sessions/start`
- `GET /v1/sessions/{session_id}`
- `POST /v1/transcribe` (multipart: audio + JSON settings)
- `POST /v1/sessions/{session_id}/append`
- `GET /v1/models`
- `POST /v1/models/pull` (optional; can be “best effort” early)

This is consistent with the ChromeOS-friendly approach of “PWA owns capture and clipboard; backend owns inference, normalization, and durable logs,” enforced by ChromeOS clipboard restrictions and localhost tunneling support. citeturn5view0turn0search0

### PWA fundamentals relevant to this repo

A web application manifest is a JSON file providing app metadata to support installation of a PWA (name, icons, behavior). citeturn10search2  
This matters because an installed PWA provides a stable “dictation cockpit” in ChromeOS without relying on extension global shortcuts or native hosts, which are weaker fits for this environment. citeturn1search1turn10search2

## Governance, multi-agent collaboration, and CI enforcement

Multi-agent collaboration succeeds when interface drift is technically impossible and risky changes require explicit review by owners.

### Code ownership and review enforcement

GitHub’s CODEOWNERS feature automatically requests review from code owners when a PR modifies owned paths. citeturn9search0  
Protected branches can require status checks to pass and can enforce PR-based workflows (approving reviews, passing checks). citeturn9search1turn9search5

**Governance recommendation:** make `/contracts/**` and key architecture docs owned by “architecture maintainers,” and require CODEOWNER reviews for those paths (ensuring contracts don’t drift under parallel agent work). citeturn9search0turn9search5

### CI pipelines as interface policing

GitHub Actions workflows are defined as YAML files and can enforce checks on PRs. citeturn9search2turn9search9  
Status checks can be required before merge on protected branches. citeturn9search12turn9search1

A minimal CI set for this repo:
- Frontend: typecheck + lint + test + build
- Backend: lint/format + unit tests
- Contracts: OpenAPI validation + schema validation + “golden response” tests

### Contribution guidelines and onboarding

GitHub documents standardized ways to provide contributor guidelines (e.g., `CONTRIBUTING.md`) so contributors see expectations when opening PRs. citeturn9search3turn9search18

Given multiple agents, the “rules” should reduce merge conflict surface:
- contract-first development
- small PRs
- explicit ADRs for behavior changes
- no model artifacts committed to git (download scripts only)

## Roadmap for future improvements and optional capabilities

This roadmap focuses on upgrades that match the architecture: composable pipeline stages and optional adapters, rather than rewriting foundational loops.

### Voice activity detection and silence trimming

faster-whisper supports VAD filtering options and exposes VAD configuration pass-through (discussed in issues/usage contexts). citeturn7search20turn7search9  
Handy’s README describes silence filtered using VAD (Silero) as part of the dictation pipeline. citeturn6search3  
Silero VAD’s repository emphasizes speed and lightweight model size, aligning with Chromebook constraints. citeturn6search9

**Architecture fit:** introduce an optional `vad` stage between normalization and transcription, controlled by `settings.vad.enabled`.

### Plugin-based post-transcription transformations

OpenWhispr explicitly supports both local and cloud processing options, which maps naturally to a transformation plugin concept (local transforms; optional cloud transforms via user-owned API keys). citeturn7search1turn7search8  
OpenAI’s speech-to-text guide documents available transcription models and endpoints, which can be used as optional adapters where “local-first” is intentionally relaxed for specific tasks. citeturn11search1

**Architecture fit:** add `/v1/actions/run` and an internal `actions/` plugin interface that consumes `{text, metadata}` and emits artifacts (`refined_prompt`, `summary`, `title`, etc.) without entangling the transcription core.

### Optional text injection into focused apps

WhisperTux shows a Linux-friendly approach: after whisper.cpp transcription, it sends text to a ydotool daemon to write text into the focused application. citeturn8search1  
On ChromeOS, however, the Linux container is explicitly treated as untrusted relative to the host OS, and system-level automation often runs into boundary constraints; therefore, injection should remain an optional module for traditional Linux, not a required ChromeOS path. citeturn12view0turn5view0

**Architecture fit:** implement “injection” as a backend plugin available only when running on non-ChromeOS Linux (or inside Linux apps), while ChromeOS remains clipboard-first.

## Repository foundational files

Below are the three requested foundational files, written for direct drop-in use.

```markdown
# README.md

# MIDI Dictation for ChromeOS (Local-First)

A local-first dictation tool designed specifically for ChromeOS constraints:
- MIDI drum pad (16 pads × 3 banks) triggers voice notes
- Chrome-side PWA handles MIDI input, microphone capture, minimal editing UI, and clipboard copying
- Crostini-side backend handles ffmpeg audio normalization and local transcription (faster-whisper or whisper.cpp)
- Per-session Markdown log aggregates all dictations

This project is optimized for **single-user, low-latency personal dictation**, not meetings, not multi-speaker diarization, not cloud SaaS.

## Why this architecture (ChromeOS realities)

ChromeOS imposes design constraints that strongly shape the implementation:

- **No programmatic clipboard read/write from inside Crostini (VM)**  
  ChromeOS Linux FAQ: clipboard automation from inside the VM is currently not allowed for security reasons (manual paste is fine).  
  https://chromeos.dev/en/linux/linux-on-chromeos-faq

- **Native messaging is not a dependable bridge on ChromeOS**  
  Native messaging depends on host resources that aren’t reachable across the VM boundary in typical ChromeOS setups.  
  https://groups.google.com/a/chromium.org/g/chromium-extensions/c/a-gkGnb_bYc

- **USB MIDI passthrough to Crostini is unreliable**  
  Many MIDI devices are visible to Chrome but not available to share with Linux (Crostini).  
  https://groups.google.com/a/chromium.org/g/chromium-os-discuss/c/slXmgxr635E

- **Localhost tunneling into Crostini is supported**  
  ChromeOS forwards localhost ports into Crostini, enabling a browser UI to access a container service.  
  https://www.chromium.org/chromium-os/developer-library/reference/security/port-forwarding/

Therefore: **PWA (Chrome) owns MIDI + clipboard; backend (Crostini) owns models + ffmpeg + files.**

## Project goals

- Fast: “pad hit → speak → transcript ready to paste” with minimal friction
- Local-first: transcription runs locally by default
- Simple UI: record, edit, copy; no heavy “meeting app” features
- Durable logs: per-session Markdown log auto-appends every note
- Extensible: clean seams for VAD, transformations, optional cloud adapters

## High-level architecture

- `apps/pwa/` (Chrome-side)
  - Web MIDI input (bank/pad mapping)
  - Mic capture (MediaRecorder)
  - Editable transcript panel
  - Clipboard write (auto if allowed, always with a Copy fallback)
  - Session UI (start session, list notes, open log)

- `services/stt-backend/` (Crostini-side)
  - HTTP API on localhost port (tunneled to Chrome)
  - ffmpeg normalization to 16kHz mono format
  - Transcription engine adapter: faster-whisper or whisper.cpp
  - Session Markdown logs stored in Linux Files

- `contracts/`
  - OpenAPI v3.1 spec and JSON Schemas used by both sides

## Repo layout (monorepo)

- `apps/pwa/` — Chrome-side web app / PWA (TypeScript)
- `services/stt-backend/` — Crostini backend service (Python)
- `contracts/` — OpenAPI + JSON Schema (single source of truth)
- `tools/model-manager/` — scripts to download and verify models (no models committed)
- `scripts/` — dev scripts to run both processes on ChromeOS
- `.github/` — CI workflows, CODEOWNERS, templates

## Setup (ChromeOS + Crostini)

### Prereqs

- ChromeOS with Linux enabled (Crostini)
- A USB MIDI drum pad (16 pads × 3 banks)
- In Crostini:
  - `ffmpeg`
  - Python 3.10+ (recommended: `uv` or `venv`)
- In Chrome:
  - Web MIDI permission will be requested (Chrome 124+ adds a permission prompt)

### Install backend dependencies (Crostini)

From repo root:

```bash
cd services/stt-backend
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

Install ffmpeg (Debian container):

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### Download models (Crostini)

We do NOT commit model weights to git. Use the model manager:

```bash
python tools/model-manager/download_faster_whisper.py --model small.en --dest services/stt-backend/models
```

(whisper.cpp model flow is documented in `tools/model-manager/README.md`.)

### Run dev mode (ChromeOS)

From repo root:

```bash
./scripts/dev_chromeos.sh
```

This should:
- start the backend on a localhost-tunneled port
- serve the PWA from the backend (same origin)
- print the local URL to open in Chrome

Open the PWA URL in Chrome and install it (optional).

## Usage

1. Open the PWA.
2. Grant Web MIDI permission when prompted.
3. Select your MIDI device and load or learn a mapping.
4. Start a session (creates a `session.md` file).
5. Tap a pad to start recording; tap another pad to stop/transcribe.
6. Review transcript, quick-edit if needed.
7. Copy to clipboard (auto-copy if permitted; Copy button always available).
8. Session Markdown log is appended automatically in Linux Files.

## Multi-agent collaboration practices (important)

This repo is designed to support multiple parallel coding agents.

Rules that keep the repo sane:
- **Contracts are authoritative**: update `contracts/` first; backend + PWA must conform.
- **Small PRs**: keep changes scoped and reviewable.
- **No model artifacts in git**: models belong in ignored folders; use download scripts.
- **Architecture changes require ADR**: add a short decision record in `docs/adr/`.

`CODEOWNERS` is used to require review for key areas (contracts, backend, frontend).

## CI overview

GitHub Actions runs:
- Frontend: install → lint → typecheck → test → build
- Backend: lint/format → unit tests
- Contracts: OpenAPI/schema validation + contract tests

Branch protection should require:
- passing CI checks
- CODEOWNER review for `contracts/` and critical modules

## License

This project’s code is MIT-licensed (see `LICENSE`).

Note: FFmpeg is LGPL/GPL depending on build configuration. This repo calls a user-installed ffmpeg binary by default. If you distribute packaged builds that bundle FFmpeg, you must comply with FFmpeg’s license conditions.
https://www.ffmpeg.org/legal.html

## References and inspiration

- Buzz (multi-backend offline transcription app): https://github.com/chidiwilliams/buzz
- Whispering (local-first dictation UX patterns): https://github.com/braden-w/whispering
- Handy (forkable dictation + VAD pipeline patterns): https://github.com/cjpais/Handy
- OpenWhispr (local + cloud provider patterns): https://github.com/HeroTools/open-whispr
- WhisperTux (Linux text injection pattern): https://github.com/cjams/whispertux
- WhisperNow (lightweight faster-whisper dictation): https://github.com/shinglyu/WhisperNow
```

```text
# LICENSE (MIT License)

MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

```gitignore
# .gitignore

# OS / editors
.DS_Store
Thumbs.db
*.swp
*.swo
.vscode/
.idea/
*.iml

# Logs
*.log
logs/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Node / frontend
node_modules/
dist/
build/
.cache/
.parcel-cache/
.next/
out/
coverage/
eslint-report.json

# Env files (keep samples only)
.env
.env.*
!.env.example

# Python / backend
__pycache__/
*.py[cod]
*.pyo
*.pyd
.mypy_cache/
.pytest_cache/
.ruff_cache/
.coverage
coverage.xml
htmlcov/
.venv/
venv/
ENV/
*.egg-info/
pip-wheel-metadata/
*.whl

# Jupyter
.ipynb_checkpoints/

# Backend runtime artifacts
services/stt-backend/tmp/
services/stt-backend/.local/
services/stt-backend/.cache/

# Model artifacts (do not commit)
models/
model_cache/
**/models/
**/*.bin
**/*.gguf
**/*.ggml
**/*.ct2
**/*.onnx
**/*.pt
**/*.safetensors

# Audio artifacts (optional local debugging)
recordings/
audio/
**/*.wav
**/*.mp3
**/*.m4a
**/*.webm
**/*.opus
**/*.flac

# Archives
*.zip
*.tar
*.tar.gz
*.7z

# Local databases
*.sqlite
*.sqlite3

# Secrets / keys
*.pem
*.key
*.p12
*.pfx

# Runtime PID files
*.pid
```
