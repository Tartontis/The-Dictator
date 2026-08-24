const API_URL = "http://localhost:8765/api";
const STORAGE_KEY = "dictator.offline.transcript";
const SHORTCUTS_STORAGE_KEY = "dictator.offline.shortcuts";

const DEFAULT_KEYBINDINGS = {
    toggle_recording: "Space",
    copy: "Control+Shift+C",
    append_session: "Control+Shift+A",
    refine_selected: "Control+Shift+R",
    clear: "Control+Shift+X"
};

const state = {
    isRecording: false,
    isOffline: true,
    transcript: "",
    autosaveTimer: null,
    keybindings: { ...DEFAULT_KEYBINDINGS },
    listeningForBinding: null
};

const recorder = new AudioRecorder();
const ui = {
    btnRecord: document.getElementById('btn-record'),
    btnStop: document.getElementById('btn-stop'),
    btnCopy: document.getElementById('btn-copy'),
    btnAppend: document.getElementById('btn-append'),
    btnClear: document.getElementById('btn-clear'),
    btnDownload: document.getElementById('btn-download'),

    // New Refs
    selectTemplate: document.getElementById('template-select'),
    btnRefine: document.getElementById('btn-refine'),

    transcript: document.getElementById('transcript'),
    offlineToggle: document.getElementById('offline-toggle'),
    autosaveStatus: document.getElementById('autosave-status'),
    wordCount: document.getElementById('word-count'),
    charCount: document.getElementById('char-count'),
    lastSaved: document.getElementById('last-saved'),
    status: document.getElementById('status'),
    apiStatus: document.getElementById('api-status'),
    midiStatus: document.getElementById('midi-status'),
    hotkeyStatus: document.getElementById('hotkey-status'),

    // Shortcuts Controls
    btnToggleShortcuts: document.getElementById('btn-toggle-shortcuts'),
    shortcutsConfig: document.getElementById('shortcuts-config'),
    btnResetShortcuts: document.getElementById('btn-reset-shortcuts'),
    keyInputs: document.querySelectorAll('.key-binding-input')
};

// --- Actions ---

async function toggleRecording() {
    if (state.isRecording) {
        await stopRecording();
    } else {
        await startRecording();
    }
}

async function startRecording() {
    try {
        await recorder.start();
        state.isRecording = true;
        updateUI();
    } catch (err) {
        console.error("Failed to start recording:", err);
        alert("Could not access microphone. Ensure you are using HTTPS or localhost.");
    }
}

async function stopRecording() {
    state.isRecording = false;
    updateUI();

    ui.status.textContent = "Processing...";

    try {
        const audioBlob = await recorder.stop();
        if (audioBlob) {
            await transcribe(audioBlob);
        }
    } catch (err) {
        console.error(err);
        ui.status.textContent = "Error stopping recording";
    }
}

async function transcribe(audioBlob) {
    const formData = new FormData();
    const extension = getAudioExtension(audioBlob.type);
    formData.append("file", audioBlob, `recording.${extension}`);

    try {
        ui.status.textContent = "Transcribing...";
        const res = await fetch(`${API_URL}/transcribe`, {
            method: "POST",
            body: formData
        });

        if (!res.ok) throw new Error(await res.text());

        const data = await res.json();
        state.transcript = data.text;
        ui.transcript.value = state.transcript;
        ui.status.textContent = "Transcribed";
    } catch (err) {
        console.error(err);
        ui.status.textContent = "Error during transcription";
    }
}

function getAudioExtension(mimeType) {
    if (!mimeType) return "wav";

    if (mimeType.includes("webm")) return "webm";
    if (mimeType.includes("ogg")) return "ogg";
    if (mimeType.includes("wav")) return "wav";

    return "wav";
}

async function appendSession() {
    if (state.isOffline) {
        ui.status.textContent = "Offline-only: session append disabled";
        return;
    }
    const text = ui.transcript.value;
    if (!text) return;

    try {
        const res = await fetch(`${API_URL}/session/append`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text })
        });

        if (res.ok) {
            ui.status.textContent = "Appended to session";
            setTimeout(() => {
                if (!state.isRecording) ui.status.textContent = "Connected";
            }, 2000);
        }
    } catch (err) {
        console.error(err);
        ui.status.textContent = "Error appending";
    }
}

async function refineText(templateName) {
    if (state.isOffline) {
        ui.status.textContent = "Offline-only: refinement disabled";
        return;
    }
    const text = ui.transcript.value;
    if (!text) return;

    ui.status.textContent = `Refining (${templateName})...`;

    try {
        const res = await fetch(`${API_URL}/refine`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: text,
                template: templateName
            })
        });

        if (!res.ok) throw new Error(await res.text());

        const data = await res.json();
        ui.transcript.value = data.text;
        ui.status.textContent = "Refined";
        state.transcript = data.text;
    } catch (err) {
        console.error(err);
        ui.status.textContent = "Refinement failed";
        alert("Refinement failed. Check backend logs and API keys.");
    }
}

