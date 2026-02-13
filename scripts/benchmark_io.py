import io
import os
import shutil
import tempfile
import time
from pathlib import Path


# Simulating a file upload
class MockUploadFile:
    def __init__(self, content):
        self.file = io.BytesIO(content)
        self.filename = "test_audio.wav"

def benchmark_disk_io(file_content):
    file = MockUploadFile(file_content)
    start_time = time.perf_counter()

    # Logic from backend/api/routes.py before optimization
    suffix = Path(file.filename).suffix
    if not suffix:
        suffix = ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    # Simulate transcriber reading the file from disk
    # faster-whisper opens the file path internally
    with open(tmp_path, "rb") as f:
        _ = f.read()

    # Cleanup
    if tmp_path.exists():
        tmp_path.unlink()

    end_time = time.perf_counter()
    return end_time - start_time

def benchmark_memory_io(file_content):
    file = MockUploadFile(file_content)
    start_time = time.perf_counter()

    # Logic after optimization: pass file-like object directly
    # faster-whisper reads from the file-like object
    _ = file.file.read()

    end_time = time.perf_counter()
    return end_time - start_time

if __name__ == "__main__":
    # Generate 10MB of dummy data
    file_size_mb = 10
    file_content = os.urandom(file_size_mb * 1024 * 1024)

    print(f"Benchmarking with {file_size_mb}MB file...")

    # Warmup
    benchmark_disk_io(file_content)
    benchmark_memory_io(file_content)

    iterations = 5
    disk_times = []
    memory_times = []

    for _ in range(iterations):
        disk_times.append(benchmark_disk_io(file_content))
        memory_times.append(benchmark_memory_io(file_content))

    avg_disk = sum(disk_times) / iterations
    avg_memory = sum(memory_times) / iterations

    print(f"Average Disk I/O approach time: {avg_disk:.4f}s")
    print(f"Average Memory I/O approach time: {avg_memory:.4f}s")

    if avg_memory > 0:
        speedup = avg_disk / avg_memory
        print(f"Speedup: {speedup:.2f}x")
    else:
        print("Memory approach took 0s (too fast to measure or error)")
