import requests
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service as ChromeService

# --- Configuration ---
WEBDRIVER_PATH = "chromedriver"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

# --- Timeout Constants ---
SELENIUM_GENERAL_TIMEOUT = 2
REQUESTS_TIMEOUT = 10
MAIN_VERIFICATION_DELAY = 5
POLL_ITERATIONS = 4
POLL_SLEEP_INTERVAL = SELENIUM_GENERAL_TIMEOUT / POLL_ITERATIONS

# ----- get_email_from_copy_button_attribute (Không đổi) -----
def get_email_from_copy_button_attribute(driver, wait_timeout_seconds):
    try:
        copy_button_xpath = "//button[.//span[normalize-space()='Copy']]"
        copy_button = WebDriverWait(driver, wait_timeout_seconds).until(
            EC.presence_of_element_located((By.XPATH, copy_button_xpath))
        )
        onclick_attribute = copy_button.get_attribute("x-on:click")
        if onclick_attribute:
            match = re.search(r"navigator\.clipboard\.writeText\('([^']+)'\)", onclick_attribute)
            if match and match.group(1):
                return match.group(1).strip()
            else:
                print(f"[BROWSER_DEBUG] Không thể phân tích email từ x-on:click của nút Copy. Giá trị: '{onclick_attribute}'")
        else:
            print("[BROWSER_DEBUG] Nút Copy được tìm thấy nhưng thuộc tính 'x-on:click' bị thiếu hoặc trống.")
    except TimeoutException:
        print(f"[BROWSER_ERROR] Timeout ({wait_timeout_seconds}s) khi chờ nút 'Copy' với XPath: {copy_button_xpath}.")
    except Exception as e:
        print(f"[BROWSER_ERROR] Lỗi xử lý nút 'Copy': {e}")
    return None

