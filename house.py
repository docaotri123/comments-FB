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

def delete_latest_comment(driver, comment_text):
    try:
        # Tìm tất cả đoạn bình luận chứa nội dung vừa comment
        comment_blocks = driver.find_elements(By.XPATH, f'//div[@dir="auto" and contains(text(), "{comment_text}")]')

        if comment_blocks:
            # Giả sử bình luận mới nhất là cái đầu tiên tìm thấy
            comment_div = comment_blocks[0]
            outer_div = comment_div.find_element(By.XPATH, "./ancestor::div[contains(@class, 'x1rg5ohu')][1]")

            # Hover để hiện dấu ba chấm
            ActionChains(driver).move_to_element(outer_div).perform()
            time.sleep(1)

            # Tìm nút "Hành động với bình luận này"
            more_btn = outer_div.find_element(By.XPATH, './/div[@aria-label="Hành động với bình luận này"]')
            more_btn.click()
            time.sleep(1)

            # Nhấn nút "Xóa"
            delete_btn = driver.find_element(By.XPATH, '//span[text()="Xóa"]')
            delete_btn.click()
            time.sleep(1)

            # Xác nhận popup "Bạn có chắc chắn muốn xóa bình luận này không?"
            confirm_btn = driver.find_element(By.XPATH, '//div[@aria-label="Xóa" or .//span[text()="Xóa"]]')
            confirm_btn.click()
            print("🗑️ Đã xóa bình luận vừa đăng.")

        else:
            print("❗ Không tìm thấy bình luận vừa đăng.")

    except Exception as e:
        print(f"❌ Lỗi khi xóa bình luận: {e}")


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

            # Tìm ô nhập bình luận
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
                    print(f"✅ Đã comment {i+1}/{qtd_comment}: {random_comment}")
                    time.sleep(3)  # Chờ Facebook render bình luận

                    # delete_latest_comment(driver, random_comment)

                    random_delay(4,10)

            else:
                print("❌ Không tìm thấy ô bình luận.")

        except Exception as e:
            print(f"❌ Lỗi khi xử lý bài viết: {e}")

        print("⏳ Chờ trước khi qua bài tiếp theo...\n")
        time.sleep(5)

    print("🎉 Hoàn tất tất cả bài viết!")
    time.sleep(3)
