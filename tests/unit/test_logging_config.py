from __future__ import annotations

import logging

from src.utils.logging_config import (
    clear_log_context,
    get_logger,
    setup_logging,
)


def test_run_specific_file_handlers_can_be_added_after_logger_creation(tmp_path):
    logger = get_logger("tests.logging")
    human_log = tmp_path / "run.log"
    json_log = tmp_path / "run.jsonl"
    setup_logging(
        log_file=human_log,
        json_log_file=json_log,
        run_id="run-123",
        command="test",
    )

    logger.info("Model completed", extra={"model_name": "ridge"})
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert "run_id=run-123" in human_log.read_text(encoding="utf-8")
    json_text = json_log.read_text(encoding="utf-8")
    assert '"run_id": "run-123"' in json_text
    assert '"model_name": "ridge"' in json_text
    clear_log_context()
