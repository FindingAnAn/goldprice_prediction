"""Lightweight process resource monitoring for model runs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import threading
import time

import psutil


@dataclass(frozen=True)
class ResourceSummary:
    peak_rss_mb: float
    average_rss_mb: float
    average_cpu_percent: float
    max_cpu_percent: float
    aggregate_average_cpu_percent: float
    aggregate_max_cpu_percent: float
    logical_cpu_count: int
    read_bytes: int
    write_bytes: int
    samples: int

    def to_dict(self) -> dict[str, float | int]:
        return asdict(self)


class ResourceMonitor:
    """Sample CPU, memory and IO for the current process and its children."""

    def __init__(self, interval_seconds: float = 0.25):
        self.interval_seconds = interval_seconds
        self._process = psutil.Process()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._rss_samples: list[float] = []
        self._cpu_samples: list[float] = []
        self._initial_io = self._io_totals()

    def _processes(self) -> list[psutil.Process]:
        processes = [self._process]
        try:
            processes.extend(self._process.children(recursive=True))
        except (psutil.Error, OSError):
            pass
        return processes

    def _io_totals(self) -> tuple[int, int]:
        read_bytes = 0
        write_bytes = 0
        for process in self._processes():
            try:
                counters = process.io_counters()
                read_bytes += int(counters.read_bytes)
                write_bytes += int(counters.write_bytes)
            except (psutil.Error, OSError, AttributeError):
                continue
        return read_bytes, write_bytes

    def _sample(self) -> None:
        while not self._stop_event.is_set():
            rss = 0
            cpu = 0.0
            for process in self._processes():
                try:
                    rss += int(process.memory_info().rss)
                    cpu += float(process.cpu_percent(interval=None))
                except (psutil.Error, OSError):
                    continue
            self._rss_samples.append(rss / (1024 * 1024))
            self._cpu_samples.append(cpu)
            self._stop_event.wait(self.interval_seconds)

    def start(self) -> None:
        for process in self._processes():
            try:
                process.cpu_percent(interval=None)
            except psutil.Error:
                continue
        self._thread = threading.Thread(
            target=self._sample,
            name="resource-monitor",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> ResourceSummary:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(1.0, self.interval_seconds * 4))
        if not self._rss_samples:
            self._rss_samples.append(self._process.memory_info().rss / (1024 * 1024))
        if not self._cpu_samples:
            self._cpu_samples.append(0.0)
        final_read, final_write = self._io_totals()
        logical_cpu_count = max(1, psutil.cpu_count(logical=True) or 1)
        aggregate_average_cpu = sum(self._cpu_samples) / len(self._cpu_samples)
        aggregate_max_cpu = max(self._cpu_samples)
        normalized_average_cpu = min(
            100.0,
            aggregate_average_cpu / logical_cpu_count,
        )
        normalized_max_cpu = min(
            100.0,
            aggregate_max_cpu / logical_cpu_count,
        )
        return ResourceSummary(
            peak_rss_mb=max(self._rss_samples),
            average_rss_mb=sum(self._rss_samples) / len(self._rss_samples),
            average_cpu_percent=normalized_average_cpu,
            max_cpu_percent=normalized_max_cpu,
            aggregate_average_cpu_percent=aggregate_average_cpu,
            aggregate_max_cpu_percent=aggregate_max_cpu,
            logical_cpu_count=logical_cpu_count,
            read_bytes=max(0, final_read - self._initial_io[0]),
            write_bytes=max(0, final_write - self._initial_io[1]),
            samples=len(self._rss_samples),
        )


class StageTimer:
    """Record named workflow stage durations."""

    def __init__(self, stage_name: str, sink: list[dict[str, object]]):
        self.stage_name = stage_name
        self.sink = sink
        self._started = 0.0

    def __enter__(self) -> "StageTimer":
        self._started = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        self.sink.append(
            {
                "stage_name": self.stage_name,
                "duration_seconds": time.perf_counter() - self._started,
                "status": "failed" if exc_type else "completed",
                "details": {},
            }
        )
        return False


__all__ = ["ResourceMonitor", "ResourceSummary", "StageTimer"]
