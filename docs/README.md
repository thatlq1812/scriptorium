# Documentation — Scriptorium

Navigation hub. Đọc `MASTER_CONTEXT.md` trước nếu chưa quen dự án.

## Đọc theo thứ tự

1. [MASTER_CONTEXT.md](MASTER_CONTEXT.md) — Scriptorium là gì, cấu trúc repo, quy chế tài liệu.
2. [STATUS.md](STATUS.md) — trạng thái thật hiện tại (skill nào đã có, stage nào chưa xây), verify theo `registry/skills.json`.
3. [DECISIONS_PENDING.md](DECISIONS_PENDING.md) — quyết định kiến trúc đang chờ owner xác nhận trước khi tiếp tục.
4. [specs/STRATEGY_SPEC.md](specs/STRATEGY_SPEC.md) — nguồn xác thực cho định hướng chiến lược, pipeline, taxonomy, vertical pháp lý, gate Elixverse.

## Thư mục

| Path | Nội dung |
| --- | --- |
| `specs/` | SPEC chính thức, đang active. Viết SPEC mới ở đây khi có quyết định/tính năng đủ lớn cần chưng cất thành nguồn xác thực. |
| `archive/` | Lịch sử — transcript thảo luận, research thô đã chưng cất vào `specs/`. Xem `archive/README.md`. Không trích số liệu/quyết định trực tiếp từ đây nếu `specs/` đã có bản đã sửa. |

## Quy tắc khi mâu thuẫn

`skills/` và `registry/` (code/skill thật) thắng mọi doc. Trong docs, `specs/` thắng `archive/`. `STATUS.md` phải verify được từ `registry/skills.json` — nếu lệch, sửa `STATUS.md`, không sửa registry để khớp doc.
