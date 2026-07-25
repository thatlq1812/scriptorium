Hiện tại, sau khi rút kinh nghiệm từ app EduStation (các nội dung tài liệu được đính kèm)
Tôi đang có dự định xây dựng một app kiểu như Claude Code, Antigravity, hay Codex, nhưng không dành cho dev, mà dành cho người dùng bình thường
Có thể sử dụng hệ thống AI đang co của elixverse, hoặc api key của các provider
Kiểu như hệ thống sẽ được chuẩn bị sẵn những quy trình được chuẩn hóa máy học, đảm bảo có thể tạo ra được sản phẩm chát lượng ấy, đúng với khả năng của người hiểu biết vê lĩnh vực đó chứ không chỉ là một AI không biết gì đang cố làm sản phẩm tốt nhất, bạn hiểu chứ?

Tôi nghĩ, nhìn vào edustation  ( tất cả tài liệu hiện tại) thì nó thất bại, nhưng cũng không hẳn, mà là một bài học tốt

Ví dụ như hiện tại, grok code, kimi code, hay gemini cli đã là mã nguồn mở, thì tôi nghĩ nó là một thứ đáng giá để có thể xây lên hệ thống này

bạn thấy sao?

Show less

API_REFERENCE.md
md


API_KEYS_GUIDE.md
212 lines

md

Thế thì tôi khá đồng ý với việc fork thẳng Kimi code CLI, xong rồi sao nhỉ, gắn adapter hoặc tùy biến để có thể dùng được API của elixverse, cũng dễ hiểu là phía platform AI Routing sẽ cần phải nâng cấp thêm nhiều nếu muốn.

Và tôi nghĩ, thay vì như vậy, ta có nên phát triển một hệ thống tiền đề, là xây dựng các skill, để làm việc, tương tự như một agent ấy,

Ví dụ nha, ta có edustation và cụm skill của nó hoàn toàn có thể bê cho bạn, hoặc các Agent CLI khác làm việc, mượt là đằng khác,

Rồi ví dụ chuyển sang ngành luật, ta sẽ lấy các skill lõi, và bổ sung thêm các skill đặc chế cho ngành luật ( mà có thể nhé, có thể thôi, sẽ được tôi tạo ra một cách hoàn hảo, đỉnh cao luôn), bạn thấy sao. Sẽ có các agent cho từng tác vụ lặp lại mà có thể định nghĩa, như tra luuật, chuyển đổi văn bản luật thành bộ tài liệu markdown, rồi tạo văn bản, duyệt luật, tạo hợp đồng, vvv.... bạn thấy sao về kiểu hình anỳ

Vì vậy nên phase 1, hoặc giai đoạn 1, sẽ là một hệ thống tạo skill, còn cái hệ thống agent thì có thể để sau, vì ta nên xây cái lõi trước cái vỏ nhỉ, xây vỏ không mà skill không hoạt động ổn định thì cũng bỏ đi, bạn thấy thế nào. Riêng phần skill này ta đang có nguồn tham khảo vô cùng rộng lớn, từ các opensource code agent, để cả nhũng project skill riêng ấy?

Show less

Synthesized skill marketplace ecosystems và thiết kế hệ thống registry định danh
Synthesized skill marketplace ecosystems và thiết kế hệ thống registry định danh
Về web search hệ sinh thái skill hiện tại (không phải EduStation cũ, mà bức tranh thị trường ngay lúc này):

Landscape đã lớn và có cấu trúc rõ hơn nhiều so với một tháng trước:

SkillsMP — catalog lớn nhất, khoảng 1.5-1.6 triệu skill được index, đã phân theo 23 occupation group / 867 job category. Đây là một reference taxonomy thật, đáng nhìn qua trước khi tự nghĩ ra taxonomy riêng cho Scriptorium.
Skills.sh (Vercel Labs) — leaderboard công khai hơn 600.000 skill, có sparkline 8 tuần install trend, hỗ trợ 18 platform, có audit bảo mật tự động qua Snyk/Socket.
Agensi — marketplace curated hiếm hoi có review bảo mật thật: checklist 8 điểm (prompt injection, data exfiltration, secret detection, dangerous commands, obfuscation, external fetch, credential access, privilege escalation), chia doanh thu 70-80% cho creator, có gói Pro $9/tháng truy cập MCP trực tiếp.
anthropics/skills — reference chính chủ, MIT license, điểm khởi đầu an toàn nhất để học format chuẩn.
addyosmani/agent-skills — collection curated chất lượng cao trên GitHub, không phải marketplace, cài bằng cách copy thư mục.
NanoSkill.ai — mô hình hand-review 100%, chọn hẳn theo ngành (marketing) thay vì scrape đại trà — đáng nhìn như hình mẫu cho một "NanoSkill cho luật/Việt Nam" mà Scriptorium có thể trở thành.
Điểm quan trọng nhất rút ra từ vòng search này: phần lớn các marketplace (awesome-list, ClaudeSkills.wiki...) là scrape không kiểm duyệt, chỉ một số ít (Agensi, Skills.sh, NanoSkill.ai) làm review bảo mật/chất lượng thật. Đây đúng là khoảng trống mà Scriptorium — nếu làm nghiêm túc phần audit chất lượng + an toàn đã bàn ở lượt trước — có thể chiếm chỗ, không chỉ cho nội bộ mà về sau có thể là vị thế thị trường thật.

