# Master Context — Scriptorium

| Version | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-26 | Claude | Bản đầu tiên, viết cùng lúc với việc thiết lập quy chế tài liệu của dự án (tham khảo cấu trúc docs của `D:/elix/platform`). |

---

## Quick Summary

| Property | Value |
| --- | --- |
| **Project Name** | Scriptorium (`elix/scriptorium`) |
| **Project Type** | Hệ thống tạo / kiểm định chất lượng / audit bảo mật / quản lý danh mục cho Agent Skill portable |
| **Core Philosophy** | Skill-first, không xây harness. Elicit → research → skill_creator → quality eval → security audit → registry, thứ tự không đảo. |
| **Tiền nhiệm** | EduStation (`D:/elix/edustation`) — pivot vì governance-trước-traction, không phải vì kiến trúc sai. Xem `docs/specs/STRATEGY_SPEC.md` §1. |
| **Vertical thử nghiệm** | Pháp lý Việt Nam, định vị lớp meta (sản xuất + audit skill), không phải chatbot tra luật. |
| **AI backend (chưa dùng)** | Elixverse (`D:/elix/platform`) — xem gate ở `docs/specs/STRATEGY_SPEC.md` §6 trước khi tích hợp. |

---

## 1. Cái gì đang được xây (hiện tại)

Một pipeline 9 bước và bộ meta-skill vận hành chính pipeline đó (xem `docs/specs/STRATEGY_SPEC.md` §3 để biết trạng thái từng bước). Sản phẩm hữu hình của mỗi bước là:

- Một hoặc nhiều `SKILL.md` trong `skills/<skill_id>/`, đúng 6-field spec agentskills.io.
- Một entry trong `registry/skills.json`, đúng schema `registry/SCHEMA.md`.

## 2. KHÔNG xây gì

- Không app/CLI/harness riêng — skill chạy trên hệ sinh thái sẵn có (~44 platform đã hỗ trợ Agent Skills giữa 2026).
- Không manifest riêng ngoài spec agentskills.io — field riêng luôn nằm trong `metadata` của frontmatter.
- Không gộp quality evaluation và security audit thành một bước.

## 3. Cấu trúc repo

```
scriptorium/
├── README.md                  # Entry point — tóm tắt + pointer vào docs/
├── docs/
│   ├── README.md               # Navigation hub (bạn nên đọc file này trước)
│   ├── MASTER_CONTEXT.md       # File này — kiến trúc & phạm vi
│   ├── STATUS.md               # Trạng thái thật, verify theo skills/ + registry/
│   ├── DECISIONS_PENDING.md    # Quyết định kiến trúc đang chờ owner xác nhận
│   ├── specs/                  # SPEC chính thức — nguồn xác thực hiện tại
│   │   └── STRATEGY_SPEC.md
│   └── archive/                # History, not current state — xem archive/README.md
├── skills/
│   └── <skill_id>/SKILL.md     # Mỗi skill là một thư mục con
└── registry/
    ├── SCHEMA.md                # Schema đăng ký đa trục
    └── skills.json              # Dữ liệu đăng ký
```

## 4. Quy chế tài liệu (documentation convention)

Tham khảo trực tiếp cách `D:/elix/platform/docs/` vận hành (README nav hub, versioned header table, `DECISIONS_PENDING.md` với format chuẩn, archive dated khi có pivot), áp dụng cho Scriptorium ở quy mô nhỏ hơn:

- **Mọi doc "current" (`MASTER_CONTEXT.md`, `STATUS.md`, `DECISIONS_PENDING.md`, mọi file trong `specs/`) có bảng version header ở đầu** — Version/Date/Author/Description. Tăng version khi nội dung đổi có ý nghĩa, không sửa âm thầm.
- **Code/skill thật thắng doc khi mâu thuẫn.** `STATUS.md` phải verify được từ `registry/skills.json` + `skills/`, không viết theo trí nhớ hay dự định.
- **`docs/archive/` là lịch sử, không phải nguồn xác thực hiện tại.** Khi có một vòng chưng cất lớn (như research → STRATEGY_SPEC lần này), file thảo luận/research thô chuyển vào một thư mục con đặt tên theo ngày (`pre-spec-YYYY-MM-DD/`), giữ nguyên nội dung, không sửa.
- **`DECISIONS_PENDING.md`** dùng đúng 1 format cho mỗi mục: câu hỏi → khuyến nghị + lý do → action plan → `Decision: [ ] OK / [ ] Override: ___`. Xóa mục khi owner đã quyết, không để tồn đọng.
- Chưa cần `CHANGELOG.md`/`TODO.md`/`ROADMAP.md`/`guides/`/`tracebacks/` ở quy mô hiện tại của Scriptorium (1 skill, chưa có code chạy) — thêm khi thực sự cần, không dựng sẵn khung rỗng.
