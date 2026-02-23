class MIDIHandler {
    constructor(actionCallback) {
        this.actionCallback = actionCallback;
        this.access = null;
        this.mappings = {};
    }

    setMappings(mappings) {
        // mappings is object like { "36": "toggle_recording", ... }
        // Convert keys to integers if they are strings
        this.mappings = {};
        for (const [key, value] of Object.entries(mappings || {})) {
            this.mappings[parseInt(key)] = value;
        }
        console.log("MIDI mappings loaded:", this.mappings);
    }

    async init() {
        if (!navigator.requestMIDIAccess) {
             console.warn("Web MIDI API not supported in this browser.");
             return false;
        }

        try {
            this.access = await navigator.requestMIDIAccess();
            this.access.onstatechange = (e) => this.handleStateChange(e);

            for (let input of this.access.inputs.values()) {
                input.onmidimessage = (e) => this.handleMessage(e);
            }
            return true;
        } catch (err) {
            console.warn("MIDI Access failed:", err);
            return false;
        }
    }

    handleStateChange(e) {
        console.log(`MIDI port ${e.port.name} ${e.port.state}`);
        if (e.port.type === "input" && e.port.state === "connected") {
             e.port.onmidimessage = (msg) => this.handleMessage(msg);
        }
    }

    handleMessage(message) {
        const [command, note, velocity] = message.data;
        // Note On is typically 144 (0x90) for channel 1
        if ((command & 0xF0) === 0x90 && velocity > 0) {
            const action = this.mappings[note];
            if (action) {
                this.actionCallback(action);
            } else {
                console.log(`Unmapped MIDI Note: ${note}`);
            }
        }
    }
}