Về quy trình "web search → tìm skill liên quan → tìm repo → clone → đào sâu → chuyển đổi thành skill hệ thống": đây chính xác là mô hình các curator thương mại nói trên đang làm để kiếm tiền — nên hướng đi của bạn không chỉ hợp lý mà đã được thị trường chứng minh là một vị trí có giá trị thật, không phải chỉ tiện cho nội bộ. Nó xứng đáng trở thành một skill lõi riêng — gọi nó là skill scout/harvester — đứng ngay trước skill_creator trong pipeline đã bàn: scout tìm và đánh giá sơ bộ ứng viên → phân tích sâu → skill_creator mới nhận input đã lọc để chuẩn hóa.

Một chỗ cần thêm vào, không thể bỏ qua khi "harvest" từ nguồn ngoài: kiểm tra license trước khi convert. Skill trên Agensi thường bán có điều khoản dùng, không mặc nhiên cho phép redistribute lại dưới tên Scriptorium; skill MIT/Apache trên GitHub thì an toàn để adapt miễn giữ attribution; một số có thể GPL kéo theo ràng buộc copyleft nếu bạn phân phối lại. Nên thêm skill license-compliance checker làm bước bắt buộc ngay sau scout, trước khi bất kỳ nội dung harvest nào chạm vào skill_creator — tránh việc cả cụm skill về sau dính rủi ro bản quyền hàng loạt vì một quyết định sai ở bước đầu.

Về "skill lõi không thể quá ít" và phân chiều/hệ lưu trữ định danh — đồng ý, và nên thiết kế đa chiều thay vì một trục phân loại duy nhất:

Trục ngành/nghề (domain axis) — tham khảo trực tiếp mô hình 23 occupation group của SkillsMP thay vì tự nghĩ lại từ đầu.
Trục loại tác vụ (task-type axis, cắt ngang mọi ngành) — research/thu thập thông tin, chuyển đổi định dạng tài liệu, soạn thảo/sinh nội dung, rà soát/QA, giao tiếp/điều phối. Đây là trục hữu ích nhất để tái sử dụng skill lõi across ngành, vì "tạo hợp đồng" (luật) và "soạn công văn NĐ 30" (giáo dục) cùng nằm trong nhóm "soạn thảo văn bản" dù khác domain.
Trục risk-tier — đã bàn ở lượt trước, tái dùng mô hình N1-N5 của EduStation.
Trục harness-compatibility — skill này đã verify chạy sạch trên harness nào (Claude Code, Kimi Code CLI...), vì không phải skill nào cũng portable 100% như đã nói.
Hệ lưu trữ định danh nên có dạng registry kiểu package manager (giống npm/crates.io nhưng cho skill), tối thiểu các field: skill_id (định danh gốc, bất biến), version, nguồn gốc (tự viết hay harvest — nếu harvest thì repo url + commit hash), license, 4 trục tag ở trên, quality score (từ upgrade-loop), trạng thái + ngày audit an toàn, danh sách harness đã verify, dependency (script/tool đi kèm). Registry này vừa là công cụ quản trị nội bộ, vừa là thứ giúp scout skill mới không vô tình làm lại thứ đã có sẵn trong Scriptorium — nên thêm luôn một bước dedup/novelty-check tra registry trước khi khởi động skill_creator cho một ứng viên mới.

Nên có tag, và tôi nghĩ không nên quá phụ thuộc edustation ấy. Nãy giờ thì bạn cũng hiểu rõ cái định hướng mà tôi viết ra rồi nhỉ?


