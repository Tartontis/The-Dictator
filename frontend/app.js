const API_URL = "http://localhost:8765/api";

const state = {
    isRecording: false,
    transcript: ""
};

const recorder = new AudioRecorder();
const ui = {
    btnRecord: document.getElementById('btn-record'),
    btnStop: document.getElementById('btn-stop'),
    btnCopy: document.getElementById('btn-copy'),
    btnAppend: document.getElementById('btn-append'),
    btnClear: document.getElementById('btn-clear'),

    // New Refs
    selectTemplate: document.getElementById('template-select'),
    btnRefine: document.getElementById('btn-refine'),

    transcript: document.getElementById('transcript'),
    status: document.getElementById('status'),
    apiStatus: document.getElementById('api-status'),
    midiStatus: document.getElementById('midi-status')
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

// --- UI Updates ---

function updateUI() {
    if (state.isRecording) {
        ui.btnRecord.classList.add('recording');
        ui.btnRecord.textContent = "Stop Recording (Pad 1)";
        ui.btnStop.disabled = false;
        ui.status.textContent = "Recording...";
        // Disable refinement while recording
        ui.btnRefine.disabled = true;
    } else {
        ui.btnRecord.classList.remove('recording');
        ui.btnRecord.textContent = "Record (Pad 1)";
        ui.btnStop.disabled = true;
        ui.btnRefine.disabled = false;
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
            ui.apiStatus.textContent = "API: OK";
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
        case "transcribe_copy":
            if (state.isRecording) {
                stopRecording().then(() => {
                    // Wait for transcription then copy
                    // A proper event system would be better here, but polling checks:
                    const checkInterval = setInterval(() => {
                        if (ui.status.textContent === "Transcribed") {
                            copyToClipboard();
                            clearInterval(checkInterval);
                        }
                    }, 500);
                });
            } else {
                // If not recording, just copy what's there
                copyToClipboard();
            }
            break;
    }
}

// Event Listeners
ui.btnRecord.onclick = toggleRecording;
ui.btnStop.onclick = stopRecording;
ui.btnCopy.onclick = copyToClipboard;
ui.btnAppend.onclick = appendSession;
ui.btnClear.onclick = () => {
    ui.transcript.value = "";
    state.transcript = "";
    if (!state.isRecording) {
        ui.status.textContent = "Ready";
    }
};

ui.btnRefine.onclick = () => {
    const template = ui.selectTemplate.value;
    refineText(template);
};

// Start
const midiHandler = new MIDIHandler(handleAction);
midiHandler.init().then(success => {
    ui.midiStatus.textContent = success ? "MIDI: Active" : "MIDI: Not Available";
});

checkAPI();
setInterval(checkAPI, 5000);
