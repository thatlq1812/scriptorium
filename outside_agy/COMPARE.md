# Phân Tích & So Sánh: Trải Nghiệm Làm Việc Của Luật Sư Tại Workspace Scriptorium
*(Giai đoạn Giả định / Tưởng tượng ban đầu vs. Thực tế sau khi khảo sát thư mục `skills/`)*

---

## I. GIAI ĐOẠN 1: TƯỞNG TƯỢNG BAN ĐẦU (Trước khi xem thư mục `skills/`)

Trước khi trực tiếp duyệt thư mục `skills/`, dựa trên tên dự án `Scriptorium` (nơi chuyên biên soạn/xây dựng tri thức và công cụ cho AI), ta hình dung trải nghiệm làm việc của một **Luật sư (Legal Practitioner)** hợp tác cùng AI trong workspace này như sau:

### 1. Góc nhìn & Kỳ vọng ban đầu của Luật sư
Luật sư thường tiếp cận AI như một **"Trợ lý Pháp lý Toàn năng" (Legal Copilot / Virtual Associate)** với mong muốn tự động hóa tối đa công việc:
*   **Phân tích & Tự động phát hiện rủi ro:** Kỳ vọng AI tự đọc hợp đồng 50 trang, tự chỉ ra điều khoản nào bất lợi (vd: mức phạt vi phạm quá cao, điều khoản miễn trừ trách nhiệm vô lý).
*   **Tra cứu & Cập nhật luật:** Kỳ vọng AI tự tìm kiếm văn bản quy phạm pháp luật Việt Nam (Luật, Nghị định, Thông tư), tự biết văn bản nào còn hiệu lực, tự đối chiếu án lệ và đề xuất hướng giải quyết case.
*   **Tự động soạn thảo & Điền biểu mẫu:** Kỳ vọng AI tự viết dự thảo hợp đồng, tự điền hồ sơ doanh nghiệp/thẩm định pháp lý (due diligence report).
*   **Tóm tắt & Tư vấn:** Kỳ vọng AI đọc tài liệu do khách hàng gửi, tóm tắt nhanh và tự đề xuất lập luận pháp lý cho luật sư.

### 2. Mô hình tương tác tưởng tượng
*   Luật sư nhập prompt: *"Hãy rà soát hợp đồng mua bán này và cho tôi biết có rủi ro gì không, trích dẫn luật liên quan."*
*   AI xử lý (sử dụng LLM) và trả về một bản nhận xét hoàn chỉnh kèm các điều luật mà AI nghĩ là phù hợp.
*   Luật sư kiểm tra lại và gửi cho khách hàng.

---

## II. GIAI ĐOẠN 2: KHẢO SÁT THỰC TẾ THƯ MỤC `skills/` & TRIẾT LÝ SCRIPTORIUM

Sau khi mở thư mục `skills/` và đối chiếu với các nghiên cứu thực tế (`outside_research/research_01_survey.md` & `research_01_result_01.md`), bức tranh thực tế hoàn toàn khác biệt — sâu sắc hơn, kỷ luật hơn và bám sát thực tiễn ngành luật.

### 1. Kiến trúc thực tế của cụm Legal Skills trong Scriptorium
Trong số 31 skills hiện có, cụm công cụ dành cho Luật sư được thiết kế cực kỳ định hình:

1.  **`contract-consistency-linter` (Trợ lý kiểm lỗi cơ học hợp đồng):**
    *   *Nhiệm vụ:* Không hề đánh giá hợp đồng "tốt hay xấu", mà linter 3 lỗi cơ học cực kỳ hay gặp do con người copy-paste:
        1. Đánh số Điều (Điều 1, 2, 3...) có bị nhảy số, trùng số hoặc đứt đoạn không.
        2. Trích dẫn nội bộ (vd: *"theo quy định tại Điều 5"*) xem Điều 5 có thực sự tồn tại trong hợp đồng không.
        3. Nhất quán danh xưng (vd: Hợp đồng khai báo Bên A & Bên B, nhưng ở Điều 8 lỡ copy từ template cũ còn sót chữ *"Bên C"*).
    *   *Đặc điểm:* Chạy hoàn toàn bằng Python stdlib/regex, local-only, zero network, zero LLM hallucination.

2.  **`legal-research-brief` (Trợ lý cấu trúc bản ý kiến pháp lý):**
    *   *Nhiệm vụ:* Kiểm tra cấu trúc 7 phần của Ý kiến pháp lý (Câu hỏi, Sự kiện đã xác minh, Thiếu sót/Giả định, Căn cứ pháp lý, Phân tích áp dụng, Quan điểm trái chiều, Đánh giá rủi ro).
    *   *Nguyên tắc sinh tử:* **Bắt buộc 100% khẳng định thực tế và căn cứ pháp lý phải có `source_id` trích dẫn từ nguồn do Luật sư/Người dùng cung cấp trước.** Nếu trích dẫn một `source_id` không tồn tại -> Lỗi cứng (Exit Code 1).

