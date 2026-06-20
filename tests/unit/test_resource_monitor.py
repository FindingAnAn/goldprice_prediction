from src.utils import resource_monitor


def test_normalized_cpu_is_capped_at_100_percent(monkeypatch):
    monitor = resource_monitor.ResourceMonitor()
    monitor._rss_samples = [100.0]
    monitor._cpu_samples = [1_200.0, 1_440.0]
    monitor._initial_io = (0, 0)

    monkeypatch.setattr(resource_monitor.psutil, "cpu_count", lambda logical=True: 12)
    monkeypatch.setattr(monitor, "_io_totals", lambda: (0, 0))

    summary = monitor.stop()

    assert summary.average_cpu_percent == 100.0
    assert summary.max_cpu_percent == 100.0
    assert summary.aggregate_average_cpu_percent == 1_320.0
    assert summary.aggregate_max_cpu_percent == 1_440.0
