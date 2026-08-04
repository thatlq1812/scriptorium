# **Báo Cáo Nghiên Cứu Kiến Trúc Scriptorium Workspace Và Lộ Trình Phát Triển Hệ Sinh Thái Agent Skills**

## **Phân Định Bối Cảnh Hệ Thống Và Ranh Giới Kiến Trúc**

Nghiên cứu về hệ thống Scriptorium đặt nền móng cho việc xây dựng một môi trường đóng gói, kiểm toán an ninh và cataloging các gói kỹ năng Agent (Agent Skills) tuân thủ chuẩn mở SKILL.md1. Hệ thống được chia tách một cách nghiêm ngặt thành hai khu vực độc lập về mặt chức năng: kho mã nguồn cốt lõi Scriptorium Core (elix/scriptorium) và ứng dụng giao diện người dùng Scriptorium Workspace1. Sự phân định này bảo đảm triết lý thiết kế tối giản của hạt nhân hệ thống, đồng thời tạo không gian mở rộng cho các trải nghiệm tương tác cục bộ1.  
Scriptorium Core giữ vai trò là nhà xưởng chuyên biệt cho việc sáng tạo, kiểm định an ninh, đánh giá chất lượng và xuất bản các artifact chuẩn SKILL.md1. Tệp mã nguồn cốt lõi áp dụng triết lý 100% không tích hợp bất kỳ API AI backend nào2. Bất kỳ Agent tiêu thụ nào (consuming agent) vận hành các gói skill từ Scriptorium sẽ tự sử dụng mô hình ngôn ngữ và hạ tầng AI riêng của agent đó2. Quyết định này giúp loại bỏ sự phụ thuộc vào nhà cung cấp mô hình, bảo toàn tính tương thích của skill trên hàng chục nền tảng agent khác nhau2.  
Ngược lại, Scriptorium Workspace được định hình như một ứng dụng giao diện trực quan (GUI App) dành cho người dùng phổ thông tại Việt Nam, vận hành theo mô hình không gian làm việc ưu tiên lưu trữ cục bộ (Local-First Workspace)1. Workspace chịu trách nhiệm tự động hóa việc khởi tạo dự án, quản lý hồ sơ người dùng, và điều phối các công cụ dòng lệnh ngầm (Headless Worker CLI Agents) thực thi công việc thông qua các gói skill xuất bản từ Core1. Tài liệu nghiên cứu trong docs/roadmap/ đóng vai trò hoàn toàn độc lập, không can thiệp hay biến đổi mã nguồn các skill hiện có trong Core Repo1.

| Thành phần hệ thống | Phạm vi trách nhiệm | Tích hợp AI Backend | Môi trường thực thi chính |
| :---- | :---- | :---- | :---- |
| **Scriptorium Core** (elix/scriptorium) | Sáng tạo, kiểm toán an ninh, đánh giá chất lượng, đóng gói và cataloging các SKILL.md1. | Hoàn toàn không tích hợp2. | CLI / Môi trường phát triển kỹ năng2. |
| **Scriptorium Workspace** (docs/roadmap/) | Quản lý dự án cục bộ, giao diện tương tác React, điều phối Worker CLI Agents1. | Thông qua Worker CLI Agent của người dùng1. | Môi trường máy tính cục bộ người dùng (D:/my\_workspace)1. |

Sự phân tách ranh giới này đảm bảo Scriptorium Core duy trì tính gọn nhẹ, tập trung hoàn toàn vào tiêu chuẩn kỹ thuật của skill, trong khi Scriptorium Workspace có thể tự do tiến hóa về mặt trải nghiệm người dùng mà không làm phình dung lượng hoặc gia tăng độ phức tạp kiểm toán cho kho mã nguồn hạt nhân1.

## **Đánh Giá Quyết Định Kỹ Thuật Và Kiến Trúc Giao Tiếp IPC**

### **Bác bỏ Tauri và định hướng React / Web-First**

