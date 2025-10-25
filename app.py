#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - Firefox Edition
MEMORY OPTIMIZED VERSION with Complete Error Handling
"""

import os
import time
import random
import logging
import re
import requests
import threading
import base64
import json
import subprocess
import gc
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from bs4 import BeautifulSoup

# ==================== CONFIGURATION ====================
CONFIG = {
    'email': "jiocloud90@gmail.com",
    'password': "@Sd2007123",
    'base_delay': 2,
    'random_delay': True,
    'min_delay': 1,
    'max_delay': 3,
    'telegram_token': "8225236307:AAF9Y2-CM7TlLDFm2rcTVY6f3SA75j0DFI8",
    'credit_check_interval': 1800,
    'max_consecutive_failures': 15,
    'refresh_page_after_failures': 5,
    'send_screenshot_on_error': True,
    'screenshot_cooldown_minutes': 1,
    'cookies_wait_timeout': 222,  # 5 minutes
}

class FirefoxSymbolGameSolver:
    def __init__(self):
        self.driver = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        self.waiting_for_cookies = False
        
        # State Management
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'last_credits': 'Unknown',
            'monitoring_active': False,
            'is_logged_in': False,
            'consecutive_fails': 0,
            'last_error_screenshot': 0,
            'daily_target': None,
            'today_start_count': 0,
            'reset_processed': False,
            'last_leaderboard_check': 0,
        }
        
        self.solver_thread = None
        self.monitoring_thread = None
        self.leaderboard_thread = None
        self.setup_logging()
        self.setup_telegram()
    
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_telegram(self):
        """Setup Telegram bot"""
        try:
            self.logger.info("Setting up Telegram bot...")
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                updates = response.json()
                if updates['result']:
                    self.telegram_chat_id = updates['result'][-1]['message']['chat']['id']
                    self.logger.info(f"Telegram Chat ID: {self.telegram_chat_id}")
                    self.send_telegram("🤖 <b>AdShare Solver Started with Complete Error Handling!</b>")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Telegram setup failed: {e}")
            return False
    
    def send_telegram(self, text, parse_mode='HTML'):
        """Send message to Telegram with error handling"""
        if not self.telegram_chat_id:
            return False
        
        try:
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendMessage"
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Telegram send failed: {e}")
            return False

    def send_screenshot(self, caption="🖥️ Screenshot"):
        """Send screenshot to Telegram with error handling"""
        if not self.driver or not self.telegram_chat_id:
            return "❌ Browser not running or Telegram not configured"
        
        try:
            screenshot_path = "/tmp/screenshot.png"
            self.driver.save_screenshot(screenshot_path)
            
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendPhoto"
            
            with open(screenshot_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.telegram_chat_id,
                    'caption': f'{caption} - {time.strftime("%H:%M:%S")}'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
            
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
            return "✅ Screenshot sent!" if response.status_code == 200 else f"❌ Failed: {response.status_code}"
                
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    def send_cookies_to_telegram(self):
        """Send cookies as file to Telegram"""
        try:
            if not self.driver or not self.telegram_chat_id:
                return False
            
            cookies = self.driver.get_cookies()
            
            # Save cookies to file
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            
            # Send file to Telegram
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendDocument"
            
            with open(self.cookies_file, 'rb') as document:
                files = {'document': document}
                data = {
                    'chat_id': self.telegram_chat_id,
                    'caption': '🔐 Fresh Cookies Generated - Save this file for later use'
                }
                
                response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                self.logger.info("Cookies sent to Telegram")
                return True
            else:
                self.logger.error("Failed to send cookies to Telegram")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending cookies: {e}")
            return False

    # ==================== BROWSER HEALTH CHECK ====================
    def is_browser_alive(self):
        """Quick browser health check"""
        try:
            if not self.driver:
                return False
            self.driver.title
            return True
        except Exception as e:
            self.logger.error(f"Browser health check failed: {e}")
            return False

    def restart_browser(self):
        """Restart browser with error handling"""
        try:
            if self.driver:
                self.driver.quit()
            time.sleep(2)
            return self.setup_firefox()
        except Exception as e:
            self.logger.error(f"Browser restart failed: {e}")
            return False

    # ==================== COOKIES MANAGEMENT ====================
    def save_cookies(self):
        """Save cookies to file"""
        try:
            if self.driver and self.state['is_logged_in'] and self.is_browser_alive():
                cookies = self.driver.get_cookies()
                with open(self.cookies_file, 'w') as f:
                    json.dump(cookies, f)
                self.logger.info("Cookies saved locally")
        except Exception as e:
            self.logger.warning(f"Could not save cookies: {e}")

    def load_cookies(self):
        """Load cookies from file"""
        try:
            if os.path.exists(self.cookies_file) and self.is_browser_alive():
                with open(self.cookies_file, 'r') as f:
                    cookies = json.load(f)
                
                self.driver.get("https://adsha.re")
                for cookie in cookies:
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        self.logger.warning(f"Could not add cookie: {e}")
                        continue
                
                self.logger.info("Cookies loaded from file")
                return True
        except Exception as e:
            self.logger.warning(f"Could not load cookies: {e}")
        
        return False

    def handle_cookies_upload(self, file_info):
        """Process uploaded cookies file from Telegram"""
        try:
            self.logger.info("Processing cookies upload...")
            
            # Download cookies file from Telegram
            file_url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getFile"
            file_path = file_info['file_path']
            
            download_url = f"https://api.telegram.org/file/bot{CONFIG['telegram_token']}/{file_path}"
            response = requests.get(download_url)
            
            # Save cookies file
            with open(self.cookies_file, 'wb') as f:
                f.write(response.content)
            
            # Load cookies to browser
            if self.load_cookies():
                self.send_telegram("✅ Cookies loaded successfully!")
                self.state['is_logged_in'] = True
                self.waiting_for_cookies = False
                return True
            else:
                self.send_telegram("❌ Failed to load cookies - Auto logging in...")
                return self.force_login()
                
        except Exception as e:
            self.logger.error(f"Cookies upload error: {e}")
            self.send_telegram(f"❌ Cookies error: {e} - Auto logging in...")
            return self.force_login()

    def wait_for_user_response(self):
        """Wait for user response with 5-minute timeout"""
        start_time = time.time()
        user_responded = False
        
        self.send_telegram("""
