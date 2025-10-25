#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - Competitive Edition
Complete features with leaderboard competition
"""

import os
import time
import random
import logging
import re
import requests
import threading
import json
import gc
import pytz
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    'max_consecutive_failures': 15,
    'refresh_page_after_failures': 5,
    'cookies_wait_timeout': 300,
    'leaderboard_check_interval': 1800,  # 30 minutes
    'safety_margin': 100,  # +100 credits above #1
}

class CompetitiveSymbolSolver:
    def __init__(self):
        self.driver = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        self.waiting_for_cookies = False
        
        # Enhanced State Management
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'is_logged_in': False,
            'consecutive_fails': 0,
            'last_error_screenshot': 0,
            'daily_target': None,
            'auto_compete': True,
            'safety_margin': CONFIG['safety_margin'],
            'leaderboard': [],
            'my_position': None,
            'last_leaderboard_check': 0,
        }
        
        self.solver_thread = None
        self.monitoring_thread = None
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
                    self.send_telegram("🤖 <b>Competitive AdShare Solver Started!</b>")
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Telegram setup failed: {e}")
            return False
    
    def send_telegram(self, text, parse_mode='HTML'):
        """Send message to Telegram"""
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
        """Send screenshot to Telegram"""
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
                    'caption': f'{caption} - {self.get_ist_time()}'
                }
                response = requests.post(url, files=files, data=data, timeout=30)
            
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
            return "✅ Screenshot sent!" if response.status_code == 200 else "❌ Failed to send screenshot"
                
        except Exception as e:
            return f"❌ Screenshot error: {str(e)}"

    def get_ist_time(self):
        """Get current IST time"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist).strftime('%I:%M %p IST')

    def send_cookies_to_telegram(self):
        """Send cookies as file to Telegram"""
        try:
            if not self.driver or not self.telegram_chat_id:
                return False
            
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendDocument"
            
            with open(self.cookies_file, 'rb') as document:
                files = {'document': document}
                data = {
                    'chat_id': self.telegram_chat_id,
                    'caption': '🔐 Fresh Cookies Generated - Save for later use'
                }
                response = requests.post(url, files=files, data=data, timeout=30)
            
            if response.status_code == 200:
                self.logger.info("Cookies sent to Telegram")
                return True
            return False
                
        except Exception as e:
            self.logger.error(f"Error sending cookies: {e}")
            return False

    # ==================== BROWSER MANAGEMENT ====================
    def is_browser_alive(self):
        """Check if browser is alive"""
        try:
            if not self.driver:
                return False
            self.driver.title
            return True
        except Exception:
            return False

    def restart_browser(self):
        """Restart browser"""
        try:
            if self.driver:
                self.driver.quit()
            time.sleep(2)
            return self.setup_firefox()
        except Exception as e:
            self.logger.error(f"Browser restart failed: {e}")
            return False

    def setup_firefox(self):
        """Setup Firefox with memory optimization"""
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Memory optimization
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("content.processLimit", 1)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("javascript.options.mem.max", 25600)
            options.set_preference("browser.sessionhistory.max_entries", 1)
            options.set_preference("image.mem.max_decoded_image_kb", 512)
            options.set_preference("media.memory_cache_max_size", 1024)
            options.set_preference("permissions.default.image", 1)  # ALLOW IMAGES
            options.set_preference("gfx.webrender.all", True)
            options.set_preference("network.http.max-connections", 10)
            
            service = Service('/usr/local/bin/geckodriver')
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Install uBlock Origin
            ublock_path = '/app/ublock.xpi'
            if os.path.exists(ublock_path):
                self.driver.install_addon(ublock_path, temporary=False)
                self.logger.info("uBlock Origin installed")
            
            self.logger.info("Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Firefox setup failed: {e}")
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
                    except:
                        continue
                
                self.logger.info("Cookies loaded from file")
                return True
        except Exception as e:
            self.logger.warning(f"Could not load cookies: {e}")
        return False

    def handle_cookies_upload(self, file_info):
        """Process uploaded cookies file"""
        try:
            file_path = file_info['file_path']
            download_url = f"https://api.telegram.org/file/bot{CONFIG['telegram_token']}/{file_path}"
            response = requests.get(download_url)
            
            with open(self.cookies_file, 'wb') as f:
                f.write(response.content)
            
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
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"Error checking user response: {e}")
                time.sleep(10)
        
        if not user_responded:
            self.logger.info("No user response - auto logging in")
            self.send_telegram("⏰ No response received - Auto logging in...")
            self.force_login()

    # ==================== PAGE STATE DETECTION ====================
    def detect_page_state(self):
        """Detect current page state"""
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
            else:
                return "UNKNOWN_PAGE"
                
        except Exception as e:
            self.logger.error(f"Page state detection error: {e}")
            return "DETECTION_ERROR"

    def ensure_correct_page(self):
        """Ensure we're on the correct surf page"""
        if not self.is_browser_alive():
            self.logger.error("Browser dead during page check")
            return False
            
        try:
            page_state = self.detect_page_state()
            
            if page_state == "BROWSER_DEAD":
                return False
            elif page_state == "LOGIN_REQUIRED":
                self.logger.info("Login page detected - handling login...")
                if not self.state['is_logged_in']:
                    self.handle_login_page()
                return self.state['is_logged_in']
            elif page_state == "GAME_ACTIVE":
                return True
            else:
                self.logger.info(f"Wrong page state: {page_state} - redirecting to surf...")
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                return self.ensure_correct_page()
                
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
                self.send_cookies_to_telegram()
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
        """Main game solving logic"""
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

    # ==================== LEADERBOARD COMPETITION ====================
    def parse_leaderboard(self):
        """Parse top 10 leaderboard"""
        try:
            if not self.is_browser_alive():
                return None
            
            original_window = self.driver.current_window_handle
            self.driver.execute_script("window.open('https://adsha.re/ten', '_blank')")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            leaderboard = []
            
            user_divs = soup.find_all('div', style=lambda x: x and 'width:250px' in x)
            
            for i, div in enumerate(user_divs[:10]):  # Top 10 only
                text = div.get_text()
                
                # Extract user ID
                user_match = re.search(r'#(\d+)', text)
                user_id = int(user_match.group(1)) if user_match else None
                
                # Extract total surfed
                surfed_match = re.search(r'Surfed in 3 Days:\s*([\d,]+)', text)
                total_surfed = int(surfed_match.group(1).replace(',', '')) if surfed_match else 0
                
                # Extract today's credits (from T: X / Y: X / DB: X)
                today_match = re.search(r'T:\s*(\d+)', text)
                today_credits = int(today_match.group(1)) if today_match else 0
                
                leaderboard.append({
                    'rank': i + 1,
                    'user_id': user_id,
                    'total_surfed': total_surfed,
                    'today_credits': today_credits,
                    'is_me': user_id == 4242  # Your ID
                })
            
            self.driver.close()
            self.driver.switch_to.window(original_window)
            
            self.state['last_leaderboard_check'] = time.time()
            self.state['leaderboard'] = leaderboard
            
            # Find my position
            self.state['my_position'] = next((item for item in leaderboard if item['is_me']), None)
            
            return leaderboard
            
        except Exception as e:
            self.logger.error(f"Leaderboard parsing error: {e}")
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return None

    def get_competitive_target(self):
        """Calculate competitive target"""
        if not self.state['leaderboard']:
            return None
        
        leader = self.state['leaderboard'][0]
        my_pos = self.state['my_position']
        
        if my_pos and my_pos['rank'] > 1:
            target = leader['today_credits'] + self.state['safety_margin']
            return target
        elif my_pos and my_pos['rank'] == 1:
            # Stay #1 with safety margin over #2
            if len(self.state['leaderboard']) > 1:
                second_place = self.state['leaderboard'][1]['today_credits']
                target = second_place + self.state['safety_margin']
                return target
        
        return None

    def get_competitive_status(self):
        """Get competitive status display"""
        status_text = f"""
📊 <b>COMPETITIVE STATUS</b>
⏰ {self.get_ist_time()}
🔄 Status: {self.state['status']}
🎮 Games Solved: {self.state['total_solved']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
"""
        
        # Add competition info
        if self.state['auto_compete'] and self.state['leaderboard']:
            target = self.get_competitive_target()
            my_pos = self.state['my_position']
            
            if my_pos and target:
                leader = self.state['leaderboard'][0]
                gap = target - my_pos['today_credits'] if my_pos['today_credits'] < target else 0
                
                status_text += f"""
🎯 <b>Auto Target:</b> {target} credits (+{self.state['safety_margin']} lead)
🥇 <b>Current Position:</b> #{my_pos['rank']} ({my_pos['today_credits']} vs #1: {leader['today_credits']})
📈 <b>To Reach #1:</b> {gap} credits needed
💎 <b>Earned Today:</b> {my_pos['today_credits']} credits
"""
        
        elif self.state['daily_target']:
            status_text += f"🎯 <b>Daily Target:</b> {self.state['daily_target']} sites\n"
        
        # Add leaderboard preview
        if self.state['leaderboard']:
            status_text += f"\n🏆 <b>LEADERBOARD (Top 3):</b>\n"
            for entry in self.state['leaderboard'][:3]:
                marker = " 👈 YOU" if entry['is_me'] else ""
                status_text += f"{entry['rank']}. #{entry['user_id']} - {entry['today_credits']} credits{marker}\n"
        
        return status_text

    def leaderboard_monitor(self):
        """Background leaderboard monitoring"""
        self.logger.info("Starting leaderboard monitoring...")
        
        while self.state['is_running']:
            try:
                if self.state['auto_compete']:
                    leaderboard = self.parse_leaderboard()
                    if leaderboard:
                        target = self.get_competitive_target()
                        if target and target != self.state.get('last_target'):
                            self.state['last_target'] = target
                            self.send_telegram(f"🎯 <b>Auto Target Updated:</b> {target} credits (Beat #{leaderboard[0]['user_id']})")
                
                # Check every 30 minutes
                for _ in range(CONFIG['leaderboard_check_interval']):
                    if not self.state['is_running']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Leaderboard monitoring error: {e}")
                time.sleep(300)

    # ==================== TARGET MANAGEMENT ====================
    def set_daily_target(self, target):
        """Set daily target"""
        try:
            self.state['daily_target'] = int(target)
            self.state['auto_compete'] = False
            self.send_telegram(f"🎯 Daily target set to {target} sites (Manual mode)")
            return True
        except:
            return False

    def clear_daily_target(self):
        """Clear daily target"""
        self.state['daily_target'] = None
        self.state['auto_compete'] = True
        self.send_telegram("🎯 Daily target cleared - Auto-compete mode activated")
        return True

    def set_auto_compete(self, margin=None):
        """Set auto-compete mode"""
        if margin:
            try:
                self.state['safety_margin'] = int(margin)
            except:
                pass
        
        self.state['auto_compete'] = True
        self.state['daily_target'] = None
        
        margin_text = f" (+{self.state['safety_margin']} margin)" if margin else ""
        self.send_telegram(f"🏆 Auto-compete mode activated{margin_text} - Targeting #1 position")
        return True

    # ==================== ERROR HANDLING ====================
    def handle_consecutive_failures(self):
        """Handle consecutive failures"""
        self.state['consecutive_fails'] += 1
        current_fails = self.state['consecutive_fails']
        
        self.logger.info(f"Consecutive failures: {current_fails}/{CONFIG['max_consecutive_failures']}")
        
        if not self.is_browser_alive():
            if current_fails >= 3:
                self.restart_browser()
            return
        
        if current_fails >= CONFIG['refresh_page_after_failures']:
            self.logger.info("Refreshing page...")
            self.send_telegram(f"🔄 Refreshing page - {current_fails} failures")
            
            try:
                self.driver.get("https://adsha.re/surf")
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                self.smart_delay()
                self.state['consecutive_fails'] = 0
            except Exception as e:
                self.logger.error(f"Page refresh failed: {e}")
        
        elif current_fails >= 8:
            self.logger.warning("Restarting browser...")
            self.restart_browser()
            self.state['consecutive_fails'] = 0
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("Too many failures! Stopping...")
            self.send_telegram("🚨 CRITICAL ERROR - Too many failures - Stopping")
            self.stop()

    # ==================== MAIN SOLVER LOOP ====================
    def solver_loop(self):
        """Main solving loop"""
        self.logger.info("Starting solver loop...")
        self.state['status'] = 'running'
        
        if not self.driver:
            if not self.setup_firefox():
                self.logger.error("Cannot start - Firefox failed")
                self.stop()
                return
        
        self.driver.get("https://adsha.re/surf")
        if not self.ensure_correct_page():
            self.logger.info("Initial navigation issues, continuing...")
        
        cycle_count = 0
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                if not self.is_browser_alive():
                    if not self.restart_browser():
                        self.stop()
                        break
                
                if cycle_count % 50 == 0:
                    gc.collect()
                
                game_solved = self.solve_symbol_game()
                
                if game_solved:
                    time.sleep(10)  # Wait for next game (10-12 seconds)
                else:
                    time.sleep(5)
                
                cycle_count += 1
                    
            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                self.state['consecutive_fails'] += 1
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
        
        self.solver_thread = threading.Thread(target=self.solver_loop)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        self.monitoring_thread = threading.Thread(target=self.leaderboard_monitor)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("Competitive solver started!")
        self.send_telegram("🚀 Competitive Solver Started!")
        return "✅ Solver started successfully!"

    def stop(self):
        """Stop the solver"""
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        
        if self.is_browser_alive():
            self.save_cookies()
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.logger.info("Solver stopped")
        self.send_telegram("🛑 Solver Stopped!")
        return "✅ Solver stopped successfully!"

    def status(self):
        """Get competitive status"""
        # Refresh leaderboard if stale
        if time.time() - self.state['last_leaderboard_check'] > 1800:  # 30 minutes
            self.parse_leaderboard()
        
        return self.get_competitive_status()

