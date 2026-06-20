# Modeling Workflow

## Forecast contract

Input tại ngày `t` dùng thông tin đã biết sau khi phiên `t` đóng cửa. Output là
Open của 10 phiên kế tiếp.

## Candidate set

| Model | Input | Vai trò |
|---|---|---|
| Persistence Close | Current close | Baseline bắt buộc |
| TiDE | Open + historical exogenous | Dense multivariate sequence |
| PatchTST | Open sequence | Patch-based univariate transformer |
| N-HiTS | Open + historical exogenous | Multi-resolution challenger |

Tabular regressors, AutoGluon và TabPFN-TS không còn trong benchmark hiện tại.
Chúng không cùng sequence/multi-horizon contract và tạo hai pipeline khó kiểm
soát.

## Sequence preparation

- Sắp xếp tăng dần theo date.
- Target: `log(gold_open)`.
- Thay infinity bằng null.
- Chỉ giữ exogenous có coverage >= 80%.
- Chỉ forward-fill; không backward-fill.
- Input window 252 phiên, validation tail 63 phiên.

PatchTST implementation hiện dùng univariate input. TiDE và N-HiTS dùng
historical exogenous.

## Evaluation

Rolling windows dự báo 10 bước. Metric được lưu riêng tại horizon 1, 3, 5, 7,
10:

- RMSE;
- MAE;
- MAPE;
- direction accuracy so với current price;
- persistence RMSE;
- RMSE improvement so với persistence.

Candidate tốt nhất là candidate có mean rolling RMSE thấp nhất. Không mặc định
deep model tốt hơn baseline.

## Production fit và interval

Sau selection, mỗi deep model được fit lại trên full eligible sequence và lưu
artifact. Forecast model được chọn tạo 10 giá trị. Khoảng 80%/95% dùng empirical
absolute residual quantile theo từng forecast step; đây không phải calibrated
probabilistic interval.

## Explanation

Direction được tính từ predicted Open so với current Close với flat threshold
0.05%. Top reasons xếp hạng rule-based evidence từ DXY, real yield, VIX, EPU,
credit, CFTC và GLD. Chúng không giải thích nội tại của neural network.
