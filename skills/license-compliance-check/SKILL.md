---
name: license-compliance-check
description: Xác định license thật của một skill/repo ứng viên harvest và quyết định go/no-go trước khi nội dung đó chạm vào skill-creator. Dùng ngay sau skill scout/harvester (bước 6), bắt buộc trước khi bất kỳ nội dung harvested nào được dùng làm input cho skill-creator (bước 3) — không có ngoại lệ "chỉ tham khảo nội bộ". KHÔNG dùng để tự soạn thảo skill mới (đó là skill-creator) — skill này chỉ trả lời một câu: có được phép dùng nguồn này không, và dùng tới mức nào.
license: MIT
compatibility: Quy trình thuần đọc + phân loại, không phụ thuộc harness cụ thể. Verify chạy sạch: Claude Code (2026-07-26, áp dụng thật lên github.com/anthropics/skills qua `gh api`).
metadata:
  domain: meta
  task_type: review-qa
  risk_tier: N2
  source: self-authored
  elicited_from: "Elicited từ một case thật 2026-07-26: kiểm tra license của github.com/anthropics/skills (dùng gh api đọc trực tiếp LICENSE.txt từng skill + THIRD_PARTY_NOTICES.md) — phát hiện license hỗn hợp trong cùng 1 repo, là bằng chứng cụ thể cho lý do bước này phải tách riêng, không suy đoán theo lô"
  version: 0.1.0
---

# license-compliance-check

Trả lời đúng 1 câu cho mỗi ứng viên harvest: **được phép dùng tới mức nào**. Không suy đoán license theo tên repo, theo README tổng quát, hay theo "trông giống open source" — luôn đọc file license thật.

## Vì sao không suy đoán theo lô (case thật, 2026-07-26)

`github.com/anthropics/skills` không có 1 LICENSE gốc áp dụng cho toàn repo (`gh api repos/anthropics/skills --jq '.license'` trả về rỗng). README nói "many skills... are open source (Apache 2.0)" — nhưng `skills/pdf/LICENSE.txt` lại là điều khoản độc quyền của Anthropic, cấm tuyệt đối extract/copy/derive/distribute. Nếu suy đoán "repo này nhìn chung mở" rồi harvest cả `pdf/`, đó là vi phạm license thật. **Luôn đọc license ở cấp file/folder cụ thể của đúng thứ định harvest, không phải cấp repo.**

## Quy trình

1. **Tìm file license đúng cấp.** Thứ tự ưu tiên: license file trong chính folder/skill định harvest (vd `skills/<x>/LICENSE.txt`) → license file gốc repo (`LICENSE`, `LICENSE.txt`, `COPYING`) → `license` field trong `package.json`/`pyproject.toml`/frontmatter SKILL.md → GitHub API `repos/{owner}/{repo}` field `license`. Dừng ở cấp đầu tiên tìm thấy — cấp cụ thể hơn luôn thắng cấp chung hơn (bài học từ case anthropics/skills).
2. **Không tìm thấy license nào** → mặc định **BLOCKED**. Không có license = giữ toàn quyền tác giả gốc theo luật bản quyền mặc định, không phải "coi như tự do dùng".
3. **Phân loại** license tìm được vào 1 trong 4 nhóm:
   - **Permissive** (MIT, Apache-2.0, BSD-2/3-Clause, ISC) → **SAFE**: được adapt/harvest, giữ attribution; nếu Apache-2.0, phải thêm change-notice khi sửa đổi (§4(b)).
   - **Copyleft** (GPL/AGPL/LGPL bất kỳ bản) → **BLOCKED cho việc nhúng trực tiếp** vào skill của Scriptorium (MIT) — copyleft lan truyền nghĩa vụ mở nguồn. Chỉ chấp nhận nếu gọi như dependency/subprocess tách biệt (không tĩnh-link, không copy code), và phải flag cho owner duyệt case-by-case, không tự quyết.
   - **Source-available / proprietary có điều khoản hạn chế riêng** (như `pdf/LICENSE.txt` của Anthropic) → **BLOCKED tuyệt đối**. Đọc kỹ điều khoản — nếu có dòng cấm "extract/copy/retain/derive/distribute", không được chạm dù chỉ để "xem cách họ làm rồi viết lại từ đầu bằng lời văn khác" (đó vẫn là derivative work theo điều khoản).
   - **Ambiguous/dual-license/chưa rõ** → **BLOCKED**, báo lại cho owner, không tự chọn diễn giải có lợi.
4. **Ghi provenance** cho mỗi quyết định: `{candidate, repo_url, path, commit, license_found, classification, decision, date}`. Đây là input trực tiếp cho field `source` + `license` của `registry/skills.json` (xem `registry/SCHEMA.md`) nếu quyết định là SAFE và tiếp tục harvest.
5. Nếu SAFE: bàn giao cho bước tiếp theo (dedup/novelty-check, bước 8) rồi mới tới skill-creator (bước 3) — license-compliance-check không tự viết SKILL.md.

## Output

Một bảng quyết định (candidate → license → classification → SAFE/BLOCKED → lý do), không phải một SKILL.md. Chỉ ứng viên SAFE mới được truyền tiếp xuống pipeline.

## Case thật đã chạy (2026-07-26): `github.com/anthropics/skills`

| Candidate | License tìm thấy | Classification | Quyết định |
| --- | --- | --- | --- |
| `skills/skill-creator/` | Apache-2.0 (LICENSE.txt riêng trong folder) | Permissive | **SAFE** — attribution + change-notice khi adapt |
| `skills/pdf/`, `skills/docx/`, `skills/pptx/`, `skills/xlsx/` | Điều khoản độc quyền Anthropic (LICENSE.txt riêng, cấm extract/copy/derive/distribute) | Proprietary, no-redistribution | **BLOCKED tuyệt đối** |
| Các skill khác trong `skills/` (mcp-builder, webapp-testing, frontend-design...) | Chưa kiểm từng cái — README chỉ nói "many", không phải "all" | Chưa phân loại | **Chưa quyết định — cần kiểm riêng từng skill trước khi harvest bất kỳ cái nào trong nhóm này** |
