# Jules Code Review Prompts: The Dictator

The following is a comprehensive suite of prompts designed to guide a Jules agent (or similar AI assistant) through a systematic, multi-faceted code review of "The Dictator" project. These prompts are meant to be executed sequentially or distributed to ensure thorough coverage of functionality, UX, resource handling, airgapped usage, and security.

---

## 1. Functionality & Bug Fixes

**Prompt:**
> "Jules, please perform a deep-dive code review focusing exclusively on the core functionality and bug detection for 'The Dictator' backend and frontend.
>
> Specifically:
> 1. Review the audio transcription pipeline from the frontend `MediaRecorder` setup to the backend `/api/transcribe` endpoint. Ensure there are no edge cases (e.g., empty files, unsupported formats) that could cause unhandled exceptions.
> 2. Trace the execution of the LLM refinement endpoint `/api/refine` and ensure Jinja2 templates are properly loaded and applied without silent failures.
> 3. Check the markdown session logger for race conditions or append errors.
> 4. Analyze recent branch merges (e.g., auth fixes, duplicate transcribe method removal) for regression.
>
> Output concrete, committed recommendations for fixing any identified bugs or logical errors."

---

## 2. UX Design & Interaction Functionality

**Prompt:**
> "Jules, conduct a comprehensive UX design and interaction functionality review of the Vanilla JS frontend for 'The Dictator'.
>
> Focus on:
> 1. The Web MIDI and keyboard shortcut implementation (including the recent custom hotkey/macro pad support). Does the frontend correctly parse and bind actions from the `/api/config` or `/api/button_map` endpoints?
> 2. The manual character-by-character word counting loop for the `updateStats` function—verify its integration doesn't stutter the UI thread for long texts.
> 3. State management during asynchronous operations (e.g., transcription and LLM refinement). Does the UI provide adequate visual feedback during long-running tasks?
> 4. Error state presentation to the user when backend services (like the optional HiveCluster or local Ollama) are unavailable.
>
> Provide committed recommendations (including HTML/JS/CSS snippets) for improving the UI/UX."

---

## 3. Resource Handling & Performance

**Prompt:**
> "Jules, perform a rigorous review of resource handling and performance optimization across the entire codebase.
>
> Key areas to investigate:
> 1. **Memory Management:** Verify the usage of generator expressions over list comprehensions in string join operations within the transcriber logic (as introduced in recent performance branches) to ensure lazy evaluation without memory spikes.
> 2. **I/O Operations:** Analyze the `load_settings` cache implementation (using `lru_cache` and EAFP patterns) and the `SessionLogger.append` logic. Confirm that redundant system calls (like `exists()`) are eliminated.
> 3. **Concurrency:** Review the FastAPI/Uvicorn configuration. Ensure Uvicorn's auto-reload is properly disabled in production and that asynchronous routes aren't blocked by synchronous I/O operations.
> 4. **File Uploads:** Verify the implementation of direct streaming of the uploaded audio file to the transcriber, bypassing intermediate disk I/O, and check for proper memory cleanup.
>
> Propose actionable code modifications to maximize performance and minimize CPU/Memory footprints."

---

## 4. Offline & Airgapped Usage Resiliency

**Prompt:**
> "Jules, review the project to ensure strict adherence to its 'local-first, offline' MVP goal.
>
> Your review must verify:
> 1. That the core application (transcription via `faster-whisper`, session logging, and UI interaction) functions completely without internet access.
> 2. That no external tracking, CDN-hosted scripts, or mandatory remote telemetry exists in the frontend HTML/JS.
> 3. That the failure of external LLM services (e.g., Anthropic, OpenAI) fails gracefully without crashing the core transcription pipeline. Local alternatives (like Ollama) should have clear fallback paths.
> 4. That the API keys and configurations are read entirely locally (from environment variables or TOML files) and never call out to a centralized key server.
>
> Provide committed recommendations to guarantee 100% airgapped viability."

---

## 5. Midday Unorganized Security Assessment

**Prompt:**
> "Jules, conduct a 'Midday Unorganized Security' audit of the system.
>
> Pay special attention to the following attack vectors and configurations:
> 1. **Authentication:** Review the API key authentication implementation (via the `X-API-Key` header). Validate the use of `secrets.compare_digest` to prevent timing attacks.
> 2. **Directory Traversal:** Ensure that Jinja2's `FileSystemLoader` strictly confines template loading to the `prompts/` directory and that `SessionLogger` prevents arbitrary file writes.
> 3. **Input Validation:** Inspect the `/api/transcribe` and `/api/refine` endpoints to ensure malicious or malformed payloads cannot cause remote code execution or denial of service.
> 4. **CORS & Network:** Verify that CORS is strictly locked down to `localhost`, `127.0.0.1`, and `null` (for local `file://` execution), and that the backend does not inadvertently expose sensitive endpoints to the broader network.
>
> Deliver committed recommendations and code patches to lock down these vulnerabilities."

---

## 6. Comprehensive Synthesis & Code Readiness

**Prompt:**
> "Jules, after aggregating the findings from functionality, UX, resource handling, airgapped usage, and security reviews, synthesize a final 'Code Readiness Report'.
>
> Your task:
> 1. Cross-reference the identified issues with the 'Agent Playbook' (`docs/agent-playbook.md`) and project architecture (`docs/architecture.md`).
> 2. Ensure all proposed fixes adhere to the established module boundaries (e.g., JS handles Web MIDI, Python handles `faster-whisper`).
> 3. Create a prioritized action plan of commits required to bring the software to a robust, production-ready MVP state.
> 4. Identify any missing tests for the newly proposed fixes and provide the necessary `pytest` stubs.
>
> Output the synthesized report as markdown ready to be appended to the documentation."