# **Scriptorium Workspace: Báo Cáo Nghiên Cứu Chuyên Sâu (Deep Research) Kiến Trúc & Lộ Trình Phát Triển**

## **1\. Tổng Quan Kiến Trúc & Nguyên Tắc Tách Biệt Hệ Thống**

Dự án Scriptorium được xây dựng dựa trên sự phân định ranh giới chức năng hoàn toàn khép kín giữa hai thành phần1:

> 1. **Scriptorium Core (elix/scriptorium)**: Đóng vai trò là nhà xưởng nghiên cứu, kiểm thử an ninh, đánh giá chất lượng và cataloging các gói Agent Skills chuẩn mở (SKILL.md)1. Core hoàn toàn không chứa ứng dụng GUI, không chứa backend cồng kềnh, và 100% không tích hợp bất kỳ AI API backend nào1. Mọi artifact skill do Core xuất bản được vận hành bởi mô hình/backend riêng của từng Agent tiêu thụ (consuming agent)2.  
> 2. **Scriptorium Workspace (docs/roadmap/)**: Đóng vai trò là tài liệu nghiên cứu định hướng cho ứng dụng giao diện trực quan (GUI App) dành cho người dùng phổ thông tại Việt Nam1. Workspace vận hành theo cơ chế **Local-First Workspace** (tại thư mục cục bộ D:/my\_workspace), tự động hóa việc khởi tạo dự án, quản lý hồ sơ cá nhân và điều phối các Worker CLI Agent thực thi công việc1.

### **Tái Khẳng Định Quyết Định Kiến Trúc GUI: React / Web-First**

Dự án **bác bỏ hoàn toàn việc sử dụng Tauri (Rust)** cho phần giao diện Workspace1. Mặc dù Tauri nhẹ, việc kết hợp giữa Rust, Python Backend và việc truyền nhận luồng tiến trình con (subprocess stream) tạo ra độ phức tạp cực kỳ lớn (High Friction) trong giao tiếp IPC và bảo trì mã nguồn1.  
Hướng đi chính thức là sử dụng **React (React.js / Next.js hoặc React \+ Electron Wrapper)** kết hợp với Python Subprocess Backend qua giao thức WebSocket cục bộ1. Giải pháp này tối ưu hóa việc quản lý luồng dữ liệu hai chiều thời gian thực, xây dựng giao diện tương tác linh hoạt và hiển thị tiến trình công việc trực quan1.

### **Cấu Trúc Thư Mục Workspace Cục Bộ (D:/my\_workspace)**

Mọi dữ liệu cá nhân, tài sản doanh nghiệp và các dự án làm việc của người dùng được tổ chức an toàn tại máy Cục bộ1:

* personals/: Hồ sơ cá nhân và tổ chức (user\_profile.json, org\_profile.json)1.  
* data/: Tài sản thiết kế doanh nghiệp (tệp mẫu PPTX, Word, bảng màu nhận diện)1.  
* documents/: Kho tài liệu tham khảo dài hạn1.  
* skills/: Nơi lưu trữ các gói Skill xuất ra từ Scriptorium1.  
* registry/: Registry quản lý danh mục skill cài đặt cục bộ1.  
* projects/: Thư mục lưu trữ dự án theo từng phiên làm việc (yyyyMMdd-hhmmss-{name}), chứa tệp mẫu mặc định \_template/1.

## **2\. Research Item 1: Khảo Sát & Benchmark Worker CLI Agents Mã Nguồn Mở**

Khảo sát chuyên sâu các công cụ CLI Agent mã nguồn mở hàng đầu nhằm lựa chọn và đóng gói động cơ thực thi ngầm (Headless Worker) cho Scriptorium Workspace1.

### **2.1. Phân Tích & So Sánh Các Mã Nguồn CLI Agent Hàng Đầu**

Các dòng CLI Agent mã nguồn mở phổ biến hiện nay bao gồm:

