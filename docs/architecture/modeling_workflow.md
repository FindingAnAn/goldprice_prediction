# Modeling Workflow

## Forecast contract

Input tại ngày `t` dùng thông tin đã biết sau khi phiên `t` đóng cửa. Output là
Open của 10 phiên kế tiếp.

## Candidate set

| Model | Input | Vai trò |
|---|---|---|
| TiDE | Open + historical exogenous | Dense multivariate sequence |
| PatchTST | Open sequence | Patch-based univariate transformer |
| N-HiTS | Open + historical exogenous | Multi-resolution challenger |
| DLinear / NLinear | Open sequence | Low-variance linear sequence controls |
| RidgeDirect | Engineered tabular features | Regularized direct horizon model |
| XGBoostDirect | Engineered tabular features | Nonlinear boosted trees |
| LightGBMDirect | Engineered tabular features | Efficient boosted trees |
| RidgeXGBoostBlend | Ridge + XGBoost | Fixed-weight variance reduction |

TabPFN-TS remains a research candidate, not a production dependency. The
current tabular benchmark is deterministic, serializable and does not require a
pretrained model download.

## Sequence preparation

- Sắp xếp tăng dần theo date.
- Target: `log(gold_open)`.
- Thay infinity bằng null.
- Chỉ giữ exogenous có coverage >= 80%.
- Chỉ forward-fill; không backward-fill.
- Input window 252 phiên, validation tail 63 phiên.

PatchTST implementation hiện dùng univariate input. TiDE và N-HiTS dùng
historical exogenous.

## Direct tabular preparation

- Target horizon `h`: `log(open[t+h] / close[t])`.
- One independent estimator per horizon 1..10; no recursive forecast error.
- Rolling training window: 1,260 sessions to reduce old-regime dominance.
- Lags: 1/2/3/5/10/21/63/126/252 sessions.
- Rolling statistics: 5/10/21/63/126/252 sessions.
- Features include return, volatility, slope, distance to mean/high/low,
  macro-market drivers, CFTC positioning and leakage-safe seasonal analogs.
- Known future calendar variables are allowed; unknown future market values
  are never supplied.

## Evaluation

Rolling windows dự báo 10 bước. Metric được lưu riêng tại horizon 1, 3, 5, 7,
10:

- RMSE;
- MAE;
- MAPE;
- sMAPE;
- normalized RMSE as a percentage of mean actual price;
- direction accuracy so với current price;

Candidate tốt nhất là candidate có mean rolling RMSE thấp nhất.

## Production fit và interval

Sau selection, sequence models và direct models được fit lại và lưu artifact.
Forecast model được chọn tạo 10 giá trị. Khoảng 80%/95% dùng empirical
absolute residual quantile theo từng forecast step; đây không phải calibrated
probabilistic interval.

## Explanation

Direction dùng `UP`, `DOWN`, `FLAT`. Top reasons và toàn bộ artifact output dùng
tiếng Anh. Reasons xếp hạng rule-based evidence từ DXY, real yield, VIX, EPU,
credit, CFTC và GLD; chúng không phải SHAP hoặc causal attribution.
