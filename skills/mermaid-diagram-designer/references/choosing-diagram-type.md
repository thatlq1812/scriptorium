# Chọn loại diagram theo tình huống

| Tình huống mô tả | Loại diagram | Vì sao |
| --- | --- | --- |
| "làm A rồi tới B, nếu X thì rẽ nhánh" | `flowchart` | Biểu diễn quyết định/rẽ nhánh trực quan nhất |
| "hệ thống A gọi hệ thống B, B trả lời, có thứ tự thời gian" | `sequenceDiagram` | Duy nhất trong Mermaid thể hiện được trục thời gian giữa nhiều actor |
| "class/entity này kế thừa/chứa class kia" | `classDiagram` | Ký hiệu UML chuẩn cho quan hệ kế thừa/composition |
| "đối tượng chuyển từ trạng thái này sang trạng thái khác khi có sự kiện" | `stateDiagram-v2` | Không dùng flowchart để giả lập state machine — thiếu ngữ nghĩa transition/event |
| "bảng A liên kết bảng B theo tỷ lệ 1-nhiều" | `erDiagram` | Ký hiệu quan hệ CSDL chuẩn (crow's foot) |
| "việc này kéo dài từ ngày X tới Y, phụ thuộc việc trước" | `gantt` | Duy nhất có trục thời gian lịch thật |
| "tỷ lệ phần trăm giữa vài nhóm" | `pie` | Đơn giản, đủ dùng cho 3-6 lát cắt; nhiều hơn thì khó đọc, cân nhắc bar chart ở công cụ khác |
| "trải nghiệm người dùng qua các bước, có mức độ hài lòng" | `journey` | Có trục cảm xúc (điểm số) tích hợp sẵn, flowchart không có |
| "ý tưởng phân nhánh không có thứ tự/thời gian cố định" | `mindmap` | Cấu trúc cây tự do, không ép vào luồng tuyến tính |
| "chuỗi sự kiện theo mốc thời gian nhưng không phải task có duration" | `timeline` | Nhẹ hơn gantt, không cần ngày bắt đầu/kết thúc chính xác |

## Quy tắc quyết định nhanh

1. Có trục **thời gian thật** (ngày tháng cụ thể, duration) → `gantt` hoặc `timeline`.
2. Có **nhiều actor tương tác qua lại** → `sequenceDiagram`.
3. Có **trạng thái + sự kiện chuyển trạng thái** (không phải chỉ bước tuần tự) → `stateDiagram-v2`.
4. Có **cấu trúc dữ liệu/class quan hệ tĩnh** (không phải luồng xử lý) → `classDiagram` hoặc `erDiagram`.
5. Còn lại, mặc định `flowchart` — linh hoạt nhất, dùng được cho hầu hết quy trình/quyết định.

Khi không chắc, hỏi lại người dùng muốn nhấn mạnh khía cạnh nào (thứ tự thời gian? trạng thái? quan hệ dữ liệu?) thay vì đoán — chọn sai loại diagram làm người đọc hiểu sai bản chất hệ thống, không chỉ là vấn đề thẩm mỹ.
