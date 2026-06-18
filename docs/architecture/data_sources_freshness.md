# Data Sources Freshness

Snapshot kiểm tra trực tiếp ngày 19/06/2026:

| Nguồn | Ngày mới nhất | Kết luận |
|---|---:|---|
| Yahoo Finance: gold, DXY, silver, S&P 500, VIX, oil futures | 18/06/2026 | Đúng latest market data |
| Yahoo Finance: 10Y và 30Y yield indices | 18/06/2026 | Dùng bổ sung khi FRED lag |
| FRED DGS10, DGS2, DGS30 | 16/06/2026 | Publication lag của nguồn |
| FRED T10YIE, SP500, VIXCLS, T10Y2Y | 17/06/2026 | Publication lag của nguồn |
| FRED DTWEXBGS | 12/06/2026 | Weekly/publication lag |
| FRED monthly CPI, Core CPI, Fed Funds, Retail Sales, Unemployment | 01/05/2026 | Đúng chu kỳ monthly |
| FRED M2 | 01/04/2026 | Đúng publication lag |
| EIA WTI/Brent spot | 15/06/2026 | EIA lag; staging bổ sung tail bằng futures |
| FreeGoldAPI | 20/02/2026 | Stale; chỉ giữ làm historical fallback |

## Nguyên nhân database chưa có latest data

Tại thời điểm kiểm tra, project không có `.env` và PostgreSQL trả về:
`password authentication failed for user "postgres"`.

API vẫn gọi được, nhưng ingestion không thể upsert vào raw tables. Cần tạo
`.env` từ `.env.example` với đúng `DB_PASSWORD` và `DB_NAME`.

## Các sửa đổi

- Yahoo Finance nhận `--end` theo nghĩa inclusive, sau đó chuyển sang end
  exclusive theo API Yahoo.
- FRED tự dùng public CSV chính thức nếu không có API key.
- Bỏ series ID `USINTR` không tồn tại và annual series bị khai báo sai monthly.
- EIA spot giữ ưu tiên; ngày EIA chưa công bố được bổ sung bằng CL=F/BZ=F.
- 10Y/30Y FRED lag được bổ sung bằng `^TNX`/`^TYX`.
- Sửa upsert làm phát sinh cột giả `index`.
- Conflict update cập nhật lại `updated_at`.
- Schema pipeline chỉ chạy DDL `01/02/03`; không chạy populate trước khi bảng tồn tại.
- Feature pipeline chạy EWMA trước `master_features`, tránh dữ liệu lệch một vòng.

## Lệnh kiểm tra

```bash
python scripts/check_data_freshness.py
python scripts/run_ingestion.py --start 2000-01-01
```

Không kỳ vọng tất cả nguồn có ngày 18–19/06/2026. Daily market data có thể đến
18/06; FRED và EIA có publication lag; monthly data có observation date theo
tháng gần nhất đã công bố.
