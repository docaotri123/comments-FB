import random
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver


def load_config(path='config.json'):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_random_question(questions):
    return random.choice(questions)


def random_delay(min_s=3, max_s=6):
    time.sleep(random.uniform(min_s, max_s))


def login_facebook(driver):
    driver.get("https://www.facebook.com/")
    input("✅ Đăng nhập xong, nhấn ENTER để tiếp tục...")


def scroll_page(driver, delay=3):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(delay)


def find_post_by_author(driver, author_name):
    posts = driver.find_elements(By.XPATH, '//div[@role="article"]')
    for post in posts:
        try:
            author = post.find_element(By.XPATH, './/strong/span').text
            if author_name.lower() in author.lower():
                return post
        except:
            continue
    return None


def find_comment_box(post):
    try:
        return post.find_element(By.XPATH, './/div[@role="textbox" and @contenteditable="true"]')
    except:
        return None


def comment_on_post(driver, post, questions, qtd_comment):
    comment_box = find_comment_box(post)

    if not comment_box:
        print("❌ Không tìm thấy ô bình luận.")
        return

    driver.execute_script("arguments[0].scrollIntoView(true);", comment_box)
    time.sleep(1)
    ActionChains(driver).move_to_element(comment_box).click().perform()

    for i in range(qtd_comment):
        random_comment = get_random_question(questions)
        comment_box.send_keys(random_comment)
        time.sleep(1)
        comment_box.send_keys(Keys.ENTER)
        print(f"✅ Đã comment {i+1}/{qtd_comment}: {random_comment}")
        time.sleep(3)

        random_delay(5, 15)

        if i % 5 == 4:
            print("😴 Nghỉ dài sau mỗi 5 comment...")
            random_delay(10, 20)


def main():
    config = load_config()
    driver = get_driver()

    try:
        login_facebook(driver)

        for link in config['posts2']:
            print(f"\n➡️ Đang truy cập link: {link}")
            driver.get(link)
            time.sleep(6)
            scroll_page(driver)

            post = find_post_by_author(driver, "Binh Lê")

            if post:
                print("✅ Tìm thấy bài viết của Binh Lê.")
                comment_on_post(driver, post, config['questions2'], config['qtd_comment'])
            else:
                print("❌ Không tìm thấy bài viết của Binh Lê.")

            print("⏳ Chờ trước khi qua bài tiếp theo...\n")
            time.sleep(5)

        print("🎉 Hoàn tất tất cả bài viết!")
        time.sleep(3)

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
