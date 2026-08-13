# Nghị định 30/2020/NĐ-CP — thể thức văn bản hành chính (grounding for the vnnd30 mode)

Source: the real government PDF (`30.signed.pdf`, downloaded 2026-07-27 directly from
`https://datafiles.chinhphu.vn/cpp/files/vbpq/2020/03/30.signed.pdf`, linked from the
official page `https://vanban.chinhphu.vn/default.aspx?pageid=27160&docid=199378`), read
directly page by page — not from a secondary source. Kept here (committed) rather than
only in `outside_research/research_03_nd30/` (gitignored, session-local) so this skill
stays portable/distributable with its own grounding intact.

## Quy định chung (Phụ lục I, Mục I)

- Khổ giấy: A4 (210mm x 297mm), trình bày theo chiều dài.
- Lề trang (range cho phép): trên/dưới 20-25mm, trái 30-35mm, phải 15-20mm. `vnnd30.sty`
  defaults to the lower bound of each range (top/bottom 20mm, left 30mm, right 15mm) as a
  concrete implementation choice within the permitted range — adjustable via package
  options if a specific agency's house style needs a different value inside the same range.
- Phông chữ: Times New Roman, Unicode (TCVN 6909:2001), màu đen — `vnnd30.sty` loads it via
  `fontspec` (XeLaTeX), not `babel`, matching `latex-project-bootstrap`'s existing Vietnamese
  guidance in `vietnamese-latex-setup.md`.
- Số trang: chữ số Ả Rập, cỡ 13-14, đứng, canh giữa lề trên, KHÔNG hiển thị ở trang đầu.

## Bảng mẫu chữ (Phụ lục I, Mục V) — nguồn của mọi macro trong vnnd30.sty

| Ô | Thành phần | Loại chữ | Cỡ | Kiểu |
|---|---|---|---|---|
| 1 | Quốc hiệu | In hoa | 12-13 | Đứng, đậm |
| 1 | Tiêu ngữ | In thường | 13-14 | Đứng, đậm |
| 2 | Cơ quan chủ quản trực tiếp | In hoa | 12-13 | Đứng |
| 2 | Cơ quan ban hành | In hoa | 12-13 | Đứng, đậm |
| 3 | Số, ký hiệu | In thường | 13 | Đứng |
| 4 | Địa danh, ngày tháng | In thường | 13-14 | Nghiêng |
| 5a | Tên loại văn bản | In hoa | 13-14 | Đứng, đậm |
| 5a | Trích yếu (văn bản có tên loại) | In thường | 13-14 | Đứng, đậm |
| 5b | Trích yếu công văn ("V/v ...") | In thường | 12-13 | Đứng |
| 6 | Nội dung | In thường | 13-14 | Đứng |
| 6 | "Điều" + số + tiêu đề Điều | In thường | = cỡ lời văn | Đứng, đậm |
| 7a | Quyền hạn người ký (TM./Q./KT./TL./TUQ.) | In hoa | 13-14 | Đứng, đậm |
| 7b | Chức vụ người ký | In hoa | 13-14 | Đứng, đậm |
| 7c | Họ tên người ký | In thường | 13-14 | Đứng, đậm |
| 9a | "Kính gửi" + nơi nhận (công văn) | In thường | 13-14 | Đứng |
| 9b | "Nơi nhận" | In thường | 12 | Nghiêng, đậm |
| 9b | Danh sách nơi nhận | In thường | 11 | Đứng |

Ghi chú gốc: cỡ chữ trong cùng một văn bản phải tăng/giảm thống nhất theo 1 trong 2 bộ
(Quốc hiệu 12 + Tiêu ngữ/địa danh 13, hoặc Quốc hiệu 13 + Tiêu ngữ/địa danh 14) — không trộn.
`vnnd30.sty` fixes one consistent set (12/13) as the default.

## 3 mẫu thật đã dựng thành template (Phụ lục III, Mục II — mẫu trực quan thật)

- **Mẫu 1.5 — Công văn**: 2 cột trên (cơ quan trái / quốc hiệu-tiêu ngữ phải), số ký hiệu +
  "V/v ..." dưới cột trái, địa danh-ngày dưới cột phải, "Kính gửi:" + danh sách, nội dung tự
  do, khối dưới: "Nơi nhận" trái / quyền hạn-chức vụ-chữ ký-họ tên phải.
- **Mẫu 1.2 — Quyết định (quy định trực tiếp)**: cùng khối trên, tên loại "QUYẾT ĐỊNH" +
  trích yếu, "Căn cứ ...;" (nhiều dòng), "Theo đề nghị của ...", "QUYẾT ĐỊNH:", danh sách
  Điều 1/Điều 2/..., khối dưới giống Công văn.
- **Mẫu 1.4 — Văn bản có tên loại (generic)**: dùng chung cho chỉ thị/quy chế/quy định/
  thông báo/hướng dẫn/chương trình/kế hoạch/phương án/đề án/dự án/báo cáo/tờ trình — cùng
  khối trên, tên loại (từ `references/loai_van_ban_viet_tat.json`) + trích yếu, nội dung tự
  do (không bắt buộc chia Điều), khối dưới giống Công văn.

Chưa dựng (v0.2.0): **Mẫu 1.1 (Nghị quyết)**, **Mẫu 1.3 (Quyết định quy định gián tiếp)**,
**Mẫu 1.9 (Biên bản, layout 2 chữ ký ngang hàng khác hẳn)** — xem "Known limitations" trong
`SKILL.md`.

## Số, ký hiệu văn bản (Phụ lục I, Mục II.3) — cùng 2 quy ước `legal-citation-checker` đã dùng

- Văn bản có tên loại + năm (Nghị quyết/Quyết định/Chỉ thị/...): `<số>/<năm>/<viết-tắt-loại>-<viết-tắt-cơ-quan>`, ví dụ `12/2026/QĐ-UBND`.
- Công văn (không tên loại, không năm): `<số>/<viết-tắt-cơ-quan>-<viết-tắt-đơn-vị>`, ví dụ `45/SNV-VP`.

`scripts/render_nd30_document.py` reuses exactly this same 2-convention distinction
`legal-citation-checker`'s `validate_citation_format.py` already validates for citations —
same real numbering rule, applied here to the document being *authored* instead of *cited*.