* **OpenHands (tiền thân là OpenDevin)**: Nền tảng agent lập trình đám mây và cục bộ có cộng đồng lớn3. Hỗ trợ chế độ chạy ngầm (openhands \--headless \-t "task"), tích hợp sẵn môi trường Docker Sandbox cô lập tuyệt đối mã nguồn3. Hỗ trợ Model Context Protocol (MCP) và kiến trúc Subagent xử lý song song6.  
* **Aider**: Công cụ CLI chuyên biệt cho môi trường terminal, vận hành dựa trên cơ chế Git-native3. Mọi thay đổi mã nguồn do AI tạo ra đều được tự động đóng gói thành từng Git commit riêng biệt, cho phép khôi phục (/undo) tức thì5. Cung cấp cờ \--yes / \--no-auto-commits để chạy ở chế độ không tương tác5.  
* **Goose**: AI Agent tổng hợp do Agentic AI Foundation (thuộc Linux Foundation) quản lý, viết bằng Rust cho hiệu năng và độ ổn định cao7. Tích hợp sâu chuẩn MCP với hơn 70 extensions, hỗ trợ định dạng "Recipes" (file YAML cấu hình quy trình làm việc) và tích hợp sẵn cơ chế Sandbox / Adversary Reviewer để chặn prompt injection7.  
* **OpenCode / Claw Code / Hermes**: Các công cụ CLI siêu nhẹ tối ưu cho terminal, hỗ trợ đa nhà cung cấp mô hình (trên 75 providers) và tích hợp LSP (Language Server Protocol)4.

### **2.2. Ma Trận Đánh Giá Benchmark Theo 4 Tiêu Chí Cốt Lõi**

| Tiêu chí đánh giá | OpenHands | Aider | Goose | OpenCode / Hermes |
| :---- | :---- | :---- | :---- | :---- |
| **1\. Khả năng chạy ngầm (Headless)** | Rất mạnh (--headless), chế độ auto-approve hoàn toàn3. | Tốt (--yes), phù hợp cho script tự động3. | Rất tốt (CLI native & Recipe execution)7. | Khá, phụ thuộc vào TUI wrapper4. |
| **2\. Stream StdIO / JSON** | Xuất dạng JSON-lines / Event SDK chi tiết5. | Xuất dạng Plain text StdIO \+ Git diffs3. | Stream JSON sự kiện thời gian thực7. | Stream StdIO tiêu chuẩn4. |
| **3\. An toàn Sandbox & File local** | Tuyệt đối (mặc định thực thi trong Docker container)3. | Trung bình (thao tác trực tiếp tệp tin máy host)3. | Cao (có Sandbox mode và kiểm soát quyền công cụ)7. | Tùy thuộc vào cấu hình môi trường4. |
| **4\. Chi phí Token & Hiệu năng** | Trung bình \- Cao (do khả năng tự sửa lỗi đa bước)5. | Tối ưu cao (nhờ Repo Map thu nhỏ ngữ cảnh)5. | Rất tối ưu (mã nguồn Rust nhẹ, xử lý nhanh)7. | Cao (tùy thuộc mô hình LLM kết nối)4. |

### **2.3. Khả Năng Xử Lý Tiếng Việt & Môi Trường Windows UTF-8**

Thách thức lớn khi chạy các CLI Agent trên hệ điều hành Windows tại Việt Nam là lỗi vỡ font ký tự tiếng Việt (UTF-8) khi xuất dữ liệu ra Console StdIO1.

* **Giải pháp kiến trúc**: Python Orchestrator khi khởi tạo tiến trình con (Subprocess) sẽ bắt buộc thiết lập các biến môi trường hệ thống:  
  * PYTHONUTF8=1  
  * PYTHONIOENCODING=utf-8  
  * Đặt mã trang Console Windows về UTF-8 (chcp 65001\) trước khi gọi CLI Agent.  
* **Đánh giá môi trường cô lập**: Khuyên dùng kiến trúc lai (Hybrid Execution Strategy):  
  * Môi trường mặc định: Chạy CLI Agent ngầm trong thư mục dự án cá nhân D:/my\_workspace/projects/{project\_id}/ với quyền hạn tệp tin bị giới hạn1.  
  * Môi trường nâng cao: Kích hoạt Docker Sandbox hoặc Windows Sandbox đối với các tác vụ có nguy cơ tự động chạy mã nguồn không an toàn3.