Xác nhận hướng dẫn, khẳng định tag linh hoạt, giảm phụ thuộc EduStation
Xác nhận hướng dẫn, khẳng định tag linh hoạt, giảm phụ thuộc EduStation
Tag: đúng hướng, và nên hiểu tag là lớp thực thi của 4 trục taxonomy đã bàn (domain, task-type, risk-tier, harness-compatibility) — mỗi skill gắn nhiều tag cùng lúc trên nhiều trục, không ép vào một danh mục cứng duy nhất. Đây cũng là cách SkillsMP và các registry package thật (npm keywords, GitHub topics) vận hành: category cứng dễ gãy khi ngành mới xuất hiện, tag đa trị thì mở rộng tự nhiên.

Về việc không phụ thuộc EduStation: đúng, và nên chốt rõ vai trò của nó — EduStation là nguồn bài học, không phải blueprint để kế thừa nguyên khối. Cụ thể: giữ lại nguyên lý (risk-tiered gating, audit trail, planning-phase HITL, injection-safety là bước bắt buộc), nhưng bỏ phần cụ thể hóa cho một vertical/harness riêng (manifest 16-field, N1-N5 gắn với dữ liệu học sinh VN, workspace sandbox riêng của EduStation). Đây cũng là lý do lượt trước tôi đề xuất nhắm thẳng vào spec mở agentskills.io thay vì manifest riêng của EduStation — cùng tinh thần bạn vừa nói ra.

Tóm tắt định hướng để xác nhận tôi hiểu đúng:

Không xây app/CLI/harness trước — lớp đó đang bị thương mại hóa nhanh (20-40+ platform đã hỗ trợ SKILL.md, đến mức các hãng lớn còn dùng lại code của nhau). Cái xây trước là Scriptorium — hệ thống tạo, kiểm thử, bảo mật, và quản lý danh mục cho Agent Skill portable across domain, không khóa vào một harness nào. Bộ skill lõi gồm: research/thu thập thông tin, elicit-quy-trình (biến tri thức ngầm của chuyên gia thật thành quy trình có cấu trúc), skill_creator tổng quát hóa, vòng lặp đánh giá chất lượng, audit an toàn/injection, skill scout/harvester (đi tìm và chuyển đổi skill tốt từ hệ sinh thái ngoài, có gate kiểm tra license), dedup/novelty-check, và một registry đa trục làm xương sống định danh. Luật là vertical thử nghiệm đầu tiên để chứng minh cơ chế. Vỏ/harness để sau — thậm chí có thể không cần tự xây, vì skill đã chạy được trên hệ sinh thái sẵn có; mô hình kinh doanh có thể là trở thành lớp nội dung/chất lượng tốt nhất phân phối qua hệ sinh thái đó, thay vì một app riêng. Elixverse API là backend AI khả dụng, còn thiếu spend cap theo key và độ chín của tool-calling/streaming cho vòng lặp agent dài. Repo đặt tên elix/scriptorium.

Hiểu đúng vậy không sai lệch chỗ nào.

Vậy ra dành một phiên research sâu cho ý tưởng và hướng đi này nhỉ, để rõ ràng hơn trong định hướng, cũng như các nội dung thật sự có sai sót và thay đổi? cũng như các tài liệu liên quan


Orchestrated comprehensive research strategy validating Scriptorium concept and identifying refinements
Orchestrated comprehensive research strategy validating Scriptorium concept and identifying refinements

Lead Researcher



Research complete
•
52 sources and counting...
52 sources
•
10m 57s
Here is your research result


Research Report
Document
Và bạn thấy nội dung ta research được rất có giá trị đúng không?
Hãy tạo cho tôi một file md chứa toàn bộ insight của thảo luận này, và toàn bộ nội dung research được


Orchestrated comprehensive markdown synthesis merging strategic insights and research findings
Orchestrated comprehensive markdown synthesis merging strategic insights and research findings
Nội dung research này thực sự có giá trị — nó không chỉ xác nhận hướng đi mà còn sửa được nhiều con số sai/lỗi thời (adoption ~44 platform chứ không phải 20-40, SkillsMP đã 2.3M chứ không phải 1.6M, "6.2/12" hóa ra không có nguồn), và phát hiện ra dữ liệu định lượng quan trọng bạn chưa có (self-generated skills "no benefit" — nghĩa là skill_creator bắt buộc phải có human-curated input, không thể để agent tự sinh skill mà không qua chuyên gia thật). Đang tạo file tổng hợp.


Created a file, read a file
Created a file, read a file
File gồm hai phần: Phần A tổng hợp toàn bộ quyết định và lý lẽ đã thống nhất qua thảo luận (từ bài học EduStation đến kiến trúc bootstrap skill, taxonomy, vertical pháp lý), Phần B là toàn văn báo cáo nghiên cứu kèm số liệu đã kiểm chứng và nguồn tham khảo.


Scriptorium dinh huong va nghien cuu
Document · MD
