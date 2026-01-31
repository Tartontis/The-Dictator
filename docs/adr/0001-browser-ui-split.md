# ADR 0001: Browser UI Split Architecture

## Status

Accepted

## Context

The-Dictator is a voice dictation tool designed to run on ChromeOS (Crostini Linux container) with MIDI controller support. During development, we encountered two significant platform constraints:

1. **USB MIDI devices are not reliably passed through to the Crostini Linux container.** ChromeOS captures USB MIDI for its own use (Android apps, Web MIDI in Chrome), but the Linux container cannot access these devices. This is a known limitation tracked in ChromeOS issue trackers with no clear timeline for resolution.

2. **Cross-application keystroke injection is blocked on ChromeOS.** Tools like `xdotool` cannot inject keystrokes into Chrome browser windows from the Linux container due to the Wayland/Sommelier security boundary. This is actually a reasonable security measure.

The original architecture assumed a pure Python desktop application (PySide6) running in Crostini. This would have required:
- Workarounds for MIDI (network MIDI, OSC protocol, Arduino bridge)
- Copy-to-clipboard only (no auto-typing into Chrome windows)

## Decision

We will split the application into two components:

1. **Frontend (Browser):** A web application running in Chrome that handles:
   - MIDI input via Web MIDI API (works natively in Chrome)
   - Audio recording via MediaRecorder API
   - Clipboard operations via Clipboard API
   - UI display and interaction

2. **Backend (Crostini):** A Python FastAPI server running in the Linux container that handles:
   - Audio preprocessing (ffmpeg normalization)
   - Speech-to-text transcription (faster-whisper)
   - Session log file management
   - LLM API relay (optional)
   - HiveCluster communication (optional)

Communication between frontend and backend uses:
- HTTP REST for request/response operations (transcription, refinement)
- WebSocket for future real-time streaming transcription

The backend listens only on localhost (127.0.0.1), accessible from Chrome on the same machine.

## Consequences

### Positive

- **MIDI works.** Web MIDI API in Chrome has full access to USB MIDI devices without any workarounds.

- **Simpler audio capture.** MediaRecorder API is well-documented and handles codec negotiation automatically.

- **Better clipboard UX.** The Clipboard API in browsers is more reliable than Linux clipboard tools when interacting with Chrome tabs.

- **No GUI framework dependency.** We avoid PySide6/PyQt complexity and licensing considerations.

- **Easier to iterate on UI.** HTML/CSS/JS has faster feedback loops than desktop GUI frameworks.

- **Works with any browser.** Could potentially work on other platforms with minimal changes.

### Negative

- **Two codebases to maintain.** Frontend (JS) and backend (Python) are separate.

- **More moving parts.** User must start the backend server before using the frontend.

- **Latency overhead.** HTTP round-trip adds some latency vs. in-process calls (but transcription time dominates anyway).

- **CORS configuration.** Backend must be configured to accept requests from the frontend origin.

### Neutral

- **Vanilla JS vs. framework.** For MVP, we use vanilla JS to avoid build steps. May revisit for Phase 2+ if complexity warrants it.

- **localhost networking.** Crostini's localhost networking between Chrome and the Linux container is well-supported and reliable.

## Alternatives Considered

### 1. Pure Python desktop app with network MIDI

Use rtpmidi or similar to receive MIDI over the network from another device.

Rejected because: Requires additional hardware or software setup. Adds complexity for users who just want to use their USB MIDI controller.

### 2. Electron app

Package frontend and backend together in an Electron wrapper.

Rejected because: Heavy dependency (ships Chromium), complex packaging, no clear benefit over browser + Python server for this use case.

### 3. Pure browser app (no Python backend)

Use WebAssembly port of Whisper (whisper.cpp compiled to WASM).

Rejected because: WASM Whisper is slower and has limited model support. We want the full faster-whisper performance. Also limits future HiveCluster integration.

### 4. Chrome Extension

Build as a Chrome extension with native messaging to Python backend.

Considered for future: Could enable "paste into active tab" functionality. Deferred because it adds complexity and the clipboard workflow is sufficient for MVP.

## References

- [ChromeOS MIDI in Crostini issue](https://issuetracker.google.com/issues/260275869)
- [Web MIDI API specification](https://www.w3.org/TR/webmidi/)
- [Crostini architecture overview](https://chromium.googlesource.com/chromiumos/docs/+/master/containers_and_vms.md)
- [McLaren Labs: Chromebook, Crostini Linux and MIDI](https://mclarenlabs.com/blog/2023/10/08/chromebook-crostini-linux-and-midi/)
