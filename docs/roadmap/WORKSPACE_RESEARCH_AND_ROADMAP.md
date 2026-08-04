# Scriptorium Workspace: Isolated Research & Roadmap

> [!IMPORTANT]
> **Tài liệu Cách ly Nghiên cứu & Định hướng Roadmap**: File này nằm trong `docs/roadmap/` đóng vai trò là tài liệu nghiên cứu độc lập cho khái niệm **Scriptorium Workspace** (GUI App & Local Workspace). Tài liệu này **không** can thiệp hay biến đổi mã nguồn các skill cốt lõi hiện có của Scriptorium.

---

## 1. Bối cảnh & Lý do Chiến lược (Market Insights & Opportunities)

Scriptorium đóng vai trò là nhà xưởng nghiên cứu, kiểm thử bảo mật và cataloging các **Agent Skills** chuẩn mở (`SKILL.md`). 

Tiếp nối nó, **Scriptorium Workspace** được định hình là ván cược chiến lược (Strategic Bet) giải quyết trực tiếp các điểm nghẽn của thị trường Việt Nam:
1. **Thói quen tiêu dùng PAYG (Pay-As-You-Go)**: Người dùng Việt Nam ít khi dùng hết hạn mức $20/tháng của các gói cố định (ChatGPT Plus / Claude Pro), họ quen và thích cơ chế trả tiền theo mức độ sử dụng thực tế (PAYG).
2. **Rào cản BYOK (Bring Your Own Key)**: Hầu hết ứng dụng PAYG hiện nay đều bắt người dùng "Bring Your Own Key" (phải tự có thẻ VISA/Mastercard nạp vào OpenAI/Anthropic), tạo rào cản rất lớn cho người dùng phổ thông.
3. **Lợi thế của Elixverse AI Provider Router (`https://api.elixverse.com/api/v1`)**:
   * Elixverse đóng vai trò là API Router chuẩn hóa (`POST /chat/completions`, `POST /images/generations`...) điều phối đa nhà cung cấp (Gemini, Anthropic, OpenAI, DeepSeek...), tự động tính phí linh hoạt (Dynamic Pricing) và quản lý ví nạp tiền nội địa.
   * Tham chiếu hợp đồng API: `D:\elix\platform\docs\API_REFERENCE.md`.
   * Giải quyết triệt để rào cản BYOK cho người dùng cuối: Người dùng không cần tự cấp thẻ quốc tế hay lấy API key từ các LLM vendor.
4. **Sức mạnh từ Bộ Skill Đã Chuẩn Hóa**: Kết hợp với bộ Skill đặc chủng của Scriptorium giúp Agent làm việc chính xác, chuẩn nghiệp vụ Việt Nam, tiết kiệm 70-90% token và đạt hiệu quả công việc tối đa.

---

## 2. Nguyên tắc Kiến trúc & Triết lý UX (Minimalist IDE & Open Intent)

### 2.1. Triết lý Giao diện Tối giản (Minimalist IDE Layout)
* **Bố cục Minimalist IDE**: Phân chia dạng `Folders` (Cây thư mục bên trái) | `Editor / Reviewer / Chat` (Màn hình chính bên phải), tương tự như VS Code nhưng được đơn giản hóa tối đa cho người dùng phổ thông.
* **Không khóa cứng tác vụ (Loại bỏ vết xe đổ EduStation)**: 
  * Không bắt người dùng chọn các nút bấm cứng như "Tạo hợp đồng" hay "Soạn bài giảng KHBD 5512" (việc khóa cứng mục tiêu làm hệ thống trở nên yếu và cứng nhắc).
  * **Mô hình Chat Phi Lập trình (Open Intent Chat)**: Người dùng chỉ gõ 1 dòng chat tự nhiên (ví dụ: *"Hãy hỗ trợ tôi tạo một báo tường"* hay *"Xem giúp tôi tài liệu này"*). Ưu tiên hàng đầu là tự động thiết lập dự án mới hoặc load dự án cũ.
  * **Agent Trung Gian tự chủ (Autonomous Orchestrator)**: Tự hiểu ý định của người dùng, tự tạo project mới hoặc load project cũ, tự tìm Skill phù hợp trong `skills/`, và tự động thực thi tới khi ra sản phẩm hoàn chỉnh nhất trong khả năng của hệ thống (chạy liên tục cho tới khi ra kết quả, không gượng ép dừng lại từng bước nhỏ).

### 2.2. Lựa chọn Công nghệ GUI: Reject Tauri $\rightarrow$ Khuyên dùng React / Web-First
* **Quyết định**: **Bác bỏ hoàn toàn Tauri (Rust)**.
* **Lý do**: Mặc dù Tauri nhẹ, việc kết hợp Rust với Python backend và xử lý IPC/Subprocess stream mang lại độ phức tạp cực kỳ lớn (High Friction), gây khó khăn trong việc bảo trì và tích hợp giao diện.
* **Hướng đi mới**: Sử dụng **React** (React.js / Next.js hoặc React + Electron Wrapper). Việc phát triển trên React giúp xây dựng UI linh hoạt, dễ dàng tích hợp các thư viện UI hiện đại, quản lý WebSocket/StdIO stream mượt mà với Python subprocess backend.

