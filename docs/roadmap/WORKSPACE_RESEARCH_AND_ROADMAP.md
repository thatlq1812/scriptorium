# Scriptorium Workspace: Isolated Research & Roadmap

> [!IMPORTANT]
> **Tài liệu Cách ly Nghiên cứu & Định hướng Roadmap**: File này nằm trong `docs/roadmap/` đóng vai trò là tài liệu nghiên cứu độc lập cho khái niệm **Scriptorium Workspace** (GUI App & Local Workspace). Tài liệu này **không** can thiệp hay biến đổi mã nguồn các skill cốt lõi hiện có của Scriptorium.

---

## 1. Bối cảnh & Định hướng Tổng quan

Scriptorium đóng vai trò là nhà xưởng nghiên cứu, kiểm thử bảo mật và cataloging các **Agent Skills** chuẩn mở (`SKILL.md`). 

Tiếp nối nó, **Scriptorium Workspace** được định hình như một ứng dụng GUI trực quan dành cho người dùng phổ thông tại Việt Nam, vận hành dựa trên cơ chế **Local-First Workspace** (ví dụ `D:/my_workspace`), tự động hóa việc khởi tạo dự án và gọi các CLI Agent thực thi công việc dựa trên các gói Skill đặc chủng.

---

## 2. Nguyên tắc Kiến trúc & Quyết định Kỹ thuật (Key Directives)

### 2.1. Lựa chọn Công nghệ GUI: Reject Tauri $\rightarrow$ Khuyên dùng React / Web-First
* **Quyết định**: **Bác bỏ hoàn toàn Tauri (Rust)**.
* **Lý do**: Mặc dù Tauri nhẹ, việc kết hợp Rust với Python backend và xử lý IPC/Subprocess stream mang lại độ phức tạp cực kỳ lớn (High Friction), gây khó khăn trong việc bảo trì và tích hợp giao diện.
* **Hướng đi mới**: Sử dụng **React** (React.js / Next.js hoặc React + Electron Wrapper). Việc phát triển trên React giúp xây dựng UI linh hoạt, dễ dàng tích hợp các thư viện UI hiện đại, quản lý WebSocket/StdIO stream mượt mà với Python subprocess backend.

### 2.2. Đánh giá & Lựa chọn Worker CLI Agent: Cần Research Độc lập
* **Quyết định**: Không ấn định hay phán đoán trước bất kỳ Worker CLI Agent cụ thể nào (như Claude Code CLI, Codex CLI, Aider, OpenHands...).
* **Yêu cầu**: Cần tổ chức một đợt **Research & Benchmark riêng** để đánh giá các CLI Agent mã nguồn mở dựa trên các tiêu chí:
  1. Khả năng chạy ngầm (Headless execution stability).
  2. Khả năng stream kết quả StdIO/JSON mượt mà.
  3. Mức độ an toàn khi thao tác file local.
  4. Chi phí token & hiệu năng thực thi.

### 2.3. Cấu trúc Workspace Cá nhân (`D:/my_workspace`)
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
  * Khảo sát và so sánh các Open-Source CLI Agents hiện có.
  * Đánh giá cơ chế cô lập môi trường thực thi (Sandbox isolation) và khả năng xử lý Tiếng Việt.

- [ ] **Research Item 2: Thiết kế Kiến trúc React GUI & Python IPC Bridge**
  * Xây dựng sơ đồ kiến trúc giao tiếp giữa React GUI frontend và Python Orchestrator qua WebSocket / Local API.
  * Thiết kế giao diện Chat 2 chiều + Live Activity Stepper (thanh tiến trình trực quan).

- [ ] **Research Item 3: Đóng gói Session State & Context Budget**
  * Nghiên cứu cơ chế quản lý file `PROJECT_PLAN.md` và `STATE.json` trong thư mục dự án để khôi phục bối cảnh làm việc mà không làm phình dung lượng token.

- [ ] **Research Item 4: Tích hợp Elixverse AI API Routing Gateway**
  * Nghiên cứu giao thức kết nối API Routing, quản lý Spend Cap, Rate Limiting và hiển thị Token Metering trên GUI.

---

## 4. Phân định Ranh giới Dự án (System Boundaries)

1. **Scriptorium Core Repo (`elix/scriptorium`)**: Giữ nguyên triết lý 100% — Tập trung vào việc phát triển, kiểm toán an ninh, đánh giá chất lượng và xuất các artifact `SKILL.md`. Không chứa GUI app hay code backend cồng kềnh.
2. **Scriptorium Workspace Roadmap (`docs/roadmap/`)**: Nơi lưu trữ tài liệu nghiên cứu, ý tưởng kiến trúc và định hướng sản phẩm cho ứng dụng GUI tương lai.