Một trong những quyết định kỹ thuật quan trọng nhất của dự án là việc loại bỏ hoàn toàn khung phát triển Tauri (Rust) cho ứng dụng GUI Workspace1. Mặc dù Tauri sở hữu ưu thế về dung lượng đóng gói nhỏ gọn và khả năng tối ưu tài nguyên hệ thống, việc kết hợp giữa ngôn ngữ Rust với backend Python cùng các luồng xử lý tiến trình con (subprocess stream) mang lại độ phức tạp tích hợp cực kỳ lớn1. Sự bất tương thích và ma sát kỹ thuật (High Friction) trong giao tiếp IPC khi truyền nhận luồng dữ liệu StdIO thời gian thực giữa Rust và Python gây khó khăn nghiêm trọng cho việc bảo trì mã nguồn1.  
Thay vào đó, kiến trúc chuyển hướng sang giải pháp **React** (React.js / Next.js hoặc React đóng gói qua Electron Wrapper)1. Việc xây dựng ứng dụng trên nền tảng React cho phép tận dụng hệ sinh thái giao diện hiện đại, tối ưu hóa khả năng quản lý luồng dữ liệu WebSocket và StdIO stream trực tiếp với Python subprocess backend1. Sự kết hợp này mang lại khả năng phản hồi mượt mà cho giao diện hội thoại hai chiều (Chat) và thanh tiến trình chi tiết (Live Activity Stepper)1.

### **Khảo sát Worker CLI Agent và Cấu trúc Workspace Cục bộ**

Đối với tầng thực thi công việc (Worker CLI Agent), hệ thống bác bỏ việc ấn định trước bất kỳ công cụ cụ thể nào1. Thay vào đó, một đợt đánh giá độc lập được thiết lập để đo kiểm các Worker CLI Agent mã nguồn mở hiện hành dựa trên bốn tiêu chí cốt lõi: độ ổn định khi chạy ngầm (Headless execution stability), khả năng stream kết quả qua StdIO/JSON, mức độ an toàn khi thao tác tệp tin cục bộ, và hiệu năng thực thi đi kèm chi phí token1.  
Không gian làm việc của người dùng được tổ chức nhất quán tại thư mục cục bộ (ví dụ D:/my\_workspace), đảm bảo dữ liệu cá nhân không rời khỏi máy tính và tạo điểm đối chiếu thông tin cho các Agent1. Tổ chức cây thư mục bao gồm:

* Thư mục personals/: Lưu trữ hồ sơ cá nhân và tổ chức như user\_profile.json và org\_profile.json1.  
* Thư mục data/: Lưu trữ tài sản doanh nghiệp bao gồm tệp mẫu Slide PPTX, mẫu văn bản Word, và bảng màu nhận diện1.  
* Thư mục documents/: Kho tài liệu tham khảo dài hạn phục vụ việc tra cứu ngữ cảnh1.  
* Thư mục skills/: Nơi lưu trữ các gói Skill được xuất bản từ Scriptorium1.  
* Thư mục registry/: Registry cục bộ quản lý thông tin các skill đã cài đặt1.  
* Thư mục projects/: Lưu trữ các phiên làm việc theo cấu trúc định danh thời gian yyyyMMdd-hhmmss-{name}, chứa thư mục mẫu \_template/ để khởi tạo dự án mới1.

### **Đóng gói Session State và Ngân sách Ngữ cảnh (Context Budget)**

Để giải quyết bài toán phình dung lượng token trong quá trình tương tác dài hạn với LLM, Scriptorium Workspace thiết kế cơ chế quản lý trạng thái phiên làm việc khép kín trong từng thư mục dự án1. Bằng cách duy trì hai tệp tin điều khiển trung tâm là PROJECT\_PLAN.md (kế hoạch thực thi) và STATE.json (trạng thái hiện tại), hệ thống có thể khôi phục bối cảnh làm việc tức thì1.  
Cơ chế này giúp loại bỏ việc nạp lại toàn bộ lịch sử trò chuyện thô vào cửa sổ ngữ cảnh (context window) của Agent1. Phân tích hiệu năng cho thấy phương pháp đóng gói trạng thái này giảm thiểu từ ![][image1] đến ![][image2] chi phí token không cần thiết, giúp giữ vững tốc độ xử lý và hạn chế hiện tượng trôi bối cảnh của mô hình1.

## **Danh Mục Nghiên Cứu Trọng Tâm Và Tiến Trình Thực Thi**

Danh mục nghiên cứu backlog của Scriptorium Workspace tập trung giải quyết các bài toán hạ tầng và tích hợp theo bốn hạng mục chính1. Mỗi hạng mục giải quyết một mắt xích cụ thể trong chuỗi vận hành ứng dụng GUI1.