### 2.3. Đánh giá & Lựa chọn Worker CLI Agent: Cần Research Độc lập
* **Quyết định**: Không ấn định hay phán đoán trước bất kỳ Worker CLI Agent cụ thể nào (như Claude Code CLI, Codex CLI, Aider, OpenHands...).
* **Yêu cầu**: Cần tổ chức một đợt **Research & Benchmark riêng** để đánh giá các CLI Agent mã nguồn mở dựa trên các tiêu chí:
  1. Khả năng chạy ngầm (Headless execution stability).
  2. Khả năng stream kết quả StdIO/JSON mượt mà.
  3. Mức độ an toàn khi thao tác file local.
  4. Chi phí token & hiệu năng thực thi.

### 2.4. Cấu trúc Workspace Cá nhân (`D:/my_workspace`)
Workspace là thư mục cá nhân local của người dùng, nơi dữ liệu được lưu trữ an toàn và các Agent đối chiếu thông tin:
```
D:/my_workspace/
├── personals/              # Hồ sơ cá nhân (user_profile.json, org_profile.json)
├── data/                   # Tài sản doanh nghiệp (mẫu Slide PPTX, mẫu Word, bảng màu)
├── documents/              # Kho tài liệu tham khảo dài hạn
├── skills/                 # Thư mục lưu trữ các gói Skill xuất từ Scriptorium
├── registry/               # Registry local cho các skill
└── projects/               # Nơi lưu trữ dự án theo phiên làm việc (yyyyMMdd-hhmmss-{name})
    └── _template/          # Thư mục mẫu mặc định để khởi tạo dự án
```

---

## 3. Danh mục Nghiên cứu (Research Backlog)

- [ ] **Research Item 1: Survey & Benchmark Worker CLI Agents**
  * Khảo sát và so sánh các Open-Source CLI Agents hiện có (OpenHands, Aider, Goose, OpenCode/Hermes).
  * Đánh giá cơ chế cô lập môi trường thực thi (Sandbox isolation) và khả năng xử lý Tiếng Việt UTF-8 trên Windows (`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, `chcp 65001`).

- [ ] **Research Item 2: Thiết kế Kiến trúc React Minimalist IDE GUI & Local API Bridge**
  * Xây dựng sơ đồ kiến trúc giao tiếp giữa React GUI frontend (`Folders | Editor / Reviewer / Chat`) và Python Orchestrator qua WebSocket / Local API (`127.0.0.1:8765`).
  * Tích hợp giao thức stream NDJSON (`agent_thought`, `tool_call_start`, `tool_call_end`, `file_mutation`, `token_usage`).

- [ ] **Research Item 3: Đóng gói Session State & Context Budget**
  * Tối ưu cơ chế đọc/ghi `PROJECT_PLAN.md` và `STATE.json` trong thư mục dự án để khôi phục bối cảnh làm việc mà không làm phình dung lượng token (cắt giảm 70-90% token dư thừa).

- [ ] **Research Item 4: Tích hợp Elixverse AI API Routing Gateway (PAYG & Zero-BYOK)**
  * Nghiên cứu giao thức kết nối API Routing theo chuẩn `D:\elix\platform\docs\API_REFERENCE.md`.
  * Quản lý Spend Cap, Rate Limiting, Dynamic Pricing và hiển thị Token Metering trên GUI.

---

## 4. Tài liệu Tham chiếu Nội bộ trong Thư mục Cách ly

- **Đặc tả Kỹ thuật Triển khai cho AI Agent**: [PRAXIS_BLUEPRINT_SPEC.md](file:///D:/elix/scriptorium/docs/roadmap/PRAXIS_BLUEPRINT_SPEC.md) (Chứa 15 quy tắc R-rules, cấu trúc React+FastAPI+pywebview, NDJSON protocol & quy trình xây dựng).
- Báo cáo chi tiết: [Scriptorium Workspace Research Roadmap (1).md](file:///D:/elix/scriptorium/docs/roadmap/researches/Scriptorium%20Workspace%20Research%20Roadmap%20%281%29.md)
- Báo cáo kiến trúc tổng quan: [Scriptorium Workspace Research Roadmap.md](file:///D:/elix/scriptorium/docs/roadmap/researches/Scriptorium%20Workspace%20Research%20Roadmap.md)
- Tham chiếu API Elixverse: [API_REFERENCE.md](file:///D:/elix/platform/docs/API_REFERENCE.md)
- Ghi chú định hướng dự án: [PROJECT.md](file:///D:/elix/scriptorium/PROJECT.md)

---

## 5. Phân định Ranh giới Dự án (System Boundaries)

1. **Scriptorium Core Repo (`elix/scriptorium`)**: Giữ nguyên triết lý 100% — Tập trung vào việc phát triển, kiểm toán an ninh, đánh giá chất lượng và xuất các artifact `SKILL.md`. Không chứa GUI app hay code backend cồng kềnh.
2. **Scriptorium Workspace Roadmap (`docs/roadmap/`)**: Nơi lưu trữ tài liệu nghiên cứu, ý tưởng kiến trúc và định hướng sản phẩm cho ứng dụng GUI tương lai.
