Tải tool về bằng lệnh

`git clone https://github.com/tdivam77/Tool_fluig.git`

Hoặc tải trực tiếp.

⚙️ **HƯỚNG DẪN CÀI ĐẶT CHI TIẾT:**

1.  **Cài đặt Python 3:**
    * Truy cập [https://www.python.org/downloads/](https://www.python.org/downloads/) tải bản cài đặt phù hợp với Windows của bạn.
    * Khi cài đặt, **NHỚ tick vào ô "Add Python to PATH"** (rất quan trọng!).

2.  **Tải Tool:**
    * Lưu mã kịch bản Python ở trên vào một file có tên là `tool_fluig.py` trên máy tính của bạn (ví dụ: lưu vào thư mục `D:\FluigTool`).

3.  **Cài đặt Thư viện:**
    * Mở Command Prompt (CMD): Nhấn `Windows + R`, gõ `cmd`, rồi `Enter`.
    * Di chuyển đến thư mục bạn vừa lưu file tool. Ví dụ, nếu bạn lưu ở `D:\FluigTool`, gõ lệnh:
        ```cmd
        D:
        cd FluigTool
        ```
    * Cài đặt các thư viện cần thiết bằng cách gõ lệnh sau rồi `Enter`:
        ```cmd
        pip install requests selenium
        ```
        (Đợi một chút để pip tải và cài đặt).

4.  **Tải và Cài đặt ChromeDriver:**
    * **Kiểm tra phiên bản Chrome:** Mở Chrome, vào `chrome://settings/help` để xem phiên bản hiện tại của bạn (ví dụ: `125.0.6422.113`).
    * **Tải ChromeDriver:** Truy cập trang [https://googlechromelabs.github.io/chrome-for-testing/](https://googlechromelabs.github.io/chrome-for-testing/) (trang chính thức mới cho ChromeDriver). Tìm phiên bản ChromeDriver tương ứng với phiên bản Chrome của bạn và tải file zip cho `win64` (hoặc `win32` nếu máy bạn cũ).
    * **Giải nén và Đặt ChromeDriver:** Giải nén file zip vừa tải. Bạn sẽ thấy file `chromedriver.exe`. **Cách dễ nhất là copy file `chromedriver.exe` này và dán nó vào cùng thư mục với file `tool_fluig.py` của bạn** (ví dụ: `D:\FluigTool`).

🚀 **CÁCH CHẠY TOOL:**

1.  Mở Command Prompt (CMD) và di chuyển đến thư mục chứa file `tool_fluig.py` và `chromedriver.exe` (như bước cài đặt thư viện).
2.  Gõ lệnh sau để chạy tool rồi `Enter`:
    ```cmd
    python tool_fluig.py
    ```
3.  **Làm theo hướng dẫn trên màn hình console:**
    * Tool sẽ hỏi bạn **"Nhập Inviter ID Fluig của bạn:"**. Nhập ID của bạn rồi `Enter`.
    * Tool sẽ hỏi **"Bạn muốn tool chạy thành công bao nhiêu lần (để nhận 'tháng'):"**. Nhập số lần bạn muốn (ví dụ: `3`) rồi `Enter`.
4.  **Đăng nhập TempMail Thủ công (Lần đầu):**
    * Một cửa sổ trình duyệt Chrome sẽ tự động mở ra, điều hướng đến trang đăng nhập của `tempmail.id.vn`.
    * **BẠN CẦN ĐĂNG NHẬP THỦ CÔNG** vào tài khoản `tempmail.id.vn` của mình trong cửa sổ Chrome đó.
    * Sau khi đăng nhập thành công vào `tempmail.id.vn` và bạn thấy được giao diện quản lý email (có nút "Create random", "Copy"), hãy **quay lại cửa sổ Command Prompt (CMD) và nhấn phím `Enter`** để tool tiếp tục.
5.  **Theo dõi Tiến trình:**
    * Tool sẽ bắt đầu quá trình tự động. Bạn có thể theo dõi các bước đang thực hiện trong cửa sổ CMD.
    * Nó sẽ lặp lại cho đến khi đủ số lần thành công bạn đã nhập, hoặc đạt giới hạn số lần thử.

💡 **MỘT SỐ LƯU Ý KHÁC:**
* Đảm bảo bạn đã có tài khoản `tempmail.id.vn` và nhớ thông tin đăng nhập.
* Tool sẽ cố gắng tìm email xác minh từ Fluig (hoặc các tên người gửi/tiêu đề liên quan như "mockplus", "verification", "verify", "confirm").
* Các khoảng thời gian chờ trong tool đã được rút ngắn (theo yêu cầu trước là 2 giây cho nhiều thao tác). Nếu mạng chậm hoặc máy yếu, tool có thể báo lỗi timeout. Khi đó, bạn có thể cần chỉnh sửa các giá trị `SELENIUM_GENERAL_TIMEOUT` trong code lên cao hơn (ví dụ 5-10 giây).
* Nếu `tempmail.id.vn` hoặc `Fluig` thay đổi đáng kể giao diện web của họ, tool có thể không hoạt động chính xác và cần được cập nhật.
