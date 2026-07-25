# Decisions Pending — Scriptorium

Thêm một mục mới khi có một fork kiến trúc thật cần owner xác nhận trước khi tiếp tục. Format cố định: câu hỏi → khuyến nghị + lý do → action plan → `Decision: [ ] OK / [ ] Override: ___`. Xóa mục khi đã quyết, không để tồn đọng.

---

## 1. Meta-skill nào xây tiếp theo sau `skill_creator`?

**Câu hỏi**: Bootstrap pipeline còn 5 stage chưa có skill vận hành (elicit-tacit-process, quality-eval, security-audit, scout/harvester, license-compliance). Xây theo thứ tự nào?

**Khuyến nghị**: `elicit-tacit-process` trước. Lý do — mọi skill domain thật (kể cả vertical pháp lý ở Phase 2) đều cần qua bước này trước `skill_creator`; hiện chưa có gì chuẩn hóa cách elicit ngoài việc làm thủ công qua hội thoại. `quality-eval` và `security-audit` có thể chờ tới khi có ≥1 skill domain thật để chấm — chấm chính `skill_creator` (một meta-skill) không đại diện tốt cho việc skill đó có ích trên tác vụ thật.

**Action plan nếu OK**: elicit quy trình elicit-tacit-process từ owner (recursive nhưng đúng nguyên tắc — không tự suy luận quy trình phỏng vấn chuyên gia mà không hỏi owner cách owner thực sự làm việc này với EduStation), rồi chạy `skill_creator` để sinh `skills/elicit-tacit-process/SKILL.md`.

**Decision**: [ ] OK / [ ] Override: ___

---

## 2. Elixverse có phải backend AI đầu tiên cho quality-eval loop không?

**Câu hỏi**: Khi `quality-eval` (stage 4) được xây, nó cần gọi LLM thật trên ≥2 harness để chấm skill. Dùng Elixverse (`D:/elix/platform`) hay API key nhà cung cấp trực tiếp (Anthropic/OpenAI) trong lúc chờ platform team thêm spend-cap/scoped-key?

**Khuyến nghị**: dùng API key trực tiếp, có giới hạn chi tiêu thủ công (theo dõi tay), cho tới khi Elixverse có spend-cap/scoped-key thật — không chờ platform team nếu điều đó chặn tiến độ Scriptorium; cũng không dùng `elix_sk_...` toàn quyền cho một agent loop tự động, kể cả loop ngắn, đúng nguyên tắc đã ghi ở `docs/specs/STRATEGY_SPEC.md` §6.

**Action plan nếu OK**: quality-eval skill nhận backend qua config, mặc định key nhà cung cấp; thêm Elixverse như một backend tùy chọn sau khi platform xác nhận đã có spend-cap.

**Decision**: [ ] OK / [ ] Override: ___