## **3\. Research Item 2: Thiết Kế Kiến Trúc React GUI & Python IPC Bridge**

Xây dựng giải pháp kết nối giao tiếp thời gian thực giữa giao diện người dùng React và bộ điều khiển Python Orchestrator1.

### **3.1. Sơ Đồ Kiến Trúc Luồng Giao Tiếp 3 Tầng**

Kiến trúc ứng dụng được chia thành 3 tầng rõ ràng:

* **Tầng 1: React GUI Frontend (Presentation Layer)**: Xây dựng bằng React.js / Next.js đóng gói Electron1. Quản lý giao diện Chat 2 chiều, thanh tiến trình trực quan (Live Activity Stepper) và Widget Token Metering1.  
* **Tầng 2: Python Orchestrator & Local API Bridge (Control Layer)**: Vận hành một Local Fast-API / WebSocket Server chạy trên cổng nội bộ (127.0.0.1:8765)1. Chịu trách nhiệm tiếp nhận lệnh từ GUI, nạp gói Skill từ D:/my\_workspace/skills/, đọc/ghi trạng thái dự án và quản lý tiến trình con (Subprocess Lifecycle)1. WebSocket cung cấp kênh truyền dữ liệu hai chiều (Bidirectional Full-Duplex) cho phép truyền lệnh và ngắt tiến trình tức thì11.  
* **Tầng 3: Headless Worker CLI Agent (Execution Layer)**: Tiến trình con do Python khởi chạy, nhận lệnh và Skill context, trực tiếp thao tác trên các tệp tin của thư mục dự án1.

### **3.2. Quy Chuẩn Giao Thức Stream Event JSON (NDJSON Protocol)**

Để hiển thị trạng thái thực thi mượt mà trên giao diện người dùng, Python Orchestrator đọc luồng stdout của CLI Agent, phân tích thành các sự kiện định dạng JSON và đẩy về React GUI qua WebSocket1:

| Loại Event (Event Type) | Cấu trúc Payload dữ liệu | Mô tả chức năng hiển thị trên UI |
| :---- | :---- | :---- |
| agent\_thought | {"type": "thought", "content": "Đang phân tích..."} | Hiển thị suy luận nội tại của Agent trong ô Chat1. |
| tool\_call\_start | {"type": "tool\_start", "tool": "read\_file", "params": {...}} | Kích hoạt hiệu ứng đang chạy công cụ trên Live Stepper1. |
| tool\_call\_end | {"type": "tool\_end", "tool": "read\_file", "status": "success"} | Đánh dấu hoàn thành bước công cụ, cập nhật danh sách tệp1. |
| file\_mutation | {"type": "file\_edit", "path": "draft/contract.md", "diff": "..."} | Hiển thị thông báo tệp tin bị thay đổi hoặc cập nhật1. |
| stepper\_update | {"type": "step", "current": 2, "total": 5, "label": "Soát lỗi"} | Cập nhật thanh tiến trình tổng thể của dự án1. |
| token\_usage | {"type": "tokens", "prompt": 1200, "completion": 350, "cost": 0.004} | Cập nhật số liệu trên Widget Token Metering1. |

### **3.3. Thiết Kế Giao Diện Live Activity Stepper & Chat 2 Chiều**

Giao diện người dùng được chia thành 2 khu vực tương tác chính:

> 1. **Khung Chat 2 chiều (Interactive Conversation Window)**: Nơi người dùng nhập yêu cầu bằng tiếng Việt tự nhiên và nhận câu trả lời đã được định dạng văn bản / Markdown từ Agent1.  
> 2. **Thanh Tiến Trình Trực Quan (Live Activity Stepper)**: Bảng mảng dọc (Accordion/Timeline Widget) nằm song song với khung chat. Mọi thao tác như đọc tài liệu, kiểm tra cú pháp, gọi script Python nội bộ hay ghi tệp tin đều được hiển thị thành các nấc tiến trình trực quan thời gian thực, giúp người dùng không chuyên hiểu rõ Agent đang làm gì mà không bị ngợp bởi các dòng code thô1.

