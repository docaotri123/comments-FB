import random
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

def get_random_question(questions):
    return random.choice(questions)

def random_delay(min_s=3, max_s=6):
    time.sleep(random.uniform(min_s, max_s))

# Cài đặt Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

def like_post(driver):
    try:
        # Scroll để chắc chắn nút Like hiện ra
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)

        like_button = driver.find_element(By.XPATH, '//div[@aria-label="Thích" or @aria-label="Like"]')
        if like_button:
            like_button.click()
            print("👍 Đã like bài viết.")
            time.sleep(2)
    except Exception as e:
        print(f"❗ Không thể like bài viết: {e}")



with webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options) as driver:
    # Đọc cấu hình
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    post_links = config['posts']
    qtd_comment = config['qtd_comment']
    questions = config['questions']

    # Đăng nhập thủ công
    driver.get("https://www.facebook.com/")
    input("✅ Sau khi đăng nhập thủ công, nhấn ENTER để tiếp tục...")

    for link in post_links:
        print(f"\n➡️ Đang comment vào: {link}")
        try:
            driver.get(link)
            time.sleep(6)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            like_post(driver)

        except Exception as e:
            print(f"❌ Lỗi khi xử lý bài viết: {e}")

        print("⏳ Chờ trước khi qua bài tiếp theo...\n")
        time.sleep(5)

    print("🎉 Hoàn tất tất cả bài viết!")
    time.sleep(3)
