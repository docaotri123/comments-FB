import random
import json
import time
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

COOKIE_FILE = 'cookies_binh_le.json'

class GroupCommentBot:
    def __init__(self):
        self.driver = None
        self.config = {}
        self.stats = {
            'total_posts_seen': 0,
            'total_posts_analyzed': 0,
            'customer_posts': 0,
            'service_posts': 0,
            'comments_made': 0,
            'errors': 0,
            'scroll_time': 0
        }
        self.processed_post_links = set()  # Tránh xử lý trùng
        
    def remove_non_bmp(self, text):
        """Loại bỏ ký tự không hỗ trợ BMP"""
        return ''.join(c for c in text if ord(c) <= 0xFFFF)
        
    def setup_driver(self):
        """Khởi tạo Chrome driver"""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        # Thêm options để scroll mượt hơn
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=options
        )
        
    def load_config(self):
        """Load cấu hình từ file"""
        try:
            with open('group_config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            print("✅ Đã load config thành công")
            
            # Kiểm tra config cần thiết
            required_keys = ['groups', 'scroll_minutes_per_group', 'customer_keywords', 'service_keywords', 'marketing_comments']
            missing_keys = [key for key in required_keys if key not in self.config]
            if missing_keys:
                print(f"⚠️ Config thiếu các key: {missing_keys}")
                print("Vui lòng cập nhật file group_config.json")
                return False
            return True
        except FileNotFoundError:
            print("❌ Không tìm thấy file group_config.json")
            print("Vui lòng tạo file config với các key cần thiết!")
            return False
            
    def save_cookies(self):
        """Lưu cookies"""
        with open(COOKIE_FILE, 'w', encoding='utf-8') as file:
            json.dump(self.driver.get_cookies(), file, ensure_ascii=False)
        print("🍪 Đã lưu cookies")
        
    def load_cookies(self):
        """Load cookies"""
        if os.path.exists(COOKIE_FILE):
            with open(COOKIE_FILE, 'r', encoding='utf-8') as file:
                cookies = json.load(file)
                for cookie in cookies:
                    if 'sameSite' in cookie:
                        del cookie['sameSite']
                    self.driver.add_cookie(cookie)
            print("🔐 Đã load cookies")
            return True
        return False
        
    def login_facebook(self):
        """Đăng nhập Facebook"""
        print("🌐 Đang truy cập Facebook...")
        self.driver.get("https://www.facebook.com/")
        time.sleep(5)
        
        if not self.load_cookies():
            input("🔓 Vui lòng đăng nhập Facebook thủ công, rồi nhấn ENTER...")
            self.save_cookies()
        else:
            self.driver.refresh()
            time.sleep(5)
            
    def smart_scroll(self, pixels=300, duration=0.5):
        """Scroll từ từ và mượt mà"""
        current_position = self.driver.execute_script("return window.pageYOffset;")
        target_position = current_position + pixels
        
        steps = 10
        step_size = pixels / steps
        step_duration = duration / steps
        
        for i in range(steps):
            new_position = current_position + (step_size * (i + 1))
            self.driver.execute_script(f"window.scrollTo(0, {new_position});")
            time.sleep(step_duration)
            
    def get_posts_in_viewport(self):
        """Lấy các bài viết hiện tại trong viewport"""
        posts = []
        try:
            # Nhiều selector để tìm bài viết
            post_selectors = [
                "//div[@data-pagelet='FeedUnit_0']//div[@role='article']",
                "//div[contains(@class,'x1yztbdb x1n2onr6 xh8yej3 x1ja2u2z')]",
                "//div[@data-testid='story-subtitle']//ancestor::div[@role='article']",
                "//div[contains(@class,'feed-story')]",
                "//article",
                "//div[contains(@class,'userContentWrapper')]"
            ]
            
            for selector in post_selectors:
                try:
                    post_elements = self.driver.find_elements(By.XPATH, selector)
                    if post_elements:
                        break
                except:
                    continue
            
            for post in post_elements:
                try:
                    # Kiểm tra xem post có trong viewport không
                    location = post.location
                    size = post.size
                    window_height = self.driver.execute_script("return window.innerHeight;")
                    scroll_position = self.driver.execute_script("return window.pageYOffset;")
                    
                    # Post phải hiện trên màn hình
                    if (location['y'] >= scroll_position - 100 and 
                        location['y'] <= scroll_position + window_height + 100):
                        
                        # Lấy text của bài viết
                        text_selectors = [
                            ".//div[@data-ad-preview='message']//span",
                            ".//div[contains(@class,'x11i5rnm xat24cr x1mh8g0r x1vvkbs')]",
                            ".//div[contains(@class,'userContent')]",
                            ".//span[contains(@class,'x193iq5w')]",
                            ".//div[@data-testid='post_message']//span"
                        ]
                        
                        post_text = ""
                        for text_sel in text_selectors:
                            try:
                                text_elem = post.find_element(By.XPATH, text_sel)
                                post_text = text_elem.text
                                if post_text and len(post_text.strip()) > 10:
                                    break
                            except:
                                continue
                        
                        if not post_text:
                            continue
                            
                        # Lấy link bài viết
                        link_selectors = [
                            ".//a[contains(@href,'/groups/') and contains(@href,'/posts/')]",
                            ".//a[contains(@href,'/posts/')]",
                            ".//a[contains(@href,'/permalink/')]"
                        ]
                        
                        post_link = None
                        for link_sel in link_selectors:
                            try:
                                link_elem = post.find_element(By.XPATH, link_sel)
                                post_link = link_elem.get_attribute('href')
                                if post_link:
                                    break
                            except:
                                continue
                        
                        # Nếu không có link, tạo unique ID từ text
                        if not post_link:
                            post_link = f"no_link_{hash(post_text[:100])}"
                        
                        # Kiểm tra đã xử lý chưa
                        if post_link not in self.processed_post_links:
                            posts.append({
                                'text': post_text,
                                'link': post_link,
                                'element': post
                            })
                            
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Lỗi khi lấy posts: {e}")
            
        return posts

    def scroll_and_process_posts_by_time(self, group_url, scroll_minutes):
        """Scroll và xử lý bài viết theo thời gian"""
        print(f"📜 Đang scroll group: {group_url}")
        print(f"⏰ Thời gian scroll: {scroll_minutes} phút")
        
        self.driver.get(group_url)
        time.sleep(10)
        
        start_time = time.time()
        end_time = start_time + (scroll_minutes * 60)
        
        last_scroll_position = 0
        stuck_count = 0
        scroll_speed = self.config.get('scroll_speed', 'medium')  # slow, medium, fast
        
        # Cấu hình tốc độ scroll
        if scroll_speed == 'slow':
            scroll_pixels = 200
            scroll_delay = [2, 4]
            batch_delay = 3
        elif scroll_speed == 'fast':
            scroll_pixels = 500
            scroll_delay = [0.5, 1.5]
            batch_delay = 1
        else:  # medium
            scroll_pixels = 300
            scroll_delay = [1, 2.5]
            batch_delay = 2
        
        print(f"🎛️ Tốc độ scroll: {scroll_speed} ({scroll_pixels}px mỗi lần)")
        
        while time.time() < end_time:
            try:
                # Lấy posts hiện tại trên màn hình
                current_posts = self.get_posts_in_viewport()
                
                print(f"👀 Tìm thấy {len(current_posts)} bài viết mới trên màn hình")
                
                # Xử lý từng bài viết
                for post in current_posts:
                    if time.time() >= end_time:
                        break
                        
                    self.process_single_post(post)
                    
                    # Đánh dấu đã xử lý
                    self.processed_post_links.add(post['link'])
                
                # Scroll xuống một chút
                self.smart_scroll(scroll_pixels, 0.8)
                
                # Kiểm tra xem có scroll được không
                current_position = self.driver.execute_script("return window.pageYOffset;")
                if current_position == last_scroll_position:
                    stuck_count += 1
                    if stuck_count >= 3:
                        print("📍 Đã scroll tới cuối, chuyển sang load thêm...")
                        # Thử click "Xem thêm" nếu có
                        try:
                            see_more_buttons = self.driver.find_elements(
                                By.XPATH, 
                                "//div[contains(text(),'Xem thêm') or contains(text(),'See more') or contains(text(),'Load more')]"
                            )
                            if see_more_buttons:
                                see_more_buttons[0].click()
                                time.sleep(3)
                                stuck_count = 0
                            else:
                                # Scroll xuống mạnh hơn
                                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                                time.sleep(2)
                        except:
                            pass
                else:
                    stuck_count = 0
                    
                last_scroll_position = current_position
                
                # Delay giữa các lần scroll
                delay_time = random.uniform(scroll_delay[0], scroll_delay[1])
                time.sleep(delay_time)
                
                # Hiển thị tiến độ
                elapsed = time.time() - start_time
                remaining = (end_time - time.time()) / 60
                print(f"⏳ Đã scroll {elapsed/60:.1f}/{scroll_minutes} phút, còn {remaining:.1f} phút")
                
            except Exception as e:
                print(f"⚠️ Lỗi trong quá trình scroll: {e}")
                self.stats['errors'] += 1
                time.sleep(2)
        
        self.stats['scroll_time'] += scroll_minutes
        print(f"✅ Hoàn thành scroll {scroll_minutes} phút cho group")

    def process_single_post(self, post):
        """Xử lý một bài viết"""
        self.stats['total_posts_seen'] += 1
        
        # Kiểm tra độ dài tối thiểu
        if len(post['text'].strip()) < 20:
            return
            
        self.stats['total_posts_analyzed'] += 1
        
        print(f"\n📝 Bài viết #{self.stats['total_posts_analyzed']}")
        print(f"Nội dung: {post['text'][:100]}...")
        
        # Phân tích loại bài viết
        post_type = self.analyze_post_type(post['text'])
        
        if post_type == 'skip':
            print("⏭️ Bỏ qua (admin/mod post)")
            return
        elif post_type == 'service':
            print("🏢 Bài viết dịch vụ - Bỏ qua")
            self.stats['service_posts'] += 1
            return
        elif post_type == 'customer':
            print("👤 Bài viết khách hàng - Sẽ comment")
            self.stats['customer_posts'] += 1
            
            # Random xem có comment không (để tránh comment quá nhiều)
            comment_rate = self.config.get('comment_probability', 0.7)  # 70% chance
            if random.random() < comment_rate:
                # Chọn comment ngẫu nhiên
                comment_text = random.choice(self.config.get('marketing_comments', []))
                
                # Thực hiện comment
                if self.make_comment(post['element'], comment_text):
                    self.stats['comments_made'] += 1
                    
                    # Delay sau khi comment
                    delay_range = self.config.get('comment_delay', [5, 12])
                    delay_time = random.uniform(delay_range[0], delay_range[1])
                    print(f"😴 Nghỉ {delay_time:.1f}s sau comment...")
                    time.sleep(delay_time)
                else:
                    self.stats['errors'] += 1
            else:
                print("🎲 Skip comment (random)")
        else:
            print("❓ Không xác định được loại bài viết")

    def _normalize_text(self, text):
        """Chuẩn hóa text để xử lý viết tắt và lỗi chính tả"""
        text = text.lower().strip()
        
        # Xử lý viết tắt phổ biến
        abbreviations = {
            r'\bcv\b': 'công việc',
            r'\bsv\b': 'sinh viên', 
            r'\ba/c\b': 'anh chị',
            r'\btphcm\b': 'thành phố hồ chí minh',
            r'\bhn\b': 'hà nội',
            r'\bdc\b': 'được',
            r'\bk\b': 'không',
            r'\bko\b': 'không',
            r'\bkhg\b': 'không',
            r'\bvs\b': 'với',
            r'\bmk\b': 'mình',
            r'\bmn\b': 'mọi người',
            r'\bib\b': 'inbox',
            r'\bsdt\b': 'số điện thoại',
            r'\blh\b': 'liên hệ',
            r'\bpt\b': 'phòng trọ',
            r'\bcc\b': 'các bạn',
            r'\bnv\b': 'nhân viên',
            r'\bdt\b': 'điện thoại'
        }
        
        for abbr, full in abbreviations.items():
            text = re.sub(abbr, full, text)
        
        # Xử lý lỗi gõ phổ biến
        typos = {
            'chuyenr': 'chuyển',
            'chuyen': 'chuyển', 
            'tim': 'tìm',
            'can': 'cần',
            'dich vu': 'dịch vụ',
            'don vi': 'đơn vị',
            'bao gia': 'báo giá',
            'tu van': 'tư vấn',
            'giup do': 'giúp đỡ',
            'chuyen nha': 'chuyển nhà',
            'chuyen tro': 'chuyển trọ'
        }
        
        for typo, correct in typos.items():
            text = text.replace(typo, correct)
        
        return text

    def _calculate_keyword_score(self, text, keywords):
        """Tính điểm từ khóa có trọng số"""
        score = 0
        found_keywords = []
        
        for keyword in keywords:
            if keyword in text:
                found_keywords.append(keyword)
                # Từ khóa mạnh có điểm cao hơn
                if keyword in ['cần chuyển', 'tìm dịch vụ', 'nhận chuyển', 'hotline', 'zalo', 'cần gấp']:
                    score += 3
                elif keyword in ['cần tìm', 'ai có', 'giúp đỡ', 'tư vấn', 'liên hệ']:
                    score += 2
                else:
                    score += 1
        
        return score, found_keywords

    def _analyze_context(self, text):
        """Phân tích ngữ cảnh để tăng độ chính xác"""
        bonus = {'customer': 0, 'service': 0}
        
        # Ngữ cảnh khách hàng
        customer_contexts = [
            r'\bmình\s+(đang|sắp|cần|muốn)\s+(chuyển|dọn)\b',
            r'\b(từ|về)\s+\w+\s+(quận|huyện|phường)\b',  # Địa chỉ cụ thể
            r'\b(tầng|lầu)\s+\d+\b',  # Tầng lầu
            r'\b(thang\s+máy|cầu\s+thang\s+bộ)\b',
            r'\b(tủ\s+lạnh|máy\s+giặt|điều\s+hòa)\s+\d*\w*\b',  # Đồ đạc cụ thể
            r'\b(nhiều\s+đồ|ít\s+đồ|đồ\s+lặt\s+vặt)\b',
            r'\b(phòng\s+trọ|căn\s+hộ|nhà\s+trọ)\b',
            r'\bcần\s+(thuê|tìm)\s+xe\b'
        ]
        
        for pattern in customer_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                bonus['customer'] += 2
        
        # Ngữ cảnh dịch vụ
        service_contexts = [
            r'\b(phục\s+vụ|hỗ\s+trợ)\s+(24/7|toàn\s+quốc|tphcm)\b',
            r'\b(đội\s+ngũ|nhân\s+viên)\s+(kinh\s+nghiệm|chuyên\s+nghiệp)\b',
            r'\b(xe\s+tải|xe\s+\d+\s+tấn)\b',
            r'\bgiá\s+(rẻ|tốt|hợp\s+lý|cạnh\s+tranh)\b',
            r'\b(cam\s+kết|bảo\s+hành|bồi\s+thường)\b',
            r'\btrọn\s+gói\b',
            r'\b0[0-9]{8,9}\b'  # Số điện thoại
        ]
        
        for pattern in service_contexts:
            if re.search(pattern, text, re.IGNORECASE):
                bonus['service'] += 2
        
        return bonus
        
    def analyze_post_type(self, post_text):
        """Phân tích loại bài viết thông minh với xử lý viết tắt và lỗi chính tả"""
        if not post_text or len(post_text.strip()) < 10:
            return 'skip'
        
        # Chuẩn hóa text
        normalized_text = self._normalize_text(post_text)
        
        # Kiểm tra từ khóa nên bỏ qua trước
        skip_keywords = self.config.get('skip_keywords', [])
        if any(keyword in normalized_text for keyword in skip_keywords):
            return 'skip'

        # --- Kiểm tra dấu hiệu dịch vụ mạnh ---
        strong_service_patterns = [
            r'\b0[0-9]{8,9}\b',                    # Số điện thoại
            r'\b(zalo|viber|telegram)\s*[:=]?\s*0[0-9]{8,9}\b',  # App + số
            r'\b(hotline|liên hệ|gọi)\s*[:=]?\s*0[0-9]{8,9}\b',
            r'\b(nhận\s+chuyển|nhận\s+làm|nhận\s+tháo)\b',
            r'\b(team\s+chúng\s+tôi|công\s+ty\s+chúng\s+tôi)\b',
            r'\b(cam\s+kết|bảo\s+hành|bồi\s+thường)\s+\d+%?\b',
            r'\b(giá\s+sinh\s+viên|ưu\s+đãi\s+sinh\s+viên)\b',
            r'\btrọn\s+gói\b.*\b(tháo|lắp|đóng|bọc)\b',
            r'\b24/7\b',
            r'\b(inbox|ib|chat|nhắn\s+tin)\s+(mình|em|anh|chị)\b'
        ]
        
        for pattern in strong_service_patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                return 'service'

        # --- Kiểm tra dấu hiệu khách hàng mạnh ---
        strong_customer_patterns = [
            r'\b(cần|tìm|thuê)\s+(dịch\s+vụ|đơn\s+vị|team|bên|ai)\b',
            r'\b(có\s+ai|ai\s+có|ai\s+biết|ai\s+làm)\b',
            r'\b(giúp\s+đỡ|tư\s+vấn|báo\s+giá|help)\b.*\b(mình|em|tôi)\b',
            r'\b(cần\s+gấp|khẩn\s+cấp|urgent|tối\s+nay|mai)\b',
            r'\bmình\s+(cần|tìm|muốn|sắp)\b',
            r'\b(nhờ\s+mọi\s+người|cho\s+hỏi|xin\s+tư\s+vấn)\b',
            r'\b(chuyển\s+từ|chuyển\s+về|dọn\s+từ|dọn\s+về)\b.*\b(quận|huyện|phường)\b'
        ]
        
        for pattern in strong_customer_patterns:
            if re.search(pattern, normalized_text, re.IGNORECASE):
                # Kiểm tra thêm xem có phải tự quảng cáo không
                if not re.search(r'\b(chúng\s+tôi|team\s+mình|công\s+ty)\b', normalized_text, re.IGNORECASE):
                    return 'customer'

        # --- Đếm điểm từ khóa ---
        customer_keywords = self.config.get('customer_keywords', [])
        service_keywords = self.config.get('service_keywords', [])

        customer_score, customer_found = self._calculate_keyword_score(normalized_text, customer_keywords)
        service_score, service_found = self._calculate_keyword_score(normalized_text, service_keywords)

        # --- Kiểm tra ngữ cảnh ---
        context_bonus = self._analyze_context(normalized_text)
        customer_score += context_bonus['customer']
        service_score += context_bonus['service']

        # Debug info
        print(f"  🔍 Customer score: {customer_score} (keywords: {customer_found[:3]})")
        print(f"  🔍 Service score: {service_score} (keywords: {service_found[:3]})")

        # --- Phân loại cuối cùng ---
        if customer_score >= 4 and service_score <= 1:
            return 'customer'
        elif service_score >= 4 and customer_score <= 1:
            return 'service'
        elif customer_score > service_score and customer_score >= 3:
            return 'customer'
        elif service_score > customer_score and service_score >= 3:
            return 'service'
        else:
            return 'unknown'
            
    def find_comment_box(self, post_element):
        """Tìm comment box trong bài viết"""
        comment_xpaths = [
            './/div[@role="textbox" and @contenteditable="true"]',
            './/div[@data-lexical-editor="true"]',
            './/div[contains(@class,"notranslate")][@contenteditable="true"]',
            './/div[@contenteditable="true" and @aria-label]',
            './/textarea[@placeholder]'
        ]
        
        for xpath in comment_xpaths:
            try:
                comment_box = post_element.find_element(By.XPATH, xpath)
                return comment_box
            except:
                continue
                
        return None
        
    def make_comment(self, post_element, comment_text):
        """Thực hiện comment"""
        try:
            # Scroll đến bài viết
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", post_element)
            time.sleep(2)
            
            # Tìm comment box
            comment_box = self.find_comment_box(post_element)
            
            if not comment_box:
                print("❌ Không tìm thấy comment box")
                return False
                
            # Click vào comment box
            ActionChains(self.driver).move_to_element(comment_box).click().perform()
            time.sleep(2)
            
            # Nhập comment (loại bỏ ký tự đặc biệt)
            safe_comment = self.remove_non_bmp(comment_text)
            comment_box.clear()
            
            # Gõ từ từ để tự nhiên hơn
            for char in safe_comment:
                comment_box.send_keys(char)
                time.sleep(random.uniform(0.05, 0.15))
            
            time.sleep(1)
            
            # Enter để post
            comment_box.send_keys(Keys.ENTER)
            
            print(f"✅ Đã comment: {safe_comment[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi khi comment: {e}")
            return False
            
    def process_group(self, group_url):
        """Xử lý một group theo thời gian"""
        print(f"\n🎯 Đang xử lý group: {group_url}")
        
        scroll_minutes = self.config.get('scroll_minutes_per_group', 5s)
        self.scroll_and_process_posts_by_time(group_url, scroll_minutes)
            
    def run(self):
        """Chạy chương trình chính"""
        print("🚀 Bắt đầu Auto Comment Groups")
        
        try:
            # Load config
            self.load_config()
            
            # Setup driver
            self.setup_driver()
            
            # Login Facebook
            self.login_facebook()

            input("🔓 Chọn account, rồi nhấn ENTER...")
            
            # Xử lý từng group
            groups = self.config.get('groups', [])
            
            for group_url in groups:
                try:
                    self.process_group(group_url)
                    
                    # Nghỉ giữa các group
                    print("😴 Nghỉ 30s trước khi chuyển group tiếp theo...")
                    time.sleep(30)
                    
                except Exception as e:
                    print(f"❌ Lỗi khi xử lý group {group_url}: {e}")
                    self.stats['errors'] += 1
                    
            # In thống kê
            self.print_stats()
            
        except Exception as e:
            print(f"❌ Lỗi chung: {e}")
            
        finally:
            if self.driver:
                input("Nhấn ENTER để đóng browser...")
                self.driver.quit()
                
    def print_stats(self):
        """In thống kê"""
        print("\n" + "="*50)
        print("📊 THỐNG KÊ HOẠT ĐỘNG")
        print("="*50)
        print(f"📝 Tổng bài viết đã xem: {self.stats['total_posts']}")
        print(f"👤 Bài viết khách hàng: {self.stats['customer_posts']}")
        print(f"🏢 Bài viết dịch vụ: {self.stats['service_posts']}")
        print(f"💬 Đã comment: {self.stats['comments_made']}")
        print(f"❌ Lỗi: {self.stats['errors']}")
        print("="*50)

if __name__ == "__main__":
    bot = GroupCommentBot()
    bot.run()