# Forecasting Research Review — 2026-06-21

## Current error assessment

The previous PatchTST benchmark produced mean RMSE 136.41, MAE 103.78 and MAPE
2.34% across horizons 1, 3, 5, 7 and 10. Mean actual price was about 4,564, so
RMSE was 2.99% of the mean price.

This error is not directly comparable with published raw RMSE values because
gold price levels, currencies, date ranges, horizons and split policies differ.
MAPE, normalized RMSE and a strictly chronological evaluation are more useful.
Six windows are still a small sample and must not be treated as a stable
estimate of live performance.

## Relevant methods and implementation decision

| Work/project | Main finding | Project decision |
|---|---|---|
| [XGBoost](https://arxiv.org/abs/1603.02754) | Regularized tree boosting is strong for nonlinear tabular relationships and sparse inputs. | Added `XGBoostDirect`. |
| [LightGBM](https://proceedings.neurips.cc/paper/6907-lightgbm-a-highly-efficient-gradient-boosting-decision-tree) | Histogram-based boosting provides efficient nonlinear learning. | Added `LightGBMDirect`. |
| [DLinear/NLinear](https://arxiv.org/abs/2205.13504) | Simple linear models can outperform complex transformers on time-series benchmarks. | Added both as low-variance sequence controls. |
| [PatchTST](https://arxiv.org/abs/2211.14730) | Patching preserves local information and supports longer lookback efficiently. | Retained as the transformer benchmark. |
| [TiDE](https://arxiv.org/abs/2304.08424) | Dense encoder supports covariates and nonlinear dependencies with lower cost than many transformers. | Retained for multivariate sequence forecasting. |
| [N-HiTS](https://arxiv.org/abs/2201.12886) | Multi-rate hierarchical interpolation targets different signal frequencies. | Retained for multi-resolution forecasting. |
| [TabPFN-TS](https://arxiv.org/abs/2501.02945) | Temporal featurization plus a pretrained tabular foundation model is competitive for small, covariate-aware datasets. | Kept as the next research candidate; excluded from production until model-download, runtime and reproducibility constraints are isolated. |
| [scikit-learn lagged-feature example](https://scikit-learn.org/stable/auto_examples/applications/plot_time_series_lagged_features.html) | Random splits are overly optimistic; lagged features require time-aware evaluation. | Implemented rolling cutoffs with horizon-specific label purging. |

## Implemented optimization

1. Predict stationary log returns `log(open[t+h]/close[t])`, then reconstruct
   the price. This avoids forcing tree models to extrapolate the long-run price
   level directly.
2. Train a separate model for each of the ten horizons. No recursive forecast
   is used.
3. Use a five-year sliding training window to adapt to regime changes.
4. Add lag and rolling features at 5, 10, 21, 63, 126 and 252 sessions:
   return, volatility, min/max return, trend slope, distance to rolling mean,
   drawdown and rebound.
5. Retain macro, cross-asset, CFTC and prior-year analog features only when
   available at the forecast cutoff.
6. Evaluate sequence and tabular candidates on the same six rolling origins.
7. Save RMSE, MAE, MAPE, sMAPE, normalized RMSE and direction accuracy.

## Full controlled result

The complete 6-window/100-step pipeline produced:

| Model | Mean RMSE | Mean MAE | Mean MAPE |
|---|---:|---:|---:|
| RidgeXGBoostBlend | 87.07 | 74.84 | 1.66% |
| XGBoostDirect | 93.82 | 80.15 | 1.78% |
| RidgeDirect | 95.55 | 84.81 | 1.87% |
| LightGBMDirect | 102.14 | 87.91 | 1.95% |
| Previous PatchTST | 136.41 | 103.78 | 2.34% |

The RMSE reduction from 136.41 to 87.07 is 36.17%. It is
promising, but the estimate remains uncertain because it contains only six
forecast origins and must be monitored on subsequently realized forecasts.
