# Seasonality, analog periods and forecast horizon

## Objective

The production cutoff is after the current gold session closes. The pipeline
predicts future trading sessions, not calendar days.

The default target remains `next_7_day_price`. Additional horizons are
available for comparison: 1, 3, 5, 7, 10, 21, 30 and 63 sessions.

## Added features

`features.seasonality_features` contains:

- calendar position: month, quarter, ISO week and day of year;
- cyclic month/year encodings;
- month-, quarter- and year-to-date returns;
- prior-year outcomes from the same month and quarter;
- prior-year outcomes within +/-10 calendar days of the same day of year;
- outcomes from historical regimes with similar 21-session momentum and
  volatility.

All analog rows must be at least one full year older than the current row.
Therefore their subsequent 5/7/10/21-session outcome was already observable at
the prediction cutoff.

## Empirical findings

The descriptive sample covers 2000 through June 18, 2026.

- The assumption that gold normally falls at year end was not supported.
- During the final 10 trading sessions of a year, the average subsequent
  7-session return was about +1.13%, with a 70% positive rate.
- December's average subsequent 21-session return was about +2.68%.
- December produced a positive average 21-session return in about 77% of
  sampled years.
- January and August also showed positive historical averages.

These statistics contain overlapping targets and are descriptive, not trading
evidence. Model selection must use chronological out-of-sample evaluation.

For the latest completed session, June 18, 2026:

- same-month historical analog: -0.19% over the next 7 sessions;
- same-day-of-year +/-10-day analog: -0.08%;
- similar momentum/volatility regime analog: +0.60%, with a 60.6% positive
  rate across 155 historical samples.

The disagreement is useful: calendar similarity alone is weak, while market
state similarity currently points in a different direction.

## Tabular horizon benchmark

Persistence was still selected by time-series CV for every horizon. For the
7-session target:

| Model | CV RMSE | Holdout RMSE | Direction accuracy |
|---|---:|---:|---:|
| Persistence | 36.60 | 99.05 | N/A |
| Same-day-of-year analog | 37.41 | 97.03 | 57.7% |
| Return Lasso | 110.58 | 98.31 | 57.3% |
| Return CatBoost | 40.67 | 103.26 | 48.5% |

The analog model improved the final holdout by about 2.0%, but its CV score was
slightly worse than persistence. It is retained as a feature/baseline rather
than selected after observing the holdout.

## Sequence model benchmark

TiDE and PatchTST were evaluated on rolling windows using 252 input sessions
and log price. PatchTST was rerun on 24 windows:

| Horizon | PatchTST RMSE | Persistence RMSE | Improvement |
|---:|---:|---:|---:|
| 5 | 135.48 | 139.27 | 2.7% |
| 7 | 163.18 | 185.54 | 12.1% |
| 10 | 109.66 | 120.56 | 9.0% |
| 21 | 233.73 | 240.17 | 2.7% |

The 7- and 10-session horizons provided the most useful balance of error and
directional performance. TiDE did not consistently beat persistence.

TabPFN-TS integration is present, but a benchmark requires one-time Prior Labs
license acceptance and checkpoint authentication. It is not included in the
reported comparison until that external requirement is completed.

## Recommendation

- Keep 7 trading sessions as the primary production horizon.
- Add 5 and 10 sessions as short-term uncertainty bands or secondary outputs.
- Add 21 sessions only as a separate tactical/monthly forecast.
- Do not replace 7 with 30 or 63 sessions: uncertainty and absolute error grow
  substantially, and these horizons answer a different business question.
- Treat PatchTST as an experimental challenger until it passes more rolling
  windows, regime-specific evaluation and live monitoring.