# ----- manage_temp_email_session (Không đổi logic chính, chỉ timeout) -----
def manage_temp_email_session(current_driver):
    driver = current_driver
    new_email = None
    try:
        if driver is None:
            print("[BROWSER] Chưa có session. Khởi tạo trình duyệt để đăng nhập tempmail.id.vn...")
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument(f"user-agent={USER_AGENT}")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1024,768")
            try:
                service = ChromeService(executable_path=WEBDRIVER_PATH)
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except Exception:
                try:
                    driver = webdriver.Chrome(options=chrome_options)
                except Exception as e_default:
                    print(f"[BROWSER_ERROR] Khởi tạo WebDriver mặc định cũng thất bại: {e_default}. Kiểm tra cài đặt.")
                    return None, None
            login_url = "https://tempmail.id.vn/en/login"
            driver.get(login_url)
            print(f"[BROWSER] Đã điều hướng đến trang đăng nhập: {login_url}")
            print("-" * 50)
            print("[YÊU CẦU HÀNH ĐỘNG] Vui lòng đăng nhập vào tempmail.id.vn trong cửa sổ trình duyệt.")
            print("Sau khi đăng nhập thành công VÀ bạn đang ở trang có nút 'Create random' và 'Copy',")
            print("nhấn Enter trong cửa sổ console này để tiếp tục.")
            print("-" * 50)
            input("Nhấn Enter tại đây sau khi đăng nhập và đến trang quản lý email...")
            print("[BROWSER] Giả định đăng nhập thành công.")
        else:
            print("[BROWSER] Sử dụng lại session trình duyệt hiện có.")
            expected_email_page_url = "https://tempmail.id.vn/en"
            current_page_simple = driver.current_url.split('?')[0].split('#')[0].rstrip('/')
            expected_page_simple = expected_email_page_url.rstrip('/')
            if current_page_simple != expected_page_simple and not current_page_simple.startswith(expected_page_simple + "/inbox"):
                print(f"[BROWSER] URL hiện tại '{driver.current_url}'. Điều hướng đến '{expected_email_page_url}'")
                driver.get(expected_email_page_url)
                try:
                    WebDriverWait(driver, SELENIUM_GENERAL_TIMEOUT).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                except TimeoutException:
                    print(f"[BROWSER_WARNING] Timeout khi chờ trang '{expected_email_page_url}' tải hoàn tất.")

        initial_email = get_email_from_copy_button_attribute(driver, SELENIUM_GENERAL_TIMEOUT)
        print(f"[BROWSER_DEBUG] Email từ Copy (trước 'Create random'): '{initial_email}'")

        create_random_button_xpath = "//button[.//span[normalize-space()='Create random']]"
        try:
            WebDriverWait(driver, SELENIUM_GENERAL_TIMEOUT).until(EC.presence_of_element_located((By.XPATH, create_random_button_xpath)))
            create_random_button = WebDriverWait(driver, SELENIUM_GENERAL_TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, create_random_button_xpath)))
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'nearest'});", create_random_button)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", create_random_button)
            print("[BROWSER] Đã thử nhấp nút 'Create random'.")
        except Exception as e_click:
            print(f"[BROWSER_ERROR] Lỗi nghiêm trọng khi tìm/nhấp 'Create random': {e_click}")
            if driver: driver.quit()
            return None, None

        print(f"[BROWSER] Chờ email mới được tạo (tối đa ~{SELENIUM_GENERAL_TIMEOUT}s)...")
        last_polled_email_in_wait = None
        wait_success = False
        for i in range(POLL_ITERATIONS):
            current_email_in_lambda = get_email_from_copy_button_attribute(driver, SELENIUM_GENERAL_TIMEOUT)
            last_polled_email_in_wait = current_email_in_lambda
            print(f"[BROWSER_DEBUG_WAIT] Lần check {i+1}/{POLL_ITERATIONS}: email ban đầu='{initial_email}', email hiện tại='{current_email_in_lambda}'")
            if current_email_in_lambda is not None and current_email_in_lambda != initial_email:
                wait_success = True; break
            time.sleep(POLL_SLEEP_INTERVAL)

        if not wait_success:
            print(f"[BROWSER_ERROR] Timeout ({POLL_ITERATIONS * POLL_SLEEP_INTERVAL:.1f}s) khi chờ email thay đổi.")
            new_email = None
        else:
            new_email = last_polled_email_in_wait
       
        if new_email:
            print(f"[BROWSER] Lấy email mới thành công: {new_email}")
            return new_email, driver
        else:
            print(f"[BROWSER_ERROR] Không thể lấy email mới hợp lệ trong chu kỳ này.")
            print("[BROWSER_INFO] Giả định session có thể đã cũ. Đóng trình duyệt để đăng nhập lại ở lần thử tiếp theo.")
            if driver: driver.quit()
            return None, None
    except Exception as e:
        print(f"[BROWSER_ERROR] Lỗi không mong muốn trong manage_temp_email_session: {e}")
        if driver: driver.quit()
        return None, None

