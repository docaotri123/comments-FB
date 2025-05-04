import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

COOKIE_FILE = 'cookies_tri_do.json'

def random_delay(min_s=3, max_s=6):
    time.sleep(random.uniform(min_s, max_s))

def save_cookies(driver, path):
    with open(path, 'w', encoding='utf-8') as file:
        json.dump(driver.get_cookies(), file, ensure_ascii=False)
    print("🍪 Đã lưu cookies thành công.")

def load_cookies(driver, path):
    with open(path, 'r', encoding='utf-8') as file:
        cookies = json.load(file)
        for cookie in cookies:
            if 'sameSite' in cookie:
                del cookie['sameSite']
            driver.add_cookie(cookie)
    print("🔐 Đã nạp cookies thành công.")

# Setup Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) as driver:
    config = json.load(open('config.json', 'r', encoding='utf-8'))
    post_links = config['posts2']  # Chứa danh sách các link bài viết

    driver.get("https://www.facebook.com/")
    time.sleep(5)

    if not os.path.exists(COOKIE_FILE):
        input("🔓 Vui lòng đăng nhập Facebook thủ công, rồi nhấn ENTER để lưu cookies...")
        save_cookies(driver, COOKIE_FILE)
    else:
        print(f"... Load cookie")
        load_cookies(driver, COOKIE_FILE)
        driver.get("https://www.facebook.com/")
        time.sleep(5)

    input("🔓 Chọn account, rồi nhấn ENTER để tiếp tục...")

    for index, link in enumerate(post_links):
        print(f"\n➡️ Đang like bài viết: {link}")
        try:
            driver.get(link)
            time.sleep(6)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # Tìm nút Like (có thể thay đổi tùy UI Facebook)
            like_buttons = driver.find_elements(By.XPATH, '//div[@aria-label="Thích" or @aria-label="Like"]')

            if like_buttons:
                for btn in like_buttons:
                    try:
                        btn.click()
                        print(f"👍 Đã like bài viết {index + 1}")
                        break
                    except:
                        continue
            else:
                print("❌ Không tìm thấy nút Like.")

            time.sleep(3)
            if index % 5 == 4:
                print("😴 Nghỉ 20s sau mỗi 5 bài viết...")
                time.sleep(20)

        except Exception as e:
            print(f"❌ Lỗi khi xử lý bài viết: {e}")

        print("⏳ Chờ trước khi qua bài tiếp theo...\n")
        time.sleep(5)

    print("🎉 Hoàn tất việc Like tất cả bài viết!")
    time.sleep(3)