# Telegram Bot
class TelegramBot:
    def __init__(self):
        self.solver = CompetitiveSymbolSolver()
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
        if 'message' not in update:
            if 'document' in update.get('message', {}):
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
                response = "Usage: /target 3000 or /target clear"
        elif text.startswith('/compete'):
            parts = text.split()
            margin = parts[1] if len(parts) > 1 else None
            self.solver.set_auto_compete(margin)
            response = f"🏆 Auto-compete mode activated (+{self.solver.state['safety_margin']} margin)"
        elif text.startswith('/leaderboard'):
            leaderboard = self.solver.parse_leaderboard()
            if leaderboard:
                leader_text = "🏆 <b>TOP 10 LEADERBOARD</b>\n"
                for entry in leaderboard:
                    marker = " 👈 YOU" if entry['is_me'] else ""
                    leader_text += f"{entry['rank']}. #{entry['user_id']} - {entry['today_credits']} credits{marker}\n"
                response = leader_text
            else:
                response = "❌ Could not fetch leaderboard"
        elif text.startswith('/login'):
            response = "🔐 Attempting login..." if self.solver.force_login() else "❌ Login failed"
        elif text.startswith('/help'):
            response = """
🤖 <b>Competitive AdShare Solver</b>

<b>Basic Commands:</b>
/start - Start solver
/stop - Stop solver  
/status - Competitive status
/screenshot - Get screenshot
/login - Force login

<b>Target Management:</b>
/target 3000 - Set daily target
/target clear - Clear target
/compete - Auto-compete mode
/compete 150 - Compete with +150 margin

<b>Information:</b>
/leaderboard - Show top 10
/help - Show help

🔐 <b>Cookies System:</b>
- Auto-sends cookies after login
- Asks for cookies on login page
- 5-minute auto-login timeout
            """
        
        if response:
            self.solver.send_telegram(response)
    
    def handle_updates(self):
        """Handle Telegram updates"""
        self.logger.info("Starting Competitive Telegram bot...")
        
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
    bot.logger.info("Competitive AdShare Solver started!")
    bot.handle_updates()