| Hạng mục nghiên cứu | Nội dung công việc trọng tâm | Mục tiêu kỹ thuật cần đạt |
| :---- | :---- | :---- |
| **Research Item 1: Survey & Benchmark Worker CLI Agents** | Khảo sát các Open-Source CLI Agents; đánh giá cơ chế cô lập môi trường thực thi (Sandbox isolation) và khả năng xử lý Tiếng Việt1. | Lựa chọn Agent nền tảng có độ ổn định headless cao và stream dữ liệu chuẩn xác1. |
| **Research Item 2: Thiết kế Kiến trúc React GUI & Python IPC Bridge** | Thiết kế sơ đồ giao tiếp qua WebSocket / Local API; xây dựng giao diện Chat 2 chiều và Live Activity Stepper1. | Đảm bảo luồng dữ liệu tiến trình con phản hồi thời gian thực trên giao diện người dùng1. |
| **Research Item 3: Đóng gói Session State & Context Budget** | Tối ưu cơ chế đọc/ghi PROJECT\_PLAN.md và STATE.json trong từng thư mục dự án1. | Khôi phục bối cảnh chính xác mà không làm phình dung lượng token phiên làm việc1. |
| **Research Item 4: Tích hợp Elixverse AI API Routing Gateway** | Nghiên cứu giao thức kết nối API Routing, quản lý Spend Cap, Rate Limiting và hiển thị Token Metering trên GUI1. | Minh bạch hóa chi phí sử dụng API và bảo vệ người dùng khỏi hạn mức vượt quá1. |

Tiến trình thực thi các hạng mục nghiên cứu này diễn ra song song với quá trình nâng cấp các công cụ cốt lõi của Scriptorium Core4. Sự kết nối giữa việc tối ưu hóa giao thức API Gateway và hiển thị chi phí trực quan trên GUI giúp người dùng phổ thông kiểm soát hoàn toàn tài chính khi vận hành các mô hình thương mại1.

## **Quản Lý Chất Lượng Chiết Xuất Và Chuẩn Hóa Danh Mục Skill**

### **Phân định phạm vi Đánh giá Chất lượng (Stage 4 Scoping)**

Quy trình phát triển skill tại Scriptorium tuân thủ nghiêm ngặt khung 9 bước, bao gồm từ nghiên cứu, chiết xuất quy trình ẩn, tạo lập, kiểm toán an ninh cho đến đăng ký registry2. Tuy nhiên, từ thực tiễn kiểm toán phiên bản v0.2.0, một thay đổi kiến trúc quan trọng đã được thực thi đối với Stage 4 (Quality Evaluation)3. Stage 4 không còn áp dụng tràn lan cho mọi skill trong hệ thống3. Các skill thuộc hạ tầng nền tảng hoặc năng lực chung được miễn trừ hoàn toàn khỏi cổng kiểm định chất lượng chính thức này3.  
Phạm vi Stage 4 được giới hạn chặt chẽ vào hai nhóm đối tượng: các skill chuyên biệt hóa ngách (niche-specializer) được chiết xuất trực tiếp từ nguồn chuyên gia thực tế, và các skill trực tiếp xử lý dữ liệu đầu vào chưa qua kiểm soát từ bên ngoài (uncontrolled external input)3. Sự điều chỉnh này giúp tập trung tài nguyên kiểm định vào những nơi có rủi ro cao nhất, tránh lãng phí chi phí đánh giá trên các công cụ hạ tầng thuần túy3.

Tổng số 63 Skills trong Registry  
├── Nhóm Bắt buộc Stage 4 (15 skills)  
│   ├── Skill chuyên biệt ngách từ nguồn chuyên gia (Ví dụ: Các skill thuộc Legal Network)  
│   └── Skill xử lý đầu vào chưa kiểm soát (Ví dụ: document-ai-structurer, deep-research)  
└── Nhóm Miễn trừ Stage 4 (48 skills)  
    ├── Skill hạ tầng / pipeline (Ví dụ: skill-creator, python-env-bootstrap)  
    └── Skill năng lực chung định dạng đầu vào rõ ràng (Ví dụ: office-doc-creator, mermaid-diagram-designer)

### **Chiến lược Nâng cấp Chiết xuất Tri thức và Phân phối**