🔐 **LOGIN REQUIRED**

Please choose:
• Send cookies file - Upload cookies.json
• `/login` - Auto login now  
• Wait - Auto login in 5 minutes
        """)
        
        while time.time() - start_time < CONFIG['cookies_wait_timeout']:
            try:
                # Check for Telegram updates
                url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    updates = response.json()
                    if updates['result']:
                        for update in updates['result']:
                            if 'message' in update:
                                text = update['message'].get('text', '').lower()
                                
                                if '/login' in text:
                                    self.logger.info("User chose auto login")
                                    self.force_login()
                                    user_responded = True
                                    break
                                
                                elif 'document' in update['message']:
                                    file_info = update['message']['document']
                                    if file_info['file_name'].endswith('.json'):
                                        self.logger.info("Cookies file received")
                                        self.handle_cookies_upload(file_info)
                                        user_responded = True
                                        break
                
                if user_responded:
                    break
                    
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error checking user response: {e}")
                time.sleep(10)
        
        # Auto login if no response after timeout
        if not user_responded:
            self.logger.info("No user response - auto logging in")
            self.send_telegram("⏰ No response received - Auto logging in...")
            self.force_login()

    # ==================== PAGE STATE DETECTION ====================
    def detect_page_state(self):
        """Detect current page state with error handling"""
        try:
            if not self.is_browser_alive():
                return "BROWSER_DEAD"
            
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()
            
            if "login" in current_url or "signin" in current_url:
                return "LOGIN_REQUIRED"
            elif "surf" in current_url:
                return "GAME_ACTIVE"
            elif "adsha.re" in current_url and "surf" not in current_url:
                return "WRONG_PAGE"
            elif "404" in page_source or "not found" in page_source:
                return "PAGE_NOT_FOUND"
            elif "error" in page_source or "500" in page_source:
                return "SERVER_ERROR"
            elif len(page_source) < 100:
                return "EMPTY_PAGE"
            else:
                return "UNKNOWN_PAGE"
                
        except Exception as e:
            self.logger.error(f"Page state detection error: {e}")
            return "DETECTION_ERROR"

    def ensure_correct_page(self):
        """Ensure we're on the correct surf page with comprehensive error handling"""
        if not self.is_browser_alive():
            self.logger.error("Browser dead during page check")
            return False
            
        try:
            page_state = self.detect_page_state()
            
            if page_state == "BROWSER_DEAD":
                self.logger.error("Browser is dead - cannot ensure correct page")
                return False
                
            elif page_state == "LOGIN_REQUIRED":
                self.logger.info("Login page detected - handling login...")
                if not self.state['is_logged_in']:
                    self.handle_login_page()
                return self.state['is_logged_in']
                
            elif page_state == "GAME_ACTIVE":
                return True
                
            elif page_state in ["WRONG_PAGE", "PAGE_NOT_FOUND", "SERVER_ERROR", "EMPTY_PAGE", "UNKNOWN_PAGE", "DETECTION_ERROR"]:
                self.logger.info(f"Wrong page state: {page_state} - redirecting to surf...")
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                return self.ensure_correct_page()
                
            else:
                self.logger.warning(f"Unknown page state: {page_state}")
                self.driver.get("https://adsha.re/surf")
                return True
                
        except Exception as e:
            self.logger.error(f"Page correction error: {e}")
            return False

    def handle_login_page(self):
        """Handle login page detection"""
        self.logger.info("Handling login page...")
        self.send_telegram("🔐 Login Page Detected!")
        self.send_screenshot("Login Page Screenshot")
        
        self.waiting_for_cookies = True
        self.wait_for_user_response()
        self.waiting_for_cookies = False

    # ==================== ORIGINAL LOGIN METHOD (UNCHANGED) ====================
    def force_login(self):
        """ORIGINAL WORKING LOGIN - DO NOT CHANGE"""
        try:
            self.logger.info("LOGIN: Attempting login...")
            
            login_url = "https://adsha.re/login"
            self.driver.get(login_url)
            
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.smart_delay()
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            form = soup.find('form', {'name': 'login'})
            if not form:
                self.logger.error("LOGIN: No login form found")
                return False
            
            password_field_name = None
            for field in form.find_all('input'):
                field_name = field.get('name', '')
                field_value = field.get('value', '')
                
                if field_value == 'Password' and field_name != 'mail' and field_name:
                    password_field_name = field_name
                    break
            
            if not password_field_name:
                self.logger.error("LOGIN: No password field found")
                return False
            
            self.logger.info(f"Password field: {password_field_name}")
            
            # Fill email
            email_selectors = [
                "input[name='mail']",
                "input[type='email']",
                "input[placeholder*='email' i]"
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    email_field.clear()
                    email_field.send_keys(CONFIG['email'])
                    self.logger.info("Email entered")
                    email_filled = True
                    break
                except:
                    continue
            
            if not email_filled:
                return False
            
            self.smart_delay()
            
            # Fill password
            password_selector = f"input[name='{password_field_name}']"
            try:
                password_field = self.driver.find_element(By.CSS_SELECTOR, password_selector)
                password_field.clear()
                password_field.send_keys(CONFIG['password'])
                self.logger.info("Password entered")
            except:
                return False
            
            self.smart_delay()
            
            # Click login button
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button",
                "input[value*='Login']",
                "input[value*='Sign']"
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_btn.is_displayed() and login_btn.is_enabled():
                        login_btn.click()
                        self.logger.info("Login button clicked")
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                try:
                    form_element = self.driver.find_element(By.CSS_SELECTOR, "form[name='login']")
                    form_element.submit()
                    self.logger.info("Form submitted")
                    login_clicked = True
                except:
                    pass
            
            self.smart_delay()
            time.sleep(8)
            
            # Verify login
            self.driver.get("https://adsha.re/surf")
            self.smart_delay()
            
            current_url = self.driver.current_url
            if "surf" in current_url or "dashboard" in current_url:
                self.logger.info("Login successful!")
                self.state['is_logged_in'] = True
                self.save_cookies()
                self.send_cookies_to_telegram()  # Send fresh cookies
                self.send_telegram("✅ <b>Login Successful!</b>")
                return True
            else:
                if "login" in current_url:
                    self.logger.error("Login failed - still on login page")
                    return False
                else:
                    self.logger.info("Login may need verification, continuing...")
                    self.state['is_logged_in'] = True
                    return True
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False

    # ==================== MEMORY OPTIMIZED FIREFOX SETUP ====================
    def setup_firefox(self):
        """Setup Firefox with memory optimization"""
        self.logger.info("Starting Firefox with memory optimization...")
        
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Memory optimization flags
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("content.processLimit", 1)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("javascript.options.mem.max", 25600)
            options.set_preference("browser.sessionhistory.max_entries", 1)
            options.set_preference("image.mem.max_decoded_image_kb", 512)
            options.set_preference("media.memory_cache_max_size", 1024)
            options.set_preference("permissions.default.image", 2)
            options.set_preference("gfx.webrender.all", True)
            options.set_preference("network.http.max-connections", 10)
            
            service = Service('/usr/local/bin/geckodriver')
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Install uBlock Origin
            ublock_path = '/app/ublock.xpi'
            if os.path.exists(ublock_path):
                self.driver.install_addon(ublock_path, temporary=False)
                self.logger.info("uBlock Origin installed")
            
            self.logger.info("Firefox started with memory optimization!")
            return True
            
        except Exception as e:
            self.logger.error(f"Firefox setup failed: {e}")
            return False

    def smart_delay(self):
        """Randomized delay between actions"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
        else:
            delay = CONFIG['base_delay']
        
        time.sleep(delay)
        return delay

    # ==================== ORIGINAL GAME SOLVING METHODS (UNCHANGED) ====================
    def simple_click(self, element):
        """Simple direct click without mouse movement"""
        try:
            self.smart_delay()
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"Click failed: {e}")
            return False

    def calculate_similarity(self, str1, str2):
        """Calculate string similarity"""
        if len(str1) == 0 or len(str2) == 0:
            return 0.0
        
        common_chars = sum(1 for a, b in zip(str1, str2) if a == b)
        max_len = max(len(str1), len(str2))
        return common_chars / max_len if max_len > 0 else 0.0

    def compare_symbols(self, question_svg, answer_svg):
        """Compare SVG symbols"""
        try:
            question_content = question_svg.get_attribute('innerHTML')
            answer_content = answer_svg.get_attribute('innerHTML')
            
            if not question_content or not answer_content:
                return {'match': False, 'confidence': 0.0, 'exact': False}
            
            def clean_svg(svg_text):
                cleaned = re.sub(r'\s+', ' ', svg_text).strip().lower()
                cleaned = re.sub(r'fill:#[a-f0-9]+', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'stroke:#[a-f0-9]+', '', cleaned, flags=re.IGNORECASE)
                cleaned = re.sub(r'style="[^"]*"', '', cleaned)
                cleaned = re.sub(r'class="[^"]*"', '', cleaned)
                return cleaned
            
            clean_question = clean_svg(question_content)
            clean_answer = clean_svg(answer_content)
            
            if clean_question == clean_answer:
                return {'match': True, 'confidence': 1.0, 'exact': True}
            
            similarity = self.calculate_similarity(clean_question, clean_answer)
            should_match = similarity >= 0.90
            
            return {'match': should_match, 'confidence': similarity, 'exact': False}
            
        except Exception as e:
            self.logger.warning(f"Symbol comparison error: {e}")
            return {'match': False, 'confidence': 0.0, 'exact': False}

    def find_best_match(self, question_svg, links):
        """Find best matching symbol"""
        best_match = None
        highest_confidence = 0
        exact_matches = []
        
        for link in links:
            try:
                answer_svg = link.find_element(By.TAG_NAME, "svg")
                if answer_svg:
                    comparison = self.compare_symbols(question_svg, answer_svg)
                    
                    if comparison['exact'] and comparison['match']:
                        exact_matches.append({
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': True
                        })
                    
                    elif comparison['match'] and comparison['confidence'] > highest_confidence:
                        highest_confidence = comparison['confidence']
                        best_match = {
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': False
                        }
            except:
                continue
        
        if exact_matches:
            return exact_matches[0]
        
        if best_match and best_match['confidence'] >= 0.90:
            return best_match
        
        return None

    def solve_symbol_game(self):
        """Main game solving logic with comprehensive error handling"""
        if not self.state['is_running']:
            return False
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead during game solving")
            return False
            
        try:
            if not self.ensure_correct_page():
                self.logger.info("Not on correct page, redirecting...")
                self.driver.get("https://adsha.re/surf")
                if not self.ensure_correct_page():
                    return False
            
            question_svg = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "svg"))
            )
            
            if not question_svg:
                self.logger.info("Waiting for game to load...")
                return False
            
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='adsha.re'], button, .answer-option")
            
            best_match = self.find_best_match(question_svg, links)
            
            if best_match:
                if self.simple_click(best_match['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_fails'] = 0
                    match_type = "EXACT" if best_match['exact'] else "FUZZY"
                    self.logger.info(f"{match_type} Match! Total: {self.state['total_solved']}")
                    return True
            else:
                self.logger.info("No good match found")
                self.handle_consecutive_failures()
                return False
            
        except TimeoutException:
            self.logger.info("Waiting for game elements...")
            self.handle_consecutive_failures()
            return False
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            self.handle_consecutive_failures()
            return False

    # ==================== ERROR HANDLING ====================
    def handle_consecutive_failures(self):
        """Handle consecutive failures with comprehensive error handling"""
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        
        self.logger.info(f"Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead during failure handling")
            if current_fails >= 3:
                self.restart_browser()
            return
        
        # Screenshot on first failure
        if current_fails == 1 and CONFIG['send_screenshot_on_error']:
            cooldown_passed = time.time() - self.state['last_error_screenshot'] > CONFIG['screenshot_cooldown_minutes'] * 60
            if cooldown_passed:
                self.logger.info("Sending error screenshot...")
                screenshot_result = self.send_screenshot("❌ Game Error - No game solved")
                self.send_telegram(f"⚠️ <b>Game Error</b>\nFails: {current_fails}/{CONFIG['max_consecutive_failures']}\n{screenshot_result}")
                self.state['last_error_screenshot'] = time.time()
        
        # Refresh page after configured failures
        elif current_fails >= CONFIG['refresh_page_after_failures']:
            self.logger.info("Too many failures! Refreshing page...")
            self.send_telegram(f"🔄 <b>Refreshing page</b> - {current_fails} failures")
            
            try:
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                self.logger.info("Page refreshed")
                self.state['consecutive_fails'] = 0
            except Exception as e:
                self.logger.error(f"Page refresh failed: {e}")
        
        # Restart browser after more failures
        elif current_fails >= 8:
            self.logger.warning("Multiple failures - restarting browser...")
            self.send_telegram(f"🔄 <b>Restarting browser</b> - {current_fails} failures")
            self.restart_browser()
            self.state['consecutive_fails'] = 0
        
        # Stop at max failures
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures! Stopping...")
            self.send_telegram("🚨 <b>CRITICAL ERROR</b>\nToo many failures - Stopping")
            self.stop()

    # ==================== TARGET MANAGEMENT ====================
    def set_daily_target(self, target):
        """Set daily target"""
        try:
            self.state['daily_target'] = int(target)
            self.send_telegram(f"🎯 Daily target set to {target} sites")
            return True
        except:
            return False

    def clear_daily_target(self):
        """Clear daily target"""
        self.state['daily_target'] = None
        self.send_telegram("🎯 Daily target cleared - Focusing on #1 position")
        return True

    def get_daily_progress(self):
        """Get daily progress"""
        # This would need actual implementation to get current surfed count
        # For now, returning placeholder
        return f"🎯 Daily: {self.state['total_solved']}/{self.state['daily_target']}"

    # ==================== LEADERBOARD PARSING ====================
    def parse_leaderboard(self):
        """Parse top 10 leaderboard"""
        try:
            if not self.is_browser_alive():
                return None
            
            # Save current window
            original_window = self.driver.current_window_handle
            
            # Open leaderboard in new tab
            self.driver.execute_script("window.open('https://adsha.re/ten', '_blank')")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Wait for page load
            time.sleep(3)
            
            # Parse HTML
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            leaderboard = []
            
            # Find all user entries
            user_divs = soup.find_all('div', style=lambda x: x and 'width:250px' in x)
            
            for i, div in enumerate(user_divs[:10]):  # Top 10 only
                text = div.get_text()
                
                # Extract user ID
                user_match = re.search(r'#(\d+)', text)
                user_id = int(user_match.group(1)) if user_match else None
                
                # Extract total surfed
                surfed_match = re.search(r'Surfed in 3 Days:\s*([\d,]+)', text)
                total_surfed = int(surfed_match.group(1).replace(',', '')) if surfed_match else 0
                
                # Extract prize
                prize_match = re.search(r'-\s*([\d,]+)\s*Visitors', text)
                prize = prize_match.group(1) + ' Visitors' if prize_match else 'No Prize'
                
                leaderboard.append({
                    'rank': i + 1,
                    'user_id': user_id,
                    'total_surfed': total_surfed,
                    'prize': prize,
                    'is_me': user_id == 4242  # Your ID
                })
            
            # Close tab and return to original window
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            self.state['last_leaderboard_check'] = time.time()
            return leaderboard
            
        except Exception as e:
            self.logger.error(f"Leaderboard parsing error: {e}")
            # Ensure we return to original window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return None

    def leaderboard_monitor(self):
        """Background leaderboard monitoring"""
        self.logger.info("Starting leaderboard monitoring...")
        
        while self.state['monitoring_active']:
            try:
                if self.state['is_running']:
                    leaderboard = self.parse_leaderboard()
                    if leaderboard:
                        # Check if we're not #1 and update target
                        my_position = next((item for item in leaderboard if item['is_me']), None)
                        if my_position and my_position['rank'] > 1:
                            leader = leaderboard[0]
                            target_sites = leader['total_surfed'] + 100
                            if not self.state['daily_target'] or target_sites > self.state['daily_target']:
                                self.state['daily_target'] = target_sites
                                self.send_telegram(f"🎯 Auto-target set: {target_sites} sites (Overtake #{leader['user_id']})")
                
                # Check every 30 minutes
                for _ in range(1800):
                    if not self.state['monitoring_active']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Leaderboard monitoring error: {e}")
                time.sleep(300)  # Retry in 5 minutes

    # ==================== MAIN SOLVER LOOP ====================
    def solver_loop(self):
        """Main solving loop with comprehensive error handling"""
        self.logger.info("Starting solver loop...")
        self.state['status'] = 'running'
        
        if not self.driver:
            if not self.setup_firefox():
                self.logger.error("Cannot start - Firefox failed")
                self.stop()
                return
        
        # Initial navigation
        self.driver.get("https://adsha.re/surf")
        if not self.ensure_correct_page():
            self.logger.info("Initial navigation issues, continuing...")
        
        consecutive_fails = 0
        cycle_count = 0
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                # Browser health check
                if not self.is_browser_alive():
                    self.logger.error("Browser dead, restarting...")
                    if not self.restart_browser():
                        self.logger.error("Browser restart failed, stopping...")
                        self.stop()
                        break
                
                # Memory cleanup every 50 cycles
                if cycle_count % 50 == 0:
                    gc.collect()
                    self.logger.debug("Memory cleanup performed")
                
                # Solve game
                game_solved = self.solve_symbol_game()
                
                if game_solved:
                    consecutive_fails = 0
                    time.sleep(11)  # Wait for next game
                else:
                    consecutive_fails += 1
                    time.sleep(5)  # Longer wait on failure
                
                cycle_count += 1
                    
            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                consecutive_fails += 1
                time.sleep(10)
        
        if self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures, stopping...")
            self.stop()

    # ==================== CONTROL METHODS ====================
    def start(self):
        """Start the solver"""
        if self.state['is_running']:
            return "❌ Solver already running"
        
        self.state['is_running'] = True
        self.state['consecutive_fails'] = 0
        self.state['last_error_screenshot'] = 0
        
        self.solver_thread = threading.Thread(target=self.solver_loop)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        if not self.state['monitoring_active']:
            self.state['monitoring_active'] = True
            self.monitoring_thread = threading.Thread(target=self.leaderboard_monitor)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
        
        self.logger.info("Solver started with complete error handling!")
        self.send_telegram("🚀 <b>Solver Started with Complete Error Handling!</b>")
        return "✅ Solver started successfully!"

    def stop(self):
        """Stop the solver"""
        self.state['is_running'] = False
        self.state['monitoring_active'] = False
        self.state['status'] = 'stopped'
        
        if self.is_browser_alive():
            self.save_cookies()
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.logger.info("Solver stopped")
        self.send_telegram("🛑 <b>Solver Stopped!</b>")
        return "✅ Solver stopped successfully!"

    def status(self):
        """Get status"""
        leaderboard = self.parse_leaderboard()
        status_text = f"""
📊 <b>Status Report</b>
⏰ {time.strftime('%H:%M:%S')}
🔄 Status: {self.state['status']}
🎯 Games Solved: {self.state['total_solved']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
"""
        
        if self.state['daily_target']:
            status_text += f"🎯 Daily Target: {self.state['daily_target']} sites\n"
        
        if leaderboard:
            my_pos = next((item for item in leaderboard if item['is_me']), None)
            if my_pos:
                status_text += f"🏆 My Position: #{my_pos['rank']}\n"
                if my_pos['rank'] > 1:
                    leader = leaderboard[0]
                    gap = leader['total_surfed'] - my_pos['total_surfed']
                    status_text += f"📈 Gap to #1: {gap} sites\n"
        
        return status_text

# Telegram Bot
class TelegramBot:
    def __init__(self):
        self.solver = FirefoxSymbolGameSolver()
        self.logger = logging.getLogger(__name__)
        self.last_update_id = 0
    
    def get_telegram_updates(self):
        """Get Telegram updates"""
        try:
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
            params = {'offset': self.last_update_id, 'timeout': 10}
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                updates = response.json()
                if updates['result']:
                    self.last_update_id = updates['result'][-1]['update_id'] + 1
                    return updates['result']
            return []
        except Exception as e:
            self.logger.error(f"Telegram updates error: {e}")
            return []
    
    def process_message(self, update):
        """Process Telegram message"""
        if 'message' not in update or 'text' not in update['message']:
            # Check for document upload (cookies file)
            if 'document' in update['message']:
                file_info = update['message']['document']
                if file_info['file_name'].endswith('.json'):
                    self.solver.handle_cookies_upload(file_info)
            return
        
        chat_id = update['message']['chat']['id']
        text = update['message']['text']
        
        if not self.solver.telegram_chat_id:
            self.solver.telegram_chat_id = chat_id
        
        response = ""
        
        if text.startswith('/start'):
            response = self.solver.start()
        elif text.startswith('/stop'):
            response = self.solver.stop()
        elif text.startswith('/status'):
            response = self.solver.status()
        elif text.startswith('/screenshot'):
            response = self.solver.send_screenshot()
        elif text.startswith('/target'):
            parts = text.split()
            if len(parts) == 2 and parts[1].isdigit():
                if self.solver.set_daily_target(parts[1]):
                    response = f"🎯 Daily target set to {parts[1]} sites"
                else:
                    response = "❌ Invalid target"
            elif len(parts) == 2 and parts[1] == 'clear':
                self.solver.clear_daily_target()
                response = "🎯 Daily target cleared"
            else:
                response = self.solver.get_daily_progress()
        elif text.startswith('/login'):
            response = "🔐 Attempting login..." if self.solver.force_login() else "❌ Login failed"
        elif text.startswith('/competitors'):
            leaderboard = self.solver.parse_leaderboard()
            if leaderboard:
                comp_text = "🏆 <b>Top 10 Competitors</b>\n"
                for entry in leaderboard[:10]:
                    marker = " 👈 YOU" if entry['is_me'] else ""
                    comp_text += f"{entry['rank']}. #{entry['user_id']} - {entry['total_surfed']} sites{marker}\n"
                response = comp_text
            else:
                response = "❌ Could not fetch leaderboard"
        elif text.startswith('/help'):
            response = """
🤖 <b>AdShare Solver Commands</b>

/start - Start solver
/stop - Stop solver  
/status - Check status
/screenshot - Get screenshot
/target [number] - Set daily target
/target clear - Clear daily target
/login - Force login
/competitors - Show top 10
/help - Show help

🔐 <b>Cookies System</b>
- Auto-sends cookies after login
- Asks for cookies on login page
- 5-minute auto-login timeout
            """
        
        if response:
            self.solver.send_telegram(response)
    
    def handle_updates(self):
        """Handle Telegram updates"""
        self.logger.info("Starting Telegram bot...")
        
        while True:
            try:
                updates = self.get_telegram_updates()
                for update in updates:
                    self.process_message(update)
                
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Telegram bot error: {e}")
                time.sleep(5)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.logger.info("AdShare Solver with Complete Error Handling started!")
    bot.handle_updates()
