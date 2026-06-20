# Data Sources and Freshness

## Chính sách

`DATA_START_DATE = 2010-01-01`. Khi `end=None`, Yahoo chỉ tải đến phiên Mỹ đã
hoàn tất an toàn: ngày hiện tại sau 18:00 New York, nếu không thì phiên làm việc
trước đó. Yahoo `end` là exclusive nên pipeline tự cộng một ngày.

## Nguồn

| Nguồn | Dữ liệu | Freshness/availability |
|---|---|---|
| Yahoo Finance | GC=F và market proxies | Latest completed US session |
| FreeGoldAPI | gold history | Fallback; có thể trễ |
| FRED daily | rates, DXY, VIX, real yield, EPU, credit | Join từ observation date + 1 ngày |
| FRED monthly | CPI, Fed funds, M2, unemployment | Lưu DB nhưng cấm model |
| CFTC | weekly gold positioning | Tuesday report, available Friday (+3 ngày) |
| EIA | WTI/Brent | Yahoo futures fallback khi thiếu key/lỗi |

Annual CFTC archives cung cấp lịch sử; current report được append để tránh độ
trễ của archive năm hiện tại.

## Series có giới hạn lịch sử

FRED `BAMLH0A0HYM2` hiện chỉ phân phối khoảng ba năm gần nhất. Series vẫn có
giá trị phân tích stress tín dụng nhưng không được phép làm co sequence dataset.
Sequence preparation chỉ giữ exogenous feature có coverage tối thiểu 80%.

## Kiểm tra

```powershell
python scripts/check_data_freshness.py
```

Lệnh gọi API gần hiện tại và đọc `MAX(date)`/`MAX(available_date)` trong DB.
Không đồng nhất ngày giữa các nguồn là bình thường do lịch giao dịch và lịch
phát hành khác nhau.

## Điều kiện chặn full refresh

Pipeline fail nếu thiếu gold, Yahoo GC=F, FRED DFII10, FRED USEPUINDXD, CFTC
hoặc nếu feature/staging có dưới 1.000 dòng.

## Rủi ro còn lại

- Yahoo Finance không có SLA chính thức.
- FRED daily lag +1 là approximation, không thay thế ALFRED vintage.
- CFTC có thể hoãn phát hành dịp lễ.
- CME holiday calendar chưa được dùng cho `forecast_date`.

Nguồn chính thức:

- [CFTC current disaggregated futures report](https://www.cftc.gov/dea/newcot/f_disagg.txt)
- [FRED BAMLH0A0HYM2](https://fred.stlouisfed.org/series/BAMLH0A0HYM2)