# ----- get_verification_url_from_tempmail (Không đổi logic chính, chỉ timeout) -----
def get_verification_url_from_tempmail(driver, registered_email_address, wait_timeout_seconds):
    print(f"[EMAIL_VERIFY] Cố gắng tìm email xác minh cho {registered_email_address} trong hộp thư tempmail.")
    try:
        inbox_url = "https://tempmail.id.vn/en/inbox"
        print(f"[EMAIL_VERIFY] Điều hướng đến hộp thư: {inbox_url}")
        driver.get(inbox_url)
        time.sleep(wait_timeout_seconds)
        print("[EMAIL_VERIFY] Làm mới trang hộp thư...")
        driver.refresh()
        WebDriverWait(driver, wait_timeout_seconds).until(lambda d: d.execute_script('return document.readyState') == 'complete')

        email_item_clickable_timeout = wait_timeout_seconds * 4
        print(f"[EMAIL_VERIFY] Chờ tối đa {email_item_clickable_timeout}s để email xác minh xuất hiện và có thể nhấp...")
       
        possible_senders_texts = ["fluig", "mockplus", "verification", "verify", "confirm"] # Thêm từ khóa tiêu đề/người gửi
        email_element_to_click = None
        email_items_found_count = 0

        for i in range(int(email_item_clickable_timeout / wait_timeout_seconds)):
            all_email_items_xpath = "//div[contains(@class, 'fi-ta-text') and contains(@class, 'px-3') and contains(@class, 'py-4')]"
            try:
                email_items = driver.find_elements(By.XPATH, all_email_items_xpath)
                email_items_found_count = len(email_items)
                if not email_items:
                    print(f"[EMAIL_VERIFY] Lần check {i+1}: Chưa tìm thấy mục email nào. Đang chờ...")
                    time.sleep(wait_timeout_seconds)
                    driver.refresh()
                    WebDriverWait(driver, wait_timeout_seconds).until(lambda d: d.execute_script('return document.readyState') == 'complete')
                    continue

                print(f"[EMAIL_VERIFY] Lần check {i+1}: Tìm thấy {len(email_items)} mục email. Kiểm tra người gửi/tiêu đề liên quan...")
                for item_index, item in enumerate(email_items): # Ưu tiên email mới nhất (thường ở đầu)
                    item_text_lower = item.text.lower()
                    print(f"[EMAIL_VERIFY_DEBUG] Mục email {item_index} text: {item_text_lower[:100]}")
                    for keyword in possible_senders_texts:
                        if keyword in item_text_lower:
                            print(f"[EMAIL_VERIFY] Tìm thấy mục email có khả năng chứa từ khóa '{keyword}'.")
                            email_element_to_click = item
                            break
                    if email_element_to_click: break
               
                if email_element_to_click: break
                else: # Nếu không khớp từ khóa, thử lấy cái đầu tiên nếu có nhiều hơn 1 và chưa thử
                    if email_items and i > 1 : # Cho email có thời gian load, nếu có nhiều thì lấy cái đầu
                         print("[EMAIL_VERIFY] Không khớp từ khóa cụ thể. Thử nhấp vào mục email đầu tiên.")
                         email_element_to_click = email_items[0]
                         break
               
                if not email_element_to_click and email_items: # Nếu vẫn chưa chọn được và có email
                    print(f"[EMAIL_VERIFY_DEBUG] Lần check {i+1}: Không tìm thấy email khớp từ khóa, sẽ thử lại sau khi chờ.")

            except Exception as e_find_items:
                print(f"[EMAIL_VERIFY_DEBUG] Lỗi khi tìm mục email ở lần {i+1}: {e_find_items}")
           
            if email_element_to_click: break # Thoát nếu đã chọn được email
            print(f"[EMAIL_VERIFY_DEBUG] Chờ {wait_timeout_seconds}s trước khi thử lại làm mới và tìm email.")
            time.sleep(wait_timeout_seconds)
            if i % 2 == 0 : # Làm mới không quá thường xuyên
                driver.refresh()
                WebDriverWait(driver, wait_timeout_seconds).until(lambda d: d.execute_script('return document.readyState') == 'complete')


        if not email_element_to_click and email_items_found_count > 0 : # Nếu vòng lặp kết thúc, vẫn không có từ khóa khớp, nhưng có email -> lấy cái đầu tiên
             print("[EMAIL_VERIFY] Không khớp từ khóa cụ thể sau các lần thử. Chọn mục email đầu tiên trong danh sách.")
             email_element_to_click = driver.find_elements(By.XPATH, all_email_items_xpath)[0]
        elif not email_element_to_click:
            print("[EMAIL_VERIFY_ERROR] Không tìm thấy mục email nào trong hộp thư sau nhiều lần thử.")
            return None
           
        print("[EMAIL_VERIFY] Nhấp vào mục email đã chọn...")
        driver.execute_script("arguments[0].scrollIntoView(true);", email_element_to_click)
        time.sleep(0.2)
        email_element_to_click.click()
       
        verification_link_href = None
        iframe_switched = False
        try:
            print("[EMAIL_VERIFY] Tìm kiếm iframe chứa nội dung email...")
            possible_iframes = driver.find_elements(By.TAG_NAME, "iframe")
            email_iframe_element = None
            if possible_iframes:
                for iframe in possible_iframes: # Tìm iframe có vẻ chứa nội dung email
                    try:
                        driver.switch_to.frame(iframe)
                        # Kiểm tra sự tồn tại của một vài thẻ hay gặp trong email body
                        if driver.find_elements(By.XPATH, "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'verify')]") or \
                           driver.find_elements(By.XPATH, "//p") or driver.find_elements(By.XPATH, "//table"):
                            email_iframe_element = iframe
                            print("[EMAIL_VERIFY_DEBUG] Có vẻ đã tìm thấy iframe chứa nội dung email.")
                            driver.switch_to.default_content() # Chuyển ra để switch lại đúng cách
                            break
                        driver.switch_to.default_content()
                    except: # Bỏ qua iframe không thể switch hoặc không chứa nội dung mong muốn
                        driver.switch_to.default_content()
                        continue
           
            if email_iframe_element:
                print(f"[EMAIL_VERIFY] Chuyển vào iframe email: {email_iframe_element.get_attribute('id') or 'không_có_id'}")
                driver.switch_to.frame(email_iframe_element)
                iframe_switched = True
            else:
                print("[EMAIL_VERIFY] Không tìm thấy iframe email cụ thể, giả định nội dung ở document chính.")

            verification_link_text_parts = ["verify my email", "confirm my email", "activate account", "verify your e-mail", "confirm registration"]
            print(f"[EMAIL_VERIFY] Tìm kiếm liên kết xác minh chứa một trong các cụm từ: {verification_link_text_parts}...")
            link_found = False
            for link_text_part in verification_link_text_parts:
                link_xpath = f"//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{link_text_part.lower()}')]"
                try:
                    verification_anchor = WebDriverWait(driver, wait_timeout_seconds).until(EC.element_to_be_clickable((By.XPATH, link_xpath)))
                    verification_link_href = verification_anchor.get_attribute("href")
                    if verification_link_href and ("http://" in verification_link_href or "https://" in verification_link_href): # Check if it's a valid URL
                        print(f"[EMAIL_VERIFY] Tìm thấy liên kết xác minh với cụm từ '{link_text_part}': {verification_link_href}")
                        link_found = True; break
                    else:
                        print(f"[EMAIL_VERIFY_DEBUG] Tìm thấy thẻ <a> khớp text '{link_text_part}' nhưng href không hợp lệ: '{verification_link_href}'")
                except TimeoutException:
                    print(f"[EMAIL_VERIFY_DEBUG] Liên kết với cụm từ '{link_text_part}' không tìm thấy hoặc không thể nhấp trong {wait_timeout_seconds}s.")
            if not link_found: print(f"[EMAIL_VERIFY_ERROR] Không thể tìm thấy liên kết xác minh nào trong nội dung email.")
        finally:
            if iframe_switched:
                driver.switch_to.default_content()
                print("[EMAIL_VERIFY] Đã chuyển về nội dung mặc định.")
        return verification_link_href
    except Exception as e:
        print(f"[EMAIL_VERIFY_ERROR] Lỗi chung trong get_verification_url_from_tempmail: {e}")
        # import traceback; traceback.print_exc() # Bỏ comment để debug sâu
        return None

