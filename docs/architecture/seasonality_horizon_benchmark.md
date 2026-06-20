# Seasonality and Horizon Analysis

## Mục tiêu

Seasonality không được dùng như một quy luật cố định. Pipeline đo xem các vị trí
tương đồng trong tháng, quý, năm, day-of-year và market regime có thống kê ổn
định hay không.

## Sliding windows

- 5 phiên: biến động rất ngắn.
- 21 phiên: gần một tháng giao dịch.
- 63 phiên: gần một quý.
- 252 phiên: gần một năm.
- EWMA 7/30/90/365 ngày: trọng số giảm dần theo thời gian.

## Calendar features

- month, quarter, ISO week, day-of-year;
- cyclic sine/cosine;
- progress trong tháng/quý/năm;
- month/quarter/year-to-date return;
- days to year end.

## Historical analogs

- same month: future return 5/7/21 phiên;
- same quarter: future return 21 phiên;
- day-of-year ±10 ngày: future return 5/7/10/21 phiên;
- regime analog: gần nhau về 21-session momentum và volatility.

Mỗi analog lưu mean, up-rate và sample count. Historical observation phải cách
current date ít nhất một năm.

## Horizon 10 phiên

Mười phiên tương đương khoảng hai tuần, phù hợp với:

- dữ liệu daily và tốc độ cập nhật macro;
- nhu cầu dự báo từng ngày thay vì một target tổng hợp;
- giới hạn uncertainty trước khi signal suy giảm mạnh.

Không nên tăng horizon chỉ để có nhiều output. Nếu cần 20–30 phiên, phải benchmark
riêng vì interval, calendar risk và regime change tăng đáng kể.

## Lệnh phân tích

```powershell
python scripts/analyze_similarity.py
```

Output:

- `monthly_seasonality.csv`;
- `quarterly_seasonality.csv`;
- `calendar_events.csv`;
- `market_regimes.csv`;
- `latest_analogs.csv`.

Không kết luận seasonal effect nếu sample nhỏ, t-stat yếu hoặc dấu không ổn định
giữa các năm.
