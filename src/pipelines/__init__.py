"""Pipeline orchestration package with lazy imports."""

__all__ = [
    "EDAReport",
    "IngestionReport",
    "run_eda_pipeline",
    "run_ingestion_pipeline",
]


def __getattr__(name: str) -> object:
    """Avoid importing plotting dependencies for modeling-only workflows."""

    if name in {"EDAReport", "run_eda_pipeline"}:
        from .eda import EDAReport, run_eda_pipeline

        return {
            "EDAReport": EDAReport,
            "run_eda_pipeline": run_eda_pipeline,
        }[name]
    if name in {"IngestionReport", "run_ingestion_pipeline"}:
        from .ingestion import IngestionReport, run_ingestion_pipeline

        return {
            "IngestionReport": IngestionReport,
            "run_ingestion_pipeline": run_ingestion_pipeline,
        }[name]
    raise AttributeError(name)
