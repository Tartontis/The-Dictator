class HotkeyHandler {
    constructor(actionCallback) {
        this.actionCallback = actionCallback;
        this.mappings = {};
    }

    setMappings(mappings) {
        // mappings is object like { "ctrl+shift+r": "toggle_recording", ... }
        this.mappings = mappings || {};
        console.log("Hotkey mappings loaded:", this.mappings);
    }

    init() {
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
    }

    handleKeydown(e) {
        // Build the key string
        const parts = [];
        if (e.ctrlKey) parts.push("ctrl");
        if (e.altKey) parts.push("alt");
        if (e.shiftKey) parts.push("shift");
        if (e.metaKey) parts.push("meta");

        // Normalize key
        let key = e.key.toLowerCase();

        // Handle F-keys and standard keys
        // Avoid adding 'control', 'shift', etc. as the key itself if it's just a modifier press
        if (['control', 'alt', 'shift', 'meta'].includes(key)) return;

        parts.push(key);

        const combo = parts.join("+");

        // Check exact match
        if (this.mappings[combo]) {
            e.preventDefault(); // Prevent default browser action (e.g. print, save)
            this.actionCallback(this.mappings[combo]);
        }
    }
}