3.  **`contract-risk-log` (Nhật ký rủi ro hợp đồng chuẩn hóa):**
    *   *Nhiệm vụ:* Kiểm tra tính đầy đủ của bản Log rủi ro do Luật sư/Agent lập. Bắt buộc mọi rủi ro phải có: vị trí điều khoản, mối quan ngại, mức độ nghiêm trọng (`low`/`medium`/`high`), và đề xuất hành động cụ thể.
    *   *Điểm đặc biệt:* Bắt buộc tuyên bố rõ ràng: *"Đã rà soát và xác nhận KHÔNG có rủi ro nào"* chứ không được để danh sách rỗng mập mờ (nhằm tránh việc bỏ sót rà soát).

4.  **`legal-citation-checker` & `legal-form-filler` (Các khoảng trống được thừa nhận - Open Gaps):**
    *   *Thực tế:* Dự án gắn nhãn rõ ràng là hoãn/chưa làm vì hiện tại Việt Nam chưa có API miễn phí công khai để tra cứu hiệu lực văn bản luật (khác với bài báo khoa học có CrossRef). Scriptorium kiên quyết **KHÔNG bịa dữ liệu giả** hay dùng LLM đoán mò hiệu lực luật.

---

## III. BẢNG SO SÁNH CHI TIẾT: GIẢ ĐỊNH VS. THỰC TẾ

| Tiêu chí | Tưởng tượng ban đầu (Giả định) | Thực tế trong Scriptorium (`skills/`) |
| :--- | :--- | :--- |
| **Vai trò của AI** | Thay thế phán đoán của Luật sư (Phán đoán điều khoản rủi ro, tự tư vấn). | Làm **"Khung giàn giáo" (Scaffolding) & Linter kiểm lỗi cơ học/cấu trúc**. Giữ nguyên vai trò phán đoán cho Luật sư. |
| **Thái độ với Ảo giác (Hallucination)** | Tin tưởng LLM sẽ tự trích dẫn đúng luật. | **Tuyệt đối không tin LLM bịa luật**. Ép buộc quy tắc: *"Dựa theo nguồn 100%, không tự generate thông tin mới"*. Trích dẫn sai `source_id` = Báo lỗi ngay lập tức. |
| **Rà soát hợp đồng** | AI đọc và tự nghĩ ra rủi ro. | `contract-consistency-linter` bắt lỗi số điều, lỗi trích dẫn chéo, lỗi lộ tên Bên C. `contract-risk-log` kiểm tra xem nhật ký rủi ro có ghi chép đủ & rõ ràng không. |
| **Công nghệ & Cơ chế chạy** | Gọi API LLM phức tạp, tốn kém, phụ thuộc prompt. | Thuần Python stdlib (regex, json), chạy local, **zero network calls**, tốc độ cực nhanh, deterministic (kết quả 100% nhất quán). |
| **Nguồn gốc quy trình** | Tự thiết kế theo cảm tính kỹ sư công nghệ. | Chiết xuất trực tiếp từ khảo sát thực tế luật sư Việt Nam (`outside_research/research_01_survey.md`). |
| **Xử lý khi thiếu dữ liệu** | Cho AI tự search web hoặc "chế" câu trả lời. | Thừa nhận thẳng thắn "Open Gaps" (như `legal-citation-checker`) và dừng lại cho tới khi có nguồn dữ liệu chuẩn xác. |

---

## IV. BÀI HỌC VÀ NHẬN XÉT KẾT LUẬN

### 1. Tại sao cách làm của Scriptorium lại ưu việt đối với ngành Luật?
Trong thực tế hành nghề luật, một sai sót nhỏ như:
*   Trích dẫn một án lệ hoặc điều luật không tồn tại (như vụ phạt Rule 11 nổi tiếng *Mata v. Avianca* ở Mỹ khi luật sư dùng ChatGPT bịa án lệ).
*   Nhầm lẫn tên Bên A thành Bên C do copy-paste mẫu hợp đồng cũ.
*   Viện dẫn nhầm Điều 15 trong khi hợp đồng chỉ có 12 Điều.

Những lỗi này nguy hiểm hơn nhiều so với việc không có AI. Scriptorium đã nhận diện chính xác nghiên cứu của **Stanford RegLab/HAI** (ngay cả công cụ luật chuyên dụng như Lexis+ AI vẫn bịa thông tin ~17%, Westlaw AI ~33%).

Do đó, thay vì biến AI thành một "Chuyên gia chém gió", Scriptorium biến AI thành một **"Kiểm soát viên Kỷ luật" (Disciplined Auditor)**:
1.  **Luật sư vẫn là người giữ vai trò chuyên môn:** Luật sư cung cấp văn bản nguồn, đưa ra phán đoán rủi ro thực sự.
2.  **AI đảm bảo tính chính xác cơ học 100%:** AI kiểm tra từng con số, từng trích dẫn nguồn, từng khung cấu trúc báo cáo.

### 2. Bức tranh Luật sư làm việc tại Workspace Scriptorium
Khi làm việc tại đây, Luật sư không phải ngồi tự viết code, mà:
*   **Đóng góp tri thức (Elicitation):** Cung cấp các checklist, quy trình rà soát thực tế cho team kỹ sư.
*   **Đồng xây dựng Skills (`skill-creator`):** Đóng góp các mẫu brief, tiêu chí rủi ro chuẩn hóa.
*   **Yên tâm tuyệt đối về Output:** Nhờ có hệ thống linter cơ học và kiểm tra grounding bắt buộc, văn bản xuất ra gửi cho khách hàng luôn đạt chuẩn cao nhất về tính chính xác và an toàn pháp lý.