nhằm nâng cao chất lượng tri thức chiết xuất từ tài liệu dài (sách chuyên ngành, sổ tay kỹ thuật), skill-creator v0.4.0 đã tích hợp Chế độ Chiết xuất Tài liệu (Document Distillation Mode), lấy cảm hứng từ dự án book-to-skill4. Chế độ này chủ động chia tách tài liệu lớn thành một tệp chỉ mục chính SKILL.md (\~4,000 tokens) cùng các tệp chuyên đề nằm trong references/ hoặc chapters/ (\~1,000 tokens/file) để nạp theo nhu cầu4. Giải pháp này mang lại hiệu quả giảm thiểu từ 24 đến 51 lần dung lượng token khi Agent truy xuất dữ liệu4.  
Song song đó, công cụ xuất bản skill-exporter v0.2.x được tái định hình thành Động cơ Triển khai Tri thức (Knowledge Deployment Engine)4. Vận hành theo nguyên tắc "Giao hàng Không Nhiễu" (Zero-Noise Delivery), công cụ này tự động lọc các skill dựa trên vai trò và nhiệm vụ để tránh ô nhiễm bối cảnh trong môi trường thực thi của Agent4. Mỗi gói xuất bản được đính kèm tệp khóa phiên bản skills.lock, sơ đồ phụ thuộc dependency-tree.md, và tự động loại bỏ các skill đang có nợ bản quyền (license\_debt), chưa vượt qua kiểm toán an ninh (security\_audit), hoặc đang ở trạng thái tạm dừng (operational\_status: paused)4.

### **Điểm dừng Tái cấu trúc Năng lực Vai trò Giáo dục**

Trong quá trình mở rộng danh mục skill theo tầng vai trò, skill socratic-concept-helper thuộc tầng Học sinh/Người học đã được chuyển sang trạng thái tạm dừng (operational\_status: paused)3. Phân tích sâu chỉ ra hai lý do kết hợp: thứ nhất, việc xây dựng skill này đi trước kết quả khảo sát thực tế giữa học sinh và giáo viên, trong khi các nghiên cứu giáo dục hiện đại khẳng định sự tham gia của giáo viên là điều kiện bắt buộc3; thứ hai, tồn tại sự lệch pha về mô hình vận hành khi giả định học sinh K12 trực tiếp thao tác trên giao diện dòng lệnh Agent3.  
Quyết định tạm dừng bảo tồn tính nguyên tắc của hệ thống: không duy trì các skill sản xuất khi chưa xác định đúng đối tượng vận hành thực tế (chẳng hạn như chuyển hướng sang người vận hành là giáo viên hoặc gia sư)3. Đồng thời, các tầng vai trò Học sinh K12 và Sinh viên Đại học đã được hợp nhất thành một tầng duy nhất "Học sinh / Người học" để phản ánh đúng sự tương đồng về hình thái kỹ thuật của skill3.

## **Định Hướng Tích Hợp Và Lộ Trình Triển Khai Tiếp Theo**

Sự phát triển của Scriptorium Workspace và Scriptorium Core tạo nên một hệ sinh thái bổ trợ lẫn nhau, nơi Core đóng vai trò sản xuất và Workspace đóng vai trò thực thi1. Các bước triển khai tiếp theo được xác định nhằm hoàn thiện toàn bộ hạ tầng giao tiếp và nâng cao trải nghiệm người dùng cuối1:

> 1. **Hoàn tất Benchmark Worker CLI Agents**: Tổ chức kiểm thử thực tế các Agent mã nguồn mở trên các kịch bản chạy ngầm, đo lường tốc độ stream JSON/StdIO và mức độ tiêu thụ tài nguyên1.  
> 2. **Thực thi Kiến trúc React GUI & Python IPC**: Xây dựng ứng dụng mẫu React Web-First kết nối trực tiếp với Python Orchestrator qua WebSocket local, tích hợp Live Activity Stepper để hiển thị chi tiết tiến trình thực thi của Agent1.  
> 3. **Tích hợp Gateway Kiểm soát Chi phí**: Đưa giao thức API Routing Gateway vào Workspace để quản lý Spend Cap và hiển thị Token Metering ngay trên giao diện, giúp người dùng theo dõi chi phí theo thời gian thực1.  
> 4. **Hoàn thiện Tài liệu Hướng dẫn Người dùng Không chuyên**: Xuất bản các tài liệu hướng dẫn trực quan (docs/guides/NON\_TECH\_USER\_GUIDE.md) nhằm giúp người dùng phổ thông dễ dàng đóng gói, nhập khẩu và vận hành các gói skill trên các phần mềm Agent thương mại và mã nguồn mở4.

#### **Works cited**