## **4\. Research Item 3: Đóng Gói Session State & Quản Lý Context Budget**

Giải pháp đóng gói bối cảnh làm việc và tối ưu hóa ngân sách token khi vận hành các phiên làm việc kéo dài1.

### **4.1. Cấu Trúc Quản Lý Trạng Thái Phiên Làm Việc Cục Bộ**

Mỗi dự án tại D:/my\_workspace/projects/yyyyMMdd-hhmmss-{name}/ chứa hai tệp tin điều khiển trung tâm1:

* **PROJECT\_PLAN.md**: Tệp tài liệu cấu trúc lưu trữ kế hoạch tổng thể:  
  * Mục tiêu dự án.  
  * Danh sách công việc (Checklist: \[ \] Chưa làm, \[/\] Đang làm, \[x\] Hoàn thành).  
  * Kết quả đầu ra mong đợi (Deliverables).  
  * Quy định & Giới hạn áp dụng.  
* **STATE.json**: Tệp dữ liệu máy đọc lưu trữ trạng thái động:  
  * Định danh dự án, thời gian khởi tạo và cập nhật gần nhất.  
  * Chỉ số bước hiện tại (current\_step\_index).  
  * Danh sách các tệp tin tài sản đã tạo (created\_artifacts).  
  * Tóm tắt bối cảnh đang thực thi (context\_summary).  
  * Tham số cấu hình của các Skill đang được kích hoạt.

### **4.2. Chiến Lược Nạp Context Tóm Tắt (Context Budgeting)**

Thay vì nạp toàn bộ lịch sử trò chuyện thô (Raw Chat History) vào LLM — nguyên nhân chính gây phình dung lượng token và trôi bối cảnh (context drift) — Python Orchestrator áp dụng cơ chế "Bọc ngữ cảnh tinh gọn" (Context Injection Engine)1:

Thành phần Ngữ cảnh Nạp vào LLM (Context Payload Window)  
├── 1\. Hệ thống chỉ dẫn cơ bản (System Prompt & Skill Instructions)  
├── 2\. Hồ sơ người dùng tinh gọn (user\_profile.json / org\_profile.json)  
├── 3\. Kế hoạch thực thi dự án hiện tại (PROJECT\_PLAN.md)  
├── 4\. Trạng thái tóm tắt phiên làm việc (STATE.json \-\> context\_summary)  
└── 5\. N câu thoại trò chuyện gần nhất (Short-term Chat Memory, N \<= 4\)

**Kết quả thử nghiệm**: Phương pháp đóng gói này giúp cắt giảm từ 70% đến 90% dung lượng token không cần thiết trong các phiên làm việc kéo dài hàng giờ, đảm bảo Agent luôn tuân thủ đúng kế hoạch trong PROJECT\_PLAN.md mà không bị quên chỉ dẫn ban đầu1.

### **4.3. Giao Thức Khôi Phục Phiên Làm Việc (Session Recovery Protocol)**

Khi người dùng tắt ứng dụng GUI và mở lại một dự án cũ:

> 1. Python Orchestrator quét thư mục dự án được chọn, đọc tệp STATE.json và PROJECT\_PLAN.md1.  
> 2. Hệ thống khôi phục ngay lập tức thanh tiến trình (Live Activity Stepper) về đúng bước đang dở dang1.  
> 3. Khi người dùng nhập lệnh mới, Orchestrator gửi bối cảnh đã tóm tắt từ STATE.json sang CLI Agent, cho phép Agent tiếp tục công việc ngay lập tức mà không cần hỏi lại lịch sử1.

## **5\. Research Item 4: Tích Hợp Elixverse AI API Routing Gateway**

Nghiên cứu cơ chế kết nối API, bảo vệ ngân sách tài chính và hiển thị chi phí trực quan trên ứng dụng GUI1.

