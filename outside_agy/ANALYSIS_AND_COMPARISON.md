# Phân Tích & Đối Chiếu Bộ Skill Pháp Lý `outside_agy/` Với Scriptorium

---

## 1. Tổng quan Bộ sưu tập `outside_agy/`

Bộ sưu tập `outside_agy/` đã thu thập và chuẩn hóa **6 Agent Skills** chia thành 2 cụm chính:

### Cụm Skill Việt Nam (Domestic):
1. [`vn-contract-review-playbook.md`](file:///d:/elix/scriptorium/outside_agy/skills/vn-contract-review-playbook.md): Rà soát hợp đồng thương mại/lao động, ẩn danh PII, bắt lỗi phạt vi phạm/đơn phương chấm dứt theo BLDS 2015, LTM 2005.
2. [`vn-mna-due-diligence.md`](file:///d:/elix/scriptorium/outside_agy/skills/vn-mna-due-diligence.md): Thẩm định pháp lý M&A, trích xuất dữ liệu VDR, soát rủi ro vốn, tài sản, hợp đồng tín dụng và Change of Control.
3. [`vn-legal-opinion-drafter.md`](file:///d:/elix/scriptorium/outside_agy/skills/vn-legal-opinion-drafter.md): Soạn thảo Ý kiến Pháp lý (Legal Opinion) 7 phần, đối chiếu căn cứ pháp lý và lập luận 2 chiều.

### Cụm Skill Quốc tế (International):
4. [`intl-litigation-brief-assistant.md`](file:///d:/elix/scriptorium/outside_agy/skills/intl-litigation-brief-assistant.md): Cảm hứng từ **CoCounsel / Casetext** — Phân tích hồ sơ tranh tụng, tóm tắt bản khai (deposition summaries), ánh xạ chứng cứ.
5. [`intl-clm-risk-triage.md`](file:///d:/elix/scriptorium/outside_agy/skills/intl-clm-risk-triage.md): Cảm hứng từ **Ironclad AI / Robin AI** — Phân loại hợp đồng in-house, rà soát hạn mức trách nhiệm (LoL), bồi thường (Indemnity), tracking nghĩa vụ sau ký.
6. [`intl-compliance-audit-framework.md`](file:///d:/elix/scriptorium/outside_agy/skills/intl-compliance-audit-framework.md): Cảm hứng từ **Harvey AI** — Kiểm tra tuân thủ đa quốc gia (GDPR, EU AI Act, Nghị định 13/2023/NĐ-CP bảo vệ dữ liệu cá nhân).

---

## 2. Phân Tích & Đối Chiếu Với Hệ Thống Scriptorium

Khi đặt các skill nổi bật của thị trường (`outside_agy/`) bên cạnh triết lý và kiến trúc hiện tại của `Scriptorium`, ta nhận thấy những điểm tương đồng và khác biệt chiến lược rất rõ ràng:

```mermaid
graph TD
    subgraph Market Skills ["Bộ Skill Thị Trường (outside_agy)"]
        M1[Playbook-driven Redlining]
        M2[Multi-document VDR Extraction]
        M3[Multi-jurisdictional Compliance Audit]
    end

    subgraph Scriptorium Core ["Kiến Trúc Scriptorium"]
        S1[Deterministic Mechanical Linter]
        S2[100% Grounded Source Validation]
        S3[Structural Completeness Check]
    end

    Market Skills <-->|Bổ sung & Nâng cấp| Scriptorium Core
```

### Bảng Đối Chiếu Chi Tiết

| Tiêu chí | Skill Thị trường (`outside_agy/`) | Scriptorium Hiện Tại (`skills/`) | Định hướng Tích hợp / Đóng góp |
| :--- | :--- | :--- | :--- |
| **Phạm vi nghiệp vụ** | Bao phủ diện rộng: M&A, In-house CLM, Tranh tụng (Litigation), Tuân thủ đa quốc gia. | Tập trung vào nền tảng cơ bản: Linter hợp đồng (`contract-consistency-linter`), Ý kiến pháp lý (`legal-research-brief`), Nhật ký rủi ro (`contract-risk-log`). | `outside_agy` giúp **mở rộng quy mô ứng dụng** của Scriptorium sang các bài toán phức tạp hơn như M&A và CLM. |
| **Cơ chế Kiểm soát Lỗi** | Dựa trên Prompting Playbook & LLM RAG (CoCounsel/Harvey). | **Tách biệt triệt để:** Dùng Python stdlib/regex cho kiểm tra cơ học; bắt lỗi cứng khi trích dẫn sai `source_id`. | Áp dụng cơ chế **Linter cơ học của Scriptorium** làm "màng lọc cứng" trước khi chuyển cho LLM xử lý Playbook của `outside_agy`. |
| **Bảo mật & PII** | Yêu cầu tích hợp tính năng Anonymization trong workflow. | Đã có nền tảng `security-audit` và nguyên tắc local-only. | Bổ sung skill chuyên biệt `vn-contract-anonymizer` để tự động hóa khâu ẩn danh dữ liệu trước khi gửi prompt. |
| **Theo dõi nghĩa vụ sau ký** | Rất mạnh ở mảng In-house CLM (Ironclad model): Đặt lịch cảnh báo renewal, SLA. | Chưa có skill tương đương. | Có thể phát triển skill `contract-obligation-tracker` dựa trên mô hình của `intl-clm-risk-triage`. |

---

## 3. Đề Xuất Hướng Phát Triển Cho Scriptorium

Dựa trên việc phân tích các skill nổi bật thu thập được, Scriptorium có thể nâng cấp hệ thống Legal Skills theo 3 bước:

1.  **Kết hợp "Nhiệt" và "Lạnh" (LLM + Deterministic Linter):**
    *   Sử dụng **Linter "lạnh" (Deterministic)** của Scriptorium để quét các lỗi số điều, lỗi trích dẫn chéo, kiểm tra `source_id`.
    *   Sử dụng **LLM "nhiệt" (Semantic/Playbook)** từ mẫu của `outside_agy` để đánh giá rủi ro ngữ nghĩa (ví dụ: so sánh điều khoản LoL với Playbook của công ty).
2.  **Xây dựng bộ thư viện Playbook tiếng Việt chuẩn hóa:**
    *   Học tập mô hình Playbook của Ironclad/Robin AI để tạo ra các tập tin cấu hình Playbook dạng JSON cho thị trường Việt Nam (Hợp đồng thương mại, Hợp đồng lao động, Hợp đồng M&A).
3.  **Mở rộng sang M&A và Tuân thủ dữ liệu (Decree 13 / GDPR):**
    *   Bổ sung cụm skill thẩm định VDR và kiểm tra tuân thủ Nghị định 13/2023/NĐ-CP — đây là nhu cầu cực kỳ lớn của các doanh nghiệp và văn phòng luật tại Việt Nam hiện nay.
