import random
import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

COOKIE_FILE = 'cookies_tri_do.json'

def get_random_question(questions):
    return random.choice(questions)

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
                del cookie['sameSite']  # Fix cho ChromeDriver mới
            driver.add_cookie(cookie)
    print("🔐 Đã nạp cookies thành công.")

# Setup Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) as driver:
    config = json.load(open('config.json', 'r', encoding='utf-8'))

    post_links = config['posts2']
    qtd_comment = config['qtd_comment']
    questions = config['questions2']
    count = 0

    driver.get("https://www.facebook.com/")
    time.sleep(5)

    # Nếu chưa có cookies, cho người dùng đăng nhập thủ công
    if not os.path.exists(COOKIE_FILE):
        input("🔓 Vui lòng đăng nhập Facebook thủ công, rồi nhấn ENTER để lưu cookies...")
        save_cookies(driver, COOKIE_FILE)
    else:
        print(f"... Load cookie")
        load_cookies(driver, COOKIE_FILE)
        driver.get("https://www.facebook.com/")
        time.sleep(5)

    input("🔓 Chon account, rồi nhấn ENTER để lưu cookies...")

    for link in post_links:
        print(f"\n➡️ Đang comment vào: {link}")
        try:
            count += 1
            driver.get(link)
            time.sleep(6)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            xpaths = [
                '//div[@role="textbox" and @contenteditable="true"]',
                '//div[@data-lexical-editor="true"]',
            ]

            comment_box = None
            for xpath in xpaths:
                try:
                    comment_box = driver.find_element(By.XPATH, xpath)
                    if comment_box:
                        break
                except:
                    continue

            if comment_box:
                driver.execute_script("arguments[0].scrollIntoView(true);", comment_box)
                time.sleep(1)
                ActionChains(driver).move_to_element(comment_box).click().perform()

                for i in range(qtd_comment):
                    random_comment = get_random_question(questions)
                    comment_box.send_keys(random_comment)
                    time.sleep(1)
                    comment_box.send_keys(Keys.ENTER)
                    print(f"✅ Đã comment {count}/{qtd_comment}: {random_comment}")
                    time.sleep(3)

                    random_delay(5, 15)

                    if count % 5 == 4:
                        print("😴 Nghỉ dài 20s sau mỗi 5 comment...")
                        random_delay(8, 20)
            else:
                print("❌ Không tìm thấy ô bình luận.")
        except Exception as e:
            print(f"❌ Lỗi khi xử lý bài viết: {e}")
        print("⏳ Chờ trước khi qua bài tiếp theo...\n")
        time.sleep(5)

    print("🎉 Hoàn tất tất cả bài viết!")
    time.sleep(3)