function copyToClipboard() {
    const text = ui.transcript.value;
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
        const originalText = ui.btnCopy.textContent;
        ui.btnCopy.textContent = "Copied!";
        setTimeout(() => ui.btnCopy.textContent = originalText, 1500);
    }).catch(err => {
        console.error("Failed to copy:", err);
    });
}

function updateStats(text) {
    const trimmed = text.trim();
    const words = trimmed ? trimmed.split(/\s+/).length : 0;
    ui.wordCount.textContent = String(words);
    ui.charCount.textContent = String(text.length);
}

function setAutosaveStatus(message) {
    ui.autosaveStatus.textContent = message;
}

function saveTranscript() {
    const text = ui.transcript.value;
    localStorage.setItem(STORAGE_KEY, text);
    const timestamp = new Date();
    ui.lastSaved.textContent = timestamp.toLocaleTimeString();
    setAutosaveStatus("Saved");
}

function scheduleAutosave() {
    setAutosaveStatus("Saving...");
    if (state.autosaveTimer) {
        clearTimeout(state.autosaveTimer);
    }
    state.autosaveTimer = setTimeout(() => {
        saveTranscript();
        state.autosaveTimer = null;
    }, 500);
}

function downloadTranscript() {
    const text = ui.transcript.value.trim();
    if (!text) return;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
    link.href = url;
    link.download = `dictator-transcript-${timestamp}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function updateOfflineMode() {
    state.isOffline = ui.offlineToggle.checked;
    ui.btnAppend.disabled = state.isOffline;
    ui.selectTemplate.disabled = state.isOffline;
    if (state.isOffline) {
        ui.btnRefine.disabled = true;
    } else if (!state.isRecording) {
        ui.btnRefine.disabled = false;
    }
    ui.apiStatus.textContent = state.isOffline ? "API: Local-only" : ui.apiStatus.textContent;
}

// --- UI Updates ---

function updateUI() {
    if (state.isRecording) {
        ui.btnRecord.classList.add('recording');
        ui.btnRecord.textContent = "Stop Recording (Pad 1)";
        ui.btnStop.disabled = false;
        ui.status.textContent = "Recording...";
        ui.btnRefine.disabled = true;
    } else {
        ui.btnRecord.classList.remove('recording');
        ui.btnRecord.textContent = "Record (Pad 1)";
        ui.btnStop.disabled = true;
        ui.btnRefine.disabled = state.isOffline;
    }
}

// --- Initialization ---

async function checkAPI() {
    try {
        const res = await fetch(`${API_URL}/health`);
        if (res.ok) {
            if (ui.status.textContent === "Disconnected" || ui.status.textContent === "API Disconnected") {
                ui.status.textContent = "Connected";
            }
            ui.status.classList.remove('disconnected');
            ui.status.classList.add('connected');
            ui.apiStatus.textContent = state.isOffline ? "API: Local-only" : "API: OK";
        } else {
            throw new Error();
        }
    } catch {
        ui.status.classList.remove('connected');
        ui.status.classList.add('disconnected');
        ui.apiStatus.textContent = "API: Offline";
    }
}

// MIDI Callback
function handleAction(action) {
    console.log("MIDI Action:", action);
    ui.midiStatus.textContent = `MIDI Action: ${action}`;

    if (action.startsWith("refine:")) {
        const template = action.split(":")[1];
        refineText(template);
        return;
    }

    if (action.startsWith("open_browser:")) {
        // Just inform user, browser cannot reliably open new tabs from MIDI background event
        // without user interaction in some contexts, but let's try
        const target = action.split(":")[1];
        const urls = {
            "claude": "https://claude.ai/new",
            "chatgpt": "https://chat.openai.com"
        };
        if (urls[target]) window.open(urls[target], "_blank");
        return;
    }

    switch(action) {
        case "toggle_recording": toggleRecording(); break;
        case "copy": copyToClipboard(); break;
        case "append_session": appendSession(); break;
        case "refine_selected":
            refineText(ui.selectTemplate.value);
            break;
        case "clear":
            ui.transcript.value = "";
            state.transcript = "";
            updateStats("");
            saveTranscript();
            if (!state.isRecording) ui.status.textContent = "Ready";
            break;
        case "transcribe_copy":
            if (state.isRecording) {
                stopRecording().then(() => {
                    const checkInterval = setInterval(() => {
                        if (ui.status.textContent === "Transcribed") {
                            copyToClipboard();
                            clearInterval(checkInterval);
                        }
                    }, 500);
                });
            } else {
                copyToClipboard();
            }
            break;
    }
}

// --- Hotkey / Macro Pad Handler ---

function getKeyCombinationString(e) {
    const parts = [];
    if (e.ctrlKey) parts.push("Control");
    if (e.altKey) parts.push("Alt");
    if (e.shiftKey) parts.push("Shift");
    if (e.metaKey) parts.push("Meta");

    const key = e.code === "Space" ? "Space" : e.key;
    if (!["Control", "Alt", "Shift", "Meta"].includes(e.key)) {
        parts.push(key.length === 1 ? key.toUpperCase() : key);
    }
    return parts.join("+");
}

function loadShortcuts() {
    try {
        const saved = localStorage.getItem(SHORTCUTS_STORAGE_KEY);
        if (saved) {
            state.keybindings = { ...DEFAULT_KEYBINDINGS, ...JSON.parse(saved) };
        }
    } catch {
        state.keybindings = { ...DEFAULT_KEYBINDINGS };
    }
    syncKeyInputs();
}

function saveShortcuts() {
    localStorage.setItem(SHORTCUTS_STORAGE_KEY, JSON.stringify(state.keybindings));
}

function syncKeyInputs() {
    ui.keyInputs.forEach(input => {
        const action = input.getAttribute("data-action");
        if (state.keybindings[action]) {
            input.value = state.keybindings[action];
        }
    });
}

function handleGlobalKeydown(e) {
    // If recording a new shortcut binding
    if (state.listeningForBinding) {
        e.preventDefault();
        e.stopPropagation();

        const combo = getKeyCombinationString(e);
        const action = state.listeningForBinding.getAttribute("data-action");

        state.keybindings[action] = combo;
        saveShortcuts();
        syncKeyInputs();

        state.listeningForBinding.classList.remove("recording");
        state.listeningForBinding = null;
        return;
    }

    // Ignore shortcut execution if user is actively typing inside text area
    if (document.activeElement === ui.transcript && !e.ctrlKey && !e.altKey && e.code !== "Escape") {
        return;
    }

    const currentCombo = getKeyCombinationString(e);

    for (const [action, combo] of Object.entries(state.keybindings)) {
        if (combo === currentCombo) {
            e.preventDefault();
            handleAction(action);
            break;
        }
    }
}

// Event Listeners
ui.btnRecord.onclick = toggleRecording;
ui.btnStop.onclick = stopRecording;
ui.btnCopy.onclick = copyToClipboard;
ui.btnAppend.onclick = appendSession;
ui.btnDownload.onclick = downloadTranscript;
ui.btnClear.onclick = () => {
    ui.transcript.value = "";
    state.transcript = "";
    updateStats("");
    saveTranscript();
    if (!state.isRecording) {
        ui.status.textContent = "Ready";
    }
};
ui.offlineToggle.onchange = updateOfflineMode;
ui.transcript.addEventListener("input", () => {
    const text = ui.transcript.value;
    state.transcript = text;
    updateStats(text);
    scheduleAutosave();
});

ui.btnRefine.onclick = () => {
    const template = ui.selectTemplate.value;
    refineText(template);
};

ui.btnToggleShortcuts.onclick = () => {
    ui.shortcutsConfig.classList.toggle("hidden");
    const isHidden = ui.shortcutsConfig.classList.contains("hidden");
    ui.btnToggleShortcuts.textContent = isHidden ? "Configure Shortcuts" : "Close Config";
};

ui.btnResetShortcuts.onclick = () => {
    state.keybindings = { ...DEFAULT_KEYBINDINGS };
    saveShortcuts();
    syncKeyInputs();
};

ui.keyInputs.forEach(input => {
    input.onclick = () => {
        if (state.listeningForBinding) {
            state.listeningForBinding.classList.remove("recording");
        }
        state.listeningForBinding = input;
        input.classList.add("recording");
        input.value = "Press key...";
    };
});

window.addEventListener("keydown", handleGlobalKeydown);

// Start
const midiHandler = new MIDIHandler(handleAction);
midiHandler.init().then(success => {
    ui.midiStatus.textContent = success ? "MIDI: Active" : "MIDI: Not Available";
});

loadShortcuts();

const savedTranscript = localStorage.getItem(STORAGE_KEY);
if (savedTranscript) {
    ui.transcript.value = savedTranscript;
    state.transcript = savedTranscript;
    updateStats(savedTranscript);
    ui.status.textContent = "Session restored";
} else {
    updateStats("");
}
setAutosaveStatus("Idle");
updateOfflineMode();
checkAPI();
setInterval(checkAPI, 5000);
