import logging
from datetime import datetime

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.logging import TextualHandler
from textual.widgets import Footer, Header, Input, RichLog

from backend.event_bus import EventBus

logger = logging.getLogger(__name__)

class VoxPadApp(App):
    """A Textual app for The Dictator."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 1 3;
        grid-rows: auto 1fr auto;
    }

    #log-container {
        height: 100%;
        border: solid green;
    }

    RichLog {
        height: 100%;
    }

    #input {
        dock: bottom;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("c", "clear_logs", "Clear Logs"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="log-container"):
            yield RichLog(highlight=True, markup=True, id="logs")
        yield Input(placeholder="Type commands here... (e.g. 'help')", id="input")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "The Dictator"
        self.sub_title = "Local-first Voice Dictation"

        # Configure logging to write to Textual's RichLog
        # We need to add the handler to the root logger
        handler = TextualHandler()
        logging.getLogger().addHandler(handler)
        # Ensure level is low enough to capture info
        logging.getLogger().setLevel(logging.INFO)

        self.query_one("#logs", RichLog).write("GUI initialized.")

        # Subscribe to events
        EventBus.subscribe("log", self.on_log_event)
        EventBus.subscribe("transcription_complete", self.on_transcription_complete)

    def on_log_event(self, data):
        # Schedule the update on the main thread
        self.call_from_thread(self._write_log, f"[dim]{datetime.now().strftime('%H:%M:%S')}[/dim] {data}")

    def on_transcription_complete(self, data):
        self.call_from_thread(self._write_log, f"[bold green]Transcription Complete:[/bold green] {data}")

    def _write_log(self, message: str):
        try:
            log_widget = self.query_one("#logs", RichLog)
            log_widget.write(message)
        except Exception:
            pass

    @on(Input.Submitted)
    def handle_input(self, event: Input.Submitted) -> None:
        command = event.value.strip()
        event.input.value = ""

        self.query_one("#logs", RichLog).write(f"[bold blue]Command:[/bold blue] {command}")

        if command == "quit":
            self.exit()
        elif command == "help":
            self.query_one("#logs", RichLog).write("Available commands: quit, help, clear")
        elif command == "clear":
            self.query_one("#logs", RichLog).clear()
        else:
            # Publish command to EventBus for other components to pick up
            EventBus.publish("command", command)
            self.query_one("#logs", RichLog).write(f"Command '{command}' published.")

    def action_clear_logs(self) -> None:
        self.query_one("#logs", RichLog).clear()

    def shutdown(self) -> None:
        """Clean up resources."""
        logger.info("GUI shut down")
        # Ensure we clean up any resources if needed

    def on_unmount(self) -> None:
        self.shutdown()

if __name__ == "__main__":
    app = VoxPadApp()
    app.run()