# ----- perform_registration_cycle (Đã cập nhật để nhận user_inviter_id) -----
def perform_registration_cycle(email_address, user_inviter_id, driver_instance):
    registration_url = "https://www.fluig.cc/api/regist"
    password = "TnoXef77@#"
    headers = {
        "Host": "www.fluig.cc", "Sec-Ch-Ua-Platform": '"Windows"',
        "Accept-Language": "en-US,en;q=0.9", "Accept": "application/json, text/plain, */*",
        "Sec-Ch-Ua": f'"Chromium";v="{USER_AGENT.split("Chrome/")[1].split(".")[0]}", "Not(A:Brand";v="99", "Google Chrome";v="{USER_AGENT.split("Chrome/")[1].split(".")[0]}"',
        "Content-Type": "application/json", "Sec-Ch-Ua-Mobile": "?0", "User-Agent": USER_AGENT,
        "Origin": "https://www.fluig.cc", "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors", "Sec-Fetch-Dest": "empty",
        "Referer": f"https://www.fluig.cc/sign-up?inviterID={user_inviter_id}", # Sử dụng user_inviter_id
        "Accept-Encoding": "gzip, deflate, br", "Priority": "u=1, i"
    }
    payload = {
        "userName": email_address, "password": password,
        "user": {"name": email_address, "email": email_address, "inviterID": user_inviter_id} # Sử dụng user_inviter_id
    }
    print(f"[*] Cố gắng đăng ký {email_address} với Inviter ID: {user_inviter_id}")
    registration_post_successful = False
    try:
        response_regist = requests.post(registration_url, headers=headers, data=json.dumps(payload), timeout=REQUESTS_TIMEOUT)
        print(f"    Yêu cầu đăng ký đã gửi. Status: {response_regist.status_code}")
        response_regist.raise_for_status()
        print(f"[+] Yêu cầu đăng ký thành công cho {email_address}.")
        registration_post_successful = True
    except requests.exceptions.HTTPError as http_err:
        print(f"[HTTP_ERROR] {http_err.response.status_code} cho {email_address}: {http_err}")
        if http_err.response is not None: print(f"    Nội dung lỗi: {http_err.response.text[:500]}")
    except requests.exceptions.RequestException as e:
        print(f"[REQUEST_ERROR] Lỗi API cho {email_address}: {e}")
   
    if not registration_post_successful: return False

    if driver_instance is None:
        print("[ERROR] Không có session trình duyệt để lấy email xác minh. Bỏ qua bước xác minh.")
        return False
    print("[INFO] Đăng ký POST có vẻ thành công. Cố gắng lấy URL xác minh từ email...")
    print("[INFO] Chờ vài giây để email có thể được gửi từ server...")
    time.sleep(SELENIUM_GENERAL_TIMEOUT * 2.5) # Chờ 5 giây (2.5 * 2s)

    verification_url_from_email = get_verification_url_from_tempmail(driver_instance, email_address, SELENIUM_GENERAL_TIMEOUT)
    if not verification_url_from_email:
        print("[ERROR] Không thể lấy URL xác minh từ email. Không thể hoàn tất đăng ký.")
        return False

    print(f"[*] URL xác minh đã trích xuất: {verification_url_from_email}")
    print(f"[*] Chờ {MAIN_VERIFICATION_DELAY} giây trước khi truy cập URL xác minh...")
    time.sleep(MAIN_VERIFICATION_DELAY)
    print(f"[*] Cố gắng xác minh email bằng yêu cầu GET đến: {verification_url_from_email}")
    try:
        verify_headers = {
            "User-Agent": USER_AGENT, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"https://tempmail.id.vn/en/inbox"
        }
        response_verify = requests.get(verification_url_from_email, headers=verify_headers, timeout=REQUESTS_TIMEOUT, allow_redirects=True)
        print(f"    Yêu cầu GET xác minh đã gửi. URL cuối cùng: {response_verify.url}, Status: {response_verify.status_code}")
        if 200 <= response_verify.status_code < 400:
            print(f"[+] Yêu cầu GET xác minh cho {email_address} có vẻ thành công (Status: {response_verify.status_code}).")
            # print(f"    Nội dung phản hồi (200 ký tự đầu): {response_verify.text[:200]}") # Bỏ comment nếu cần debug
            print(f"[SUCCESS] Chu kỳ có khả năng hoàn thành cho {email_address}")
            return True
        else:
            print(f"[-] Yêu cầu GET xác minh cho {email_address} trả về {response_verify.status_code}.")
            print(f"    Nội dung phản hồi (200 ký tự đầu): {response_verify.text[:200]}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[REQUEST_ERROR] Lỗi API trong quá trình GET xác minh email cho {email_address}: {e}")
        return False

