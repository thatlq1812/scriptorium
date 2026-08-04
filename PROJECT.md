Hiện tại, tôi muốn làm sạch một số nội dung bên trong dự án này, với trọng tâm là chuẩn hóa tốt hơn, gọn gàng hơn

1. Tôi muốn xóa vết tích nhắc đến Edustation trong dự án này

2. Theo như định hướng từ ban đầu, tôi đã xác định rõ rằng, Scriptorium sẽ là nơi nghiên cứu và phát triển ra các skill đặc chủng cho nhiều mảng công việc tại Việt Nam, có thể mở rộng đa ngành nghề
Và tiếp nối nó, một "Scriptorium Workspace" là một app trực quan được tưởng tự như sau:
Sẽ là một app GUI thân thiện với người dùng, sẽ trỏ thẳng vào một thư mục cá nhân của người dùng, ví dụ như D:/my_workspace
Trong my_workspace sẽ có các thư mục như: personals,data,documents, skills, registry, projects, ... ( nói chung sẽ là nơi mà các agent chạy và đối chéo thông tin)
Trong projects, sẽ có thư mục _template được tạo từ đầu với khả năng tối ưu cho công việc của người dùng, rồi các thư mục được đặt tên tối ưu, theo tôi là yyyyMMdd-hhmmss-{name} hoặc bất kì kiểu nào khác mà tối ưu
Khi người dùng yêu cầu bắt đầu phiên làm việc mới, hệ thống sẽ init và thiết lập projects mới cho người dùng

Về kiến trúc app, tôi có ý tưởng như sau

Người dùng <-> Giao diện GUI trực quan <-> Agent trung gian để truyền đạt 2 chiều giữa người dùng và Agent thực thi công việc ( ở đây ta có thể hiểu là nó đọc yêu cầu của người dùng, diễn giải chi tiết dựa trên đặc tính của ứng dụng cho agent thực thi, và ngược lại, diễn giải phản hồi của agent thực thi cho người dùng) <-> Agent thực thi ( Ở đây tôi có ý tưởng về việc sử dụng các coding cli opensource để chạy agent) <-> Nối trực tiếp với elixverse ( một AI API routing của riêng hệ thống elix).

Từ đó sẽ chuẩn hóa được mô hình tạo ra thu nhập, và mượt mà với hệ thống hơn, bạn thấy sao với kiến trúc này? tôi muốn bạn nhận xét, hoặc có thể research riêng về phiên thảo luận này xem nó có khả thi hay không, có độc đáo không, và nếu bạn là người dùng phổ thông tại việt nam, bạn nghĩ sao về nó?

===

Phần 1, tôi đồng ý, ta không cần nhắc về edustation nữa, vì hiện tại scriptorium project đã được chuẩn hóa chất lượng cao hơn rồi
Phần 2, tôi hiểu vấn đề đó và đó cũng chính là mục đích mà Scriptorium và Scriptorium Workspace được lên ý tưởng
Nhưng ở phần 3, tôi có nhận định như sau: Không phải chọn, mà là người dùng chỉ cần một dòng chat phi lập trình kiểu như "Hãy hỗ trợ tôi tạo ra một báo tường" hoặc bất cứ cái gì, ưu tiên vẫn là thiết lập project mới hoặc load project cũ. Giao diện hợp lý sẽ là Folders | Editor / Reviewer / Chat | có thể là tương tự vs code hoặc các coding IDE, nhưng tối giản hơn, không rườm ra như hiện tại, vì nó phải tối ưu cho người dùng phổ thông mà.
Việc chọn "Tạo hợp đồng" hay "Soạn bài giảng KHBD 5512" là đang đi vào vết xe đổ của Edustation, khóa cứng tác vụ mục tiêu khiến cho hệ thống yếu hơn hẳn. Cái ta cần là agent trung gian biết ta cần gì và biết nó phải làm gì
Phần 3, với các kđề xuất kiến trúc của bạn,
1. Đồng ý
2. Nên cân nhắc, vì agent sẽ không làm theo bước, mà làm tới khi ra sản phẩm hoàn chỉnh trên khả năng của hệ thống
3. Cái này bạn có thể review thử ở d:/elix/platform/docs,

Tạo một thư mục ở docs, có thể là roadmap hoặc tên gì hợp lý và xây dựng kế hoạch ngay trong đó nhỉ

Về dọn dẹp tàng tích của edustation, cứ triển khai nhé, vì nó cũng không nhiều