### **5.1. Kiến Trúc Cầu Nối API Gateway & Điều Hướng Mô Hình**

Python Orchestrator tích hợp mô-đun kết nối API Gateway hỗ trợ hai tuyến điều hướng1:

* **Tuyến 1: Elixverse API Routing Gateway**: Đi qua Gateway trung tâm để quản lý định tuyến linh hoạt, tự động chuyển đổi mô hình dự phòng (Failover Router) khi một nhà cung cấp gặp sự cố1.  
* **Tuyến 2: Direct Provider API**: Kết nối trực tiếp bằng API Key riêng của người dùng (OpenAI, Anthropic, Google Gemini, OpenRouter, Ollama local)1.

### **5.2. Cơ Chế Bắt Buộc Hạn Mức Chi Tiêu (Spend Cap & Rate Limiting)**

Để bảo vệ người dùng phổ thông khỏi nguy cơ bùng nổ chi phí do Agent lặp vô tận (infinite loop):

* **Hạn mức Mềm (Soft Limit)**: Cảnh báo trên giao diện UI khi chi phí trong ngày/tháng đạt 80% ngưỡng thiết lập1.  
* **Hạn mức Cứng (Hard Limit / Auto-Cutoff)**: Khi chi phí đạt 100% ngưỡng an toàn (ví dụ: tối đa 5 USD/ngày), Gateway hoặc Orchestrator sẽ chủ động từ chối các request tiếp theo và gửi tín hiệu ngắt tiến trình CLI Agent1.  
* **Rate Limiting (RPM/TPM)**: Tự động xếp hàng các request (Queue Management) và áp dụng thuật toán Lùi thời gian lũy thừa (Exponential Backoff with Jitter) khi gặp lỗi HTTP 429 Too Many Requests.

### **5.3. Thiết Kế Widget Token Metering Trên React GUI**

Trên góc giao diện Scriptorium Workspace, một đồng hồ chi phí (Token & Cost Meter) được cập nhật thời gian thực sau mỗi bước xử lý của Agent1:

* Hiển thị tổng số Prompt Tokens (dữ liệu đầu vào) và Completion Tokens (dữ liệu đầu ra)1.  
* Tự động quy đổi chi phí ra đơn vị tiền tệ (USD / VND) dựa trên bảng giá của mô hình đang sử dụng1.  
* Hiển thị biểu đồ thanh trực quan so sánh mức độ tiêu thụ token giữa các phiên làm việc, giúp người dùng nắm rõ ngân sách sử dụng1.

## **6\. Tổng Hợp Kết Luận & Lộ Trình Thực Thi Dự Án**

### **Bảng Tổng Hợp Giải Pháp Cho 4 Hạng Mục Nghiên Cứu**

| Hạng mục nghiên cứu | Giải pháp kỹ thuật được chốt | Sản phẩm đầu ra cụ thể |
| :---- | :---- | :---- |
| **Research Item 1: Worker CLI Agent** | Chiến lược lai (Goose / OpenHands SDK cho tác vụ phức tạp; Aider / OpenCode cho tác vụ local nhẹ)1. | Bộ thông số Benchmark & Script khởi tạo CLI Agent ngầm với môi trường UTF-81. |
| **Research Item 2: React GUI & IPC Bridge** | React Electron Frontend \+ FastAPI WebSocket Bridge (127.0.0.1:8765) \+ NDJSON Stream Event Parser1. | Sơ đồ giao thức WebSocket JSON và Component Live Activity Stepper1. |
| **Research Item 3: Session State & Budget** | Quản lý qua PROJECT\_PLAN.md & STATE.json \+ Bộ lọc Context Budgeting cắt giảm 70-90% token1. | Thư mục mẫu \_template/ cho dự án và Engine nạp/khôi phục ngữ cảnh1. |
| **Research Item 4: API Gateway Integration** | Định tuyến Elixverse / Direct API \+ Hard Spend Cap Auto-Cutoff \+ Token Metering Widget1. | Mô-đun Python kiểm soát chi phí & Component đồng hồ Token trên GUI1. |

