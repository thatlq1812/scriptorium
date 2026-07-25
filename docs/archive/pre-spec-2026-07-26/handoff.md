Gửi các agent sẽ làm việc trên Scriptorium

Trước khi bắt tay vào, đọc kỹ mấy điều sau — chúng không phải quy tắc phong cách, mà là bài học trả giá thật từ EduStation và từ chính dữ liệu ngành vừa research xong.

1. Thứ tự làm việc không được đảo. Elicit tacit process → research → skill_creator. Không được viết SKILL.md từ suy luận của chính bạn rồi coi là xong. SkillsBench đã đo: skill do agent tự sinh không cải thiện gì so với không có skill, tính trung bình. Nếu bạn đang viết một skill mà không có input từ một quy trình đã elicit từ người thật, hoặc từ nguồn research đã grounding — dừng lại, đó không phải việc bạn nên làm.

2. Đừng lặp lại lỗi của EduStation. EduStation không chết vì kiến trúc sai — nó chết vì đổ quá nhiều vào governance (18 R-rules, 5 non-negotiables, spec 23 mục) trước khi có một pilot thật nào chạy. Ở đây: một skill chạy tốt, được audit sạch, dùng thật trên một vertical nhỏ — quan trọng hơn mười skill nằm trong registry chưa ai dùng.

3. Bám đúng 6 field của spec mở agentskills.io — name, description, license, compatibility, metadata, allowed-tools. Không tự chế thêm field ngoài chuẩn vào frontmatter. Cần gì riêng, nhét vào metadata. Mọi lần lệch khỏi spec mở là một lần đánh đổi portability lấy tiện lợi ngắn hạn — không đáng.

4. Quality và security là hai người gác cổng khác nhau, không phải một. Đừng gộp chung một bước "review" cho cả hai. Pattern-matching scanner một lớp đã được chứng minh là bỏ sót phần lớn tấn công nghiêm trọng. Một skill chưa qua đủ cả hai cửa thì chưa được vào registry, không có ngoại lệ vì deadline.

5. Đừng tin lời tuyên bố tương thích — kể cả trong tài liệu này. "Chạy được trên Kimi Code CLI" chỉ có giá trị khi bạn đã tự chạy thật và thấy nó chạy. Trước khi đánh dấu harness-compatibility cho bất kỳ skill nào, verify trực tiếp, không copy từ showcase của ai.

6. Harvest từ nguồn ngoài luôn qua license-check trước khi chạm vào skill_creator. Không có ngoại lệ "chỉ để tham khảo nội bộ thôi". GPL lẫn vào sản phẩm đóng là nợ pháp lý thật, không phải rủi ro lý thuyết.

7. Vertical pháp lý: risk-tier quyết định mức giám sát, không phải deadline quyết định. Tra luật, chuyển văn bản → markdown: chạy tự động được. Duyệt luật, soạn hợp đồng: luôn có người thật xác nhận trước khi output rời khỏi hệ thống. Đây không phải thận trọng thừa — nó là ranh giới giữa một công cụ hữu ích và một vụ Mata v. Avianca phiên bản tiếng Việt.

8. Từ EduStation, lấy nguyên lý, không lấy khuôn. Audit trail, planning-phase HITL, risk-tiering — giữ. Manifest 16 field, workspace sandbox riêng, mọi thứ gắn cứng vào một harness cụ thể — bỏ. Nếu phân vân một thứ thuộc loại nào, tự hỏi: nó còn đúng nếu đổi domain, đổi harness không? Đúng thì giữ, không thì bỏ.

Làm ít, làm đúng, làm ra được một skill chuyên gia thật sự tin dùng — trước khi nghĩ đến quy mô.