# ----- Cập nhật khối __main__ -----
if __name__ == "__main__":
    print("Chào mừng bạn đến với Tool Tự Động Đăng Ký Fluig!")
    print("--------------------------------------------------")
    print("LƯU Ý: Tool này chỉ nhằm mục đích học tập và tự động hóa quy trình cá nhân.")
    print("Vui lòng sử dụng có trách nhiệm và tuân thủ điều khoản của các trang web liên quan.")
    print("--------------------------------------------------")

    while True:
        user_inviter_id = input("🔗 Vui lòng nhập Inviter ID Fluig của bạn: ").strip()
        if user_inviter_id and user_inviter_id.isdigit(): # Kiểm tra xem có phải là số không
            break
        else:
            print("Inviter ID không hợp lệ. Vui lòng nhập một chuỗi số.")

    while True:
        try:
            months_input_str = input(f"📅 Bạn muốn tool chạy thành công bao nhiêu lần (để nhận 'tháng'): ").strip()
            max_successful_cycles_input = int(months_input_str)
            if max_successful_cycles_input > 0:
                break
            else:
                print("Số lần chạy phải là một số dương. Vui lòng nhập lại.")
        except ValueError:
            print("Vui lòng nhập một số hợp lệ.")

    print(f"\n👍 OK! Tool sẽ sử dụng Inviter ID: {user_inviter_id}")
    print(f"🎯 Mục tiêu: {max_successful_cycles_input} lần đăng ký thành công.")
    print("--------------------------------------------------\n")

    attempt_count = 0
    successful_cycles = 0
    # Giới hạn số lần thử tối đa, ví dụ: gấp 3 lần số lần thành công mong muốn, hoặc ít nhất 5 lần thử.
    max_total_attempts = max(max_successful_cycles_input * 3, max_successful_cycles_input + 5)
    driver_instance = None

    try:
        while successful_cycles < max_successful_cycles_input:
            attempt_count += 1
            if attempt_count > max_total_attempts:
                print(f"\n⚠️ Đã đạt tối đa {max_total_attempts} lượt thử nhưng chỉ thành công {successful_cycles}/{max_successful_cycles_input} lần. Dừng tool.")
                break
           
            print(f"\n--- 🔄 Bắt đầu Lượt thử {attempt_count}/{max_total_attempts} (Mục tiêu: {successful_cycles}/{max_successful_cycles_input} thành công) ---")
           
            new_email, driver_instance = manage_temp_email_session(driver_instance)

            if new_email and driver_instance:
                print(f"[INFO] Sử dụng email: {new_email} để đăng ký Fluig.")
                if perform_registration_cycle(new_email, user_inviter_id, driver_instance):
                    successful_cycles += 1
                    print(f"✅ HOÀN THÀNH THÀNH CÔNG LẦN THỨ {successful_cycles}/{max_successful_cycles_input}!")
                else:
                    print(f"❌ Lượt thử {attempt_count} không thành công (bước đăng ký/xác minh Fluig thất bại).")
            elif not new_email and driver_instance is not None: # Lỗi lấy email nhưng driver vẫn còn
                 print("[ERROR] Không thể lấy email mới, nhưng session trình duyệt có thể vẫn còn. Sẽ thử lại.")
            else: # new_email là None và driver_instance cũng là None (do lỗi nghiêm trọng hoặc chưa khởi tạo)
                print("[ERROR] Không thể lấy email mới (session trình duyệt có thể đã đóng). Bỏ qua lượt thử này.")
           
            if successful_cycles >= max_successful_cycles_input:
                print(f"\n🎉🎉🎉 ĐÃ HOÀN THÀNH MỤC TIÊU {max_successful_cycles_input} LẦN ĐĂNG KÝ THÀNH CÔNG! 🎉🎉🎉")
                break # Thoát vòng lặp chính

            if successful_cycles < max_successful_cycles_input: # Chỉ in nếu chưa đạt mục tiêu
                 print(f"--- Chuẩn bị cho lượt thử tiếp theo... ---")
                 if not new_email : # Nếu không lấy được email, đợi lâu hơn một chút
                    print("[*] Chờ 10 giây trước khi thử lại...")
                    time.sleep(10)
                 else: # Nếu thành công hoặc thất bại ở bước Fluig, đợi ngắn hơn
                    time.sleep(2)


    except KeyboardInterrupt:
        print("\n[INFO] Script bị dừng bởi người dùng (Ctrl+C).")
    except Exception as e_main:
        print(f"[FATAL_ERROR] Lỗi không mong muốn trong vòng lặp chính: {e_main}")
        import traceback
        traceback.print_exc()
    finally:
        if driver_instance:
            print("\n[INFO] Đóng session trình duyệt khi kết thúc/thoát script.")
            driver_instance.quit()

    print(f"\n--- KẾT THÚC SCRIPT ---")
    print(f"Tổng cộng: {successful_cycles} lần đăng ký thành công trên {attempt_count} lượt thử (mục tiêu: {max_successful_cycles_input}).")
  