### **Lộ Trình Triển Khai Thực Tế Tiếp Theo (Phases)**

> 1. **Giai đoạn 1 (Hạ tầng IPC & Subprocess Stream)**: Xây dựng bộ khung ứng dụng React \+ Electron, thiết lập WebSocket Server bằng Python và thực hiện stream thử nghiệm luồng StdIO từ một Worker CLI Agent ngầm1.  
> 2. **Giai đoạn 2 (Quản lý State & Khung Giao Diện Workspace)**: Cài đặt bộ khởi tạo dự án theo chuẩn D:/my\_workspace/projects/, hiện thực hóa cơ chế đọc/ghi PROJECT\_PLAN.md và STATE.json, hoàn thiện thanh tiến trình Live Activity Stepper1.  
> 3. **Giai đoạn 3 (Tích hợp Gateway & Token Metering)**: Nhúng mô-đun API Routing Gateway, thiết lập cơ chế ngắt Spend Cap tự động và hoàn thiện đồng hồ đo Token trên GUI1.  
> 4. **Giai đoạn 4 (Đóng gói & Hướng Dẫn Người Dùng)**: Đóng gói ứng dụng GUI thành tệp cài đặt cục bộ, xuất bản tài liệu hướng dẫn người dùng không chuyên (NON\_TECH\_ USER\_GUIDE.md) để kết nối mượt mà với các gói Skill từ Scriptorium Core1.

#### **Works cited**

> 1. WORKSPACE\_RESEARCH\_AND\_ROADMAP.md  
> 2. MASTER\_CONTEXT.md  
> 3. Open-source AI agents \- Modal, [https://modal.com/blog/open-ai-agents](https://modal.com/blog/open-ai-agents)  
> 4. GitHub \- bradAGI/awesome-cli-coding-agents: Curated directory of terminal-native AI coding agents and the harnesses that orchestrate them. Covers open-source tools (Pi, OpenCode, Aider, Goose), platform agents (Claude Code, Codex, Gemini CLI), parallel runners, autonomous loops, and agent infrastructure., [https://github.com/bradagi/awesome-cli-coding-agents](https://github.com/bradagi/awesome-cli-coding-agents)  
> 5. Aider vs Claude Code vs OpenHands CLI Compared \[2026\] \- Kunal Ganglani, [https://www.kunalganglani.com/blog/aider-vs-claude-code-openhands-cli](https://www.kunalganglani.com/blog/aider-vs-claude-code-openhands-cli)  
> 6. OpenHands | The Open Platform for Cloud Coding Agents, [https://www.openhands.dev/](https://www.openhands.dev/)  
> 7. goose | Your open source AI agent, [https://goose-docs.ai/](https://goose-docs.ai/)  
> 8. Terminal AI Agents: The 2025 Landscape \- wal.sh, [https://wal.sh/research/2025-terminal-ai-agents/](https://wal.sh/research/2025-terminal-ai-agents/)  
> 9. GitHub \- aaif-goose/goose: an open source, extensible AI agent that goes beyond code suggestions \- install, execute, edit, and test with any LLM, [https://github.com/aaif-goose/goose](https://github.com/aaif-goose/goose)  
> 10. Best AI Coding Assistants for the Terminal in 2026 \- DEV Community, [https://dev.to/lightningdev123/best-open-source-cli-coding-agents-to-explore-in-2026-5bn7](https://dev.to/lightningdev123/best-open-source-cli-coding-agents-to-explore-in-2026-5bn7)  
> 11. Agent-User Interaction Protocol: When the frontend got an AI protocol \- Via Transportation, [https://ridewithvia.com/resources/agent-user-interaction-protocol-when-the-frontend-got-an-ai-protocol](https://ridewithvia.com/resources/agent-user-interaction-protocol-when-the-frontend-got-an-ai-protocol)  
> 12. WebSockets and AI: Why LLMs Are Moving Beyond SSE, [https://websocket.org/guides/websockets-and-ai/](https://websocket.org/guides/websockets-and-ai/)