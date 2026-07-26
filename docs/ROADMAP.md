# Roadmap — Scriptorium

| Version | Date | Author | Description |
| --- | --- | --- | --- |
| 1.0.0 | 2026-07-26 | Claude | Bản đầu tiên — ghi lại backlog mở rộng skill do owner vạch ra (`important.md`), owner giao toàn quyền tự sắp thứ tự thực thi. |

---

## Bối cảnh

Owner cung cấp 4 nguồn ngoài đã verify sạch pháp lý (`docs/STATUS.md` không cần ghi nợ cho các nguồn này):

| Repo | Stars | License | Ghi chú |
| --- | --- | --- | --- |
| `google-gemini/gemini-cli` | 106,186 | Apache-2.0 | CLI agent, tham khảo pattern kiến trúc, không phải nguồn skill trực tiếp |
| `K-Dense-AI/scientific-agent-skills` | 31,783 | MIT | 148 skill khoa học thật trong `skills/` |
| `VoltAgent/awesome-agent-skills` | 28,962 | MIT | Danh sách liên kết tới 1000+ skill khác — dùng làm INDEX để tìm tiếp, bản thân không chứa skill |
| `mermaid-js/mermaid` | 89,421 | MIT | Cú pháp diagram, nguồn cho `mermaid-diagram-designer` |

Một bài blog "Top 10 kho Agent Skills" owner dán kèm có số liệu **không xác thực được** (vd "Matt Pocock Skills 130k+ stars" — repo thật cao nhất chỉ 59 sao; "Superpowers" không tìm thấy repo khớp trên GitHub) — **không dùng làm nguồn**, chỉ verify trực tiếp qua `gh api`/`gh search` như 4 repo trên.

Ảnh owner gửi (`1785053923858_...jpg`) là sơ đồ tổ chức 42 skill của một sản phẩm thương mại khác (nhóm theo phòng ban: Phát triển/Thiết kế/Marketing/Mạng xã hội/Tài chính/Doanh nghiệp nhỏ/Pháp lý) — dùng làm **cảm hứng cấu trúc mở rộng domain sau này**, không copy nội dung.

## Nguyên tắc áp dụng cho mọi skill mới từ giờ (owner, 2026-07-26)

Một skill chỉ có `SKILL.md` là CHƯA đạt chuẩn. Skill chất lượng cần đủ file bổ trợ (`scripts/`, `references/`, `assets/` khi phù hợp) để "nhìn qua là biết trước nó sẽ làm gì và thật sự muốn dùng" — không phải văn bản thuần túy mô tả ý định.

## Backlog (thứ tự thực thi do Claude tự chọn)

| # | Hạng mục | Lý do thứ tự | Trạng thái |
| --- | --- | --- | --- |
| 1 | `dedup-novelty-check` (stage 8) | Quy tắc đã có sẵn trong `registry/SCHEMA.md`, hoàn thiện nốt bộ xương pipeline (9/9 stage có skill vận hành) trước khi mở rộng ngang | Đang làm |
| 2 | `mermaid-diagram-designer` | MIT, kiến trúc rõ (cú pháp text → diagram), test được ngay không cần elicit dài | Kế tiếp |
| 3 | `translator-en-vi` | Không cần scout repo ngoài — elicit trực tiếp từ owner về kiểm soát chất lượng dịch (thuật ngữ, văn phong), mở rộng ngôn ngữ sau | Kế tiếp |
| 4 | LaTeX/research skill(s) từ `D:\elix\researches` | Cần đọc sâu hơn cấu trúc thật (`textbooks/document_engineering/`, `docs/methodology/idea_to_book_series.md`, `elix-textbook.cls`) để elicit đúng quy trình, không suy đoán — tốn thời gian hơn 3 mục trên | Sau |
| 5 | Scout sâu `scientific-agent-skills` (148 skill) + duyệt catalog `awesome-agent-skills` (1000+ entry) | Khối lượng lớn nhất, nên làm sau khi có thêm 3-4 skill mẫu chất lượng cao để đối chiếu chuẩn, tránh harvest hàng loạt rồi phát hiện sai chuẩn phải làm lại | Sau |
| 6 (tùy chọn) | Image-generation skill (dùng API key riêng của user) | Owner đánh dấu optional, tham khảo `D:/elix/platform/scripts`, `D:/UNI/S9_SP26/MLN131/project` | Chưa lên lịch cụ thể |

## Định hướng dài hạn (owner xác nhận hợp lý)

Cụm skill chung chung trước → skill theo đối tượng (học sinh, sinh viên, giáo viên, giảng viên) → bùng nổ theo ngành nghề. Khớp nguyên tắc đã có ở `docs/specs/STRATEGY_SPEC.md` §5 (vertical pháp lý là thử nghiệm đầu tiên, không phải duy nhất).

## Cấu trúc repo linh hoạt hơn (owner xác nhận)

Không bắt buộc mọi thứ nằm trong `skills/`. Được phép thêm thư mục ở root (`scripts/`, `venv` dùng chung...) nếu tiện — coi Scriptorium như một dự án bình thường, không phải một khuôn cứng chỉ chứa `skills/`.