> 1. WORKSPACE\_RESEARCH\_AND\_ROADMAP.md  
> 2. MASTER\_CONTEXT.md  
> 3. DECISIONS\_PENDING.md  
> 4. ROADMAP.md  
> 5. STATUS.md  
> 6. README.md

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAZCAYAAABdEVzWAAACb0lEQVR4Xu2WT8hNQRiHf0IRksiXkPInKUXxJYU+hWxIKKJsbZRYkI8isvCvZEPYICmRlVIsvlgIGysbC5SShaysJH5P7xl3zjjndlPK4j71dM+dc+7MO+87M+dKff4PRtvpdmJ5o2CCHVs2/ism2wf2nL1r99hRtSeC+YrnZpU3cjbam3axnVE4oPqsFtqz9qrdZcdn9+CwvWfH2Kn2uX2qGIP+Fthh+9lurn7TCp39bPGLXVQ9t82+sUsVZTplHyuyBJTmiWLgxBG7xg7Z3Xan3W8vKYLvynVFWslC8pp9bw8pSjHbvlV0nphiX9l91Xcy8kEx0QTXm7LvrD1K3LWEwMwv22lF+wp7S51SEdA3u+z3ExHwbTui6GeSfaZ6YExsXXXN82fUQwmBgQkiTyuzYp3MydpIfRkY3LCf7Nzq+wVFsARB31fszOreentRPZSwCX5EEDuKdgJoCyxvZzKU96giiINVO6W7X33+FatVX9BAmUbUW2BApsjOEkXmmCxBphJynx3N7p5XtXWFDu4oMpaTdlsZADQFVkJAqYQcPWyu44rdzsbLl0wjnGNfVd95ibYA2toTZQlXKnZ3WpOcbweq61b2Ks6ufHsnTqs5AAL7qOa1U5YQWHMcKRwtwO/ouyuk9btdVd5QdP5Dna0P4+zDSq5L8hImOErywPg8r3i/NpIGacoK8Hp5aU9kbbzvyBaneQmZ4CDl6MnZqnpgjHWyc/tPui3wxHL7TnFoblccCxyY5T+EVEJ2ZglvkNd2rWLHHlPzczXYHZSxNa2KCWywWxSDNDGkGJCBmxi0L+wjxfoqJ9anT58+vfILu2Z1T4mlJVYAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACYAAAAZCAYAAABdEVzWAAAClUlEQVR4Xu2WS6hOURiGX6EIScolRC7JiHJLSUchAyQMRBkpExIDcikiA7eSkaRkcCYnMlKKwY+B28SIASWlJBkaGLi8T99e/957nb35J8rgf+vp/Hvttfd69/d961tH6uv/0EgzxYzPb2QaZ0bng/9KE81dc9EMmT1mRG1GaL5i3sz8Rq6xZpe5bs6p/YGF5oJiHvN5rqqj5rYZZSabp+ax2WimmwXmuPlsthTPtGqaeWSuKAxtMu/N6uoka7t5bZYo0nTWPFBECZGah4qFk46ZNWbA7DY7zUFzVWG+Vdy8Yd6YqZVxovZM5aKzzFvFy5MmmZdmf3FNRD4oopbE782Va2qPFLdlpKtF5qvpqF6svOynWVdcY+ibWdqdEbUzqPLZCeaJ6saOqHwH88+rhxQiFmLBjoYb+6VyEUKfG0O3zCczt7i+rDCLCervmplR3FuvKJc/pjDpb8ZIM8JAm7Hq+GxFek8oTBwuxkndneJvT6KGqCVSQCqSqDGMsTCGO+rNGCJSRGexInJECJMphakDsLvnFWONYrd9MSuL6zmKzZCMpd2WG0BNxnJhKKWQhkqrOaWobzJClBvFV9Ei3il2FY1vn+o11magbTwpT+Eqxe5ONUl/O1T87kkYq+5KUttkAGMf1Vw7eQoRNcfH01oQz/HuRh1Q1FgKKRG8qXof4+U/VBpFY8y9An7nqqYwiQxUjfH3kuJ8HSa++rsizGiFogVUv5Tj5YU5XRnjvCNadPNcRIJGSkOtapvqxsjAmfJ2XRjgqNlrTioWazp8lymOKprmDkVboGHm/yGkFLIzc3GCvDJrFe9nvaZ5XXEc0bs2KHZhm7jHnK2KRZo0oFgw/7Ck5ea5ua+or/zD+uqrr7561W85XYKYNdhZtgAAAABJRU5ErkJggg==>