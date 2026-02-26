class AudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.mimeType = "";
    }

    async start() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mimeType = this.#pickMimeType();
        const options = this.mimeType ? { mimeType: this.mimeType } : undefined;
        this.mediaRecorder = new MediaRecorder(stream, options);
        this.audioChunks = [];

        this.mediaRecorder.ondataavailable = (event) => {
            this.audioChunks.push(event.data);
        };

        this.mediaRecorder.start();
    }

    stop() {
        return new Promise((resolve) => {
            if (!this.mediaRecorder || this.mediaRecorder.state === "inactive") {
                resolve(null);
                return;
            }

            this.mediaRecorder.onstop = () => {
                const audioBlob = new Blob(this.audioChunks, { type: this.mimeType || undefined });
                resolve(audioBlob);

                // Stop all tracks to release microphone
                this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
            };
            this.mediaRecorder.stop();
        });
    }

    #pickMimeType() {
        if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) {
            return "";
        }

        const candidates = [
            "audio/webm;codecs=opus",
            "audio/webm",
            "audio/ogg;codecs=opus",
            "audio/ogg"
        ];

        return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || "";
    }
}
