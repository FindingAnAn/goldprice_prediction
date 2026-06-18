from __future__ import annotations

from pathlib import Path

import pandas as pd
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

import scripts.run_modeling as run_modeling


class DummyBest:
    def __init__(self):
        self.name = "dummy"
        self.cv_rmse = 1.23
        self.test_rmse = 4.56
        self.params = {"alpha": 0.1}
        self.model = object()


def test_build_parser_accepts_all_subcommands():
    parser = run_modeling.build_parser()

    assert parser.parse_args(["train"]).command == "train"
    assert parser.parse_args(["evaluate"]).command == "evaluate"
    assert parser.parse_args(["predict"]).command == "predict"
    assert parser.parse_args(["autogluon"]).command == "autogluon"
    assert parser.parse_args(["train"]).target_col == "next_7_day_price"


def test_main_train_smoke_uses_log_file_and_prints(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    tmp_path: Path,
) -> None:
    recorded: dict[str, object] = {}

    def fake_setup_logging(level: str | None = None, log_file: Path | None = None) -> None:
        recorded["level"] = level
        recorded["log_file"] = log_file

    monkeypatch.setattr(run_modeling, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(run_modeling, "setup_logging", fake_setup_logging)
    monkeypatch.setattr(run_modeling, "train_and_select_best", lambda **kwargs: DummyBest())
    monkeypatch.setattr(run_modeling.sys, "argv", ["run_modeling.py", "train"])

    run_modeling.main()

    out = capsys.readouterr().out
    assert "Best model: dummy" in out
    assert recorded["log_file"] == tmp_path / "logs" / "modeling" / "run_modeling_train.log"


def test_main_evaluate_smoke(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    tmp_path: Path,
) -> None:
    recorded: dict[str, object] = {}

    def fake_setup_logging(level: str | None = None, log_file: Path | None = None) -> None:
        recorded["level"] = level
        recorded["log_file"] = log_file

    monkeypatch.setattr(run_modeling, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(run_modeling, "setup_logging", fake_setup_logging)
    monkeypatch.setattr(run_modeling, "load_best_model", lambda path: object())
    monkeypatch.setattr(
        run_modeling,
        "build_training_frame",
        lambda **kwargs: pd.DataFrame(
            {"f1": [1.0, 2.0], "next_1_day_price": [1.0, 2.0]},
            index=pd.date_range("2024-01-01", periods=2, freq="D"),
        ),
    )
    monkeypatch.setattr(run_modeling, "evaluate_holdout_model", lambda model, frame, **kwargs: {"rmse": 0.5})
    monkeypatch.setattr(
        run_modeling.sys,
        "argv",
        ["run_modeling.py", "evaluate", "--target-col", "next_1_day_price"],
    )

    run_modeling.main()

    out = capsys.readouterr().out
    assert "Holdout RMSE: 0.5000" in out
    assert recorded["log_file"] == tmp_path / "logs" / "modeling" / "run_modeling_evaluate.log"


def test_main_predict_smoke(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
    tmp_path: Path,
) -> None:
    recorded: dict[str, object] = {}
    output = pd.DataFrame({"prediction": [12.34]}, index=pd.date_range("2024-01-01", periods=1, freq="D"))

    def fake_setup_logging(level: str | None = None, log_file: Path | None = None) -> None:
        recorded["level"] = level
        recorded["log_file"] = log_file

    monkeypatch.setattr(run_modeling, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(run_modeling, "setup_logging", fake_setup_logging)
    monkeypatch.setattr(run_modeling, "load_best_model", lambda path: object())
    monkeypatch.setattr(run_modeling, "predict_latest", lambda **kwargs: output)
    monkeypatch.setattr(run_modeling.sys, "argv", ["run_modeling.py", "predict"])

    run_modeling.main()

    out = capsys.readouterr().out
    assert "prediction" in out
    assert recorded["log_file"] == tmp_path / "logs" / "modeling" / "run_modeling_predict.log"
