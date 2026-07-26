# Thư viện Skill Pháp Lý Dành Cho Luật Sư (Việt Nam & Quốc Tế)
*Thư mục: `outside_agy/`*

---

## 📌 Giới thiệu & Mục đích
Thư mục `outside_agy/` được khởi tạo nhằm thu thập, tổng hợp và chuẩn hóa các **Agent Skills**, **Workflows**, và **Playbooks** nổi bật dành cho Luật sư tại Việt Nam và Quốc tế (dựa trên các mô hình LegalTech hàng đầu như CoCounsel, Harvey AI, Ironclad, Robin AI, cũng như thực tiễn tư vấn pháp lý tại Việt Nam).

Các skill này được biên soạn dưới dạng chuẩn **Agent Skill Specification** để dễ dàng phân tích, đối chiếu với triết lý của dự án `Scriptorium` (nơi nhấn mạnh tính *Grounding 100%*, *Deterministic*, và *Human-in-the-Loop*).

---

## 🗂 Danh sách các Skill được thu thập

### 1. Cụm Skill Pháp Lý Việt Nam (Domestic Legal Skills)

| File Skill | Tên Skill | Phạm vi & Ứng dụng chính |
| :--- | :--- | :--- |
| [`vn-contract-review-playbook.md`](file:///d:/elix/scriptorium/outside_agy/skills/vn-contract-review-playbook.md) | **VN Contract Review & Redlining Playbook** | Rà soát hợp đồng thương mại, dịch vụ, lao động theo Bộ luật Dân sự 2015, Luật Thương mại 2005. Bắt lỗi điều khoản bất lợi, đề xuất sửa đổi và ẩn danh hóa PII. |
| [`vn-mna-due-diligence.md`](file:///d:/elix/scriptorium/outside_agy/skills/vn-mna-due-diligence.md) | **VN M&A Legal Due Diligence** | Thẩm định pháp lý M&A, trích xuất dữ liệu phòng dữ liệu ảo (VDR), quét rủi ro chuyển nhượng cổ phần/vốn góp, giấy phép và tài sản. |
| [`vn-legal-opinion-drafter.md`](file:///d:/elix/scriptorium/outside_agy/skills/vn-legal-opinion-drafter.md) | **VN Legal Opinion & Research Drafter** | Xây dựng bản ý kiến pháp lý (Legal Brief/Opinion), tổng hợp căn cứ pháp lý, lập luận 2 chiều và kiểm chứng hiệu lực văn bản. |

---

### 2. Cụm Skill Pháp Lý Quốc Tế (International Legal Skills)

| File Skill | Tên Skill | Phạm vi & Mô hình lấy cảm hứng |
| :--- | :--- | :--- |
| [`intl-litigation-brief-assistant.md`](file:///d:/elix/scriptorium/outside_agy/skills/intl-litigation-brief-assistant.md) | **Litigation Discovery & Case Briefing** | Cảm hứng từ **CoCounsel / Casetext**. Phân tích hồ sơ tranh tụng, tóm tắt lời khai (deposition summaries), trích xuất chứng cứ và lập dàn ý tranh tụng. |
| [`intl-clm-risk-triage.md`](file:///d:/elix/scriptorium/outside_agy/skills/intl-clm-risk-triage.md) | **CLM Contract Risk Triage & Obligation Tracking** | Cảm hứng từ **Ironclad AI & Robin AI**. Phân loại hợp đồng in-house, rà soát hạn mức trách nhiệm (Liability Cap), bồi thường (Indemnity) và theo dõi nghĩa vụ sau ký. |
| [`intl-compliance-audit-framework.md`](file:///d:/elix/scriptorium/outside_agy/skills/intl-compliance-audit-framework.md) | **Regulatory Compliance & Privacy Audit** | Cảm hứng từ **Harvey AI / Enterprise Audit**. Kiểm tra tuân thủ đa quốc gia (GDPR, EU AI Act, ESG, bảo vệ dữ liệu cá nhân Nghị định 13/2023/NĐ-CP). |

---

## 🔍 So sánh Nhanh: Xu Hướng Thế Giới vs. Triết Lý Scriptorium

*   **Xu hướng thế giới (Harvey, CoCounsel, Ironclad):** Tập trung vào **Context Integration** (kết nối trực tiếp Westlaw/Lexis), **Playbook-driven Redlining** (sửa hợp đồng tự động theo quy tắc doanh nghiệp), và **Multi-document Analysis** (quét hàng nghìn file VDR).
*   **Điểm tương đồng với Scriptorium:** Đều lấy **Human-in-the-Loop** làm trung tâm — AI đóng vai trò như Luật sư tập sự (Junior Associate), Luật sư chính (Partner) bắt buộc phải kiểm duyệt.
*   **Khác biệt độc đáo của Scriptorium:** Scriptorium tách biệt triệt để giữa **Linter cơ học (chạy regex local, 0% ảo giác)** và **LLM Analysis (xử lý ngữ nghĩa)**, tạo ra độ tin cậy tuyệt đối mà các hệ thống thuần LLM khó đạt được.
