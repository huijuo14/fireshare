#!/usr/bin/env python3
"""
AdShare Symbol Game Solver - PERFECT SHAPE MATCHING EDITION v3.4
EXACT SAME LOGIC AS USERSCRIPT v3.4
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
import urllib3
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup

# Disable connection pool warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==================== CONFIGURATION ====================
CONFIG = {
    'email': "loginallapps@gmail.com",
    'password': "@Sd2007123",
    'base_delay': 1.7,
    'random_delay': True,
    'min_delay': 1.5,
    'max_delay': 3.5,
    'telegram_token': "8225236307:AAF9Y2-CM7TlLDFm2rcTVY6f3SA75j0DFI8",
    'max_consecutive_failures': 15,
    'element_wait_time': 5,
    'refresh_after_failures': 3,
    'restart_after_failures': 8,
    'leaderboard_check_interval': 1800,
    'safety_margin': 100,
    'performance_tracking': True,
    'minimum_confidence': 0.90,
    'max_clicks_per_minute': 20,
}

class UltimateShapeSolver:
    def __init__(self):
        self.driver = None
        self.telegram_chat_id = None
        self.cookies_file = "/app/cookies.json"
        
        # Enhanced State Management - EXACT SAME AS USERSCRIPT v3.4
        self.state = {
            'is_running': False,
            'total_solved': 0,
            'status': 'stopped',
            'is_logged_in': False,
            'consecutive_fails': 0,
            'element_not_found_count': 0,
            'daily_target': None,
            'auto_compete': True,
            'safety_margin': CONFIG['safety_margin'],
            'leaderboard': [],
            'my_position': None,
            'last_leaderboard_check': 0,
            'last_target': None,
            'last_rank': None,
            'performance_metrics': {
                'games_per_hour': 0,
                'start_time': 0,
                'last_hour_count': 0
            },
            'last_question_hash': '',
            'auto_click': True,
            'wrong_click_count': 0,
            'last_wrong_click_time': 0,
            'no_question_count': 0,
            'click_count': 0,
            'last_click_time': 0,
            'session_start_time': 0,
            'consecutive_rounds': 0,
            'is_in_cooldown': False,
            'consecutive_match_fails': 0
        }
        
        # Symbol types - EXACT SAME AS USERSCRIPT v3.4
        self.SYMBOL_TYPES = {
            'CIRCLE': 'circle',
            'SQUARE': 'square', 
            'DIAMOND': 'diamond',
            'ARROW_DOWN': 'arrow_down',
            'ARROW_LEFT': 'arrow_left',
            'BACKGROUND_CIRCLE': 'background_circle',
            'UNKNOWN': 'unknown'
        }
        
        self.solver_thread = None
        self.monitoring_thread = None
        self.setup_logging()
        self.setup_telegram()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_telegram(self):
        """Setup Telegram bot with enhanced features"""
        try:
            self.logger.info("Setting up Ultimate Telegram bot...")
            url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/getUpdates"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                updates = response.json()
                if updates['result']:
                    self.telegram_chat_id = updates['result'][-1]['message']['chat']['id']
                    self.logger.info(f"Telegram Chat ID: {self.telegram_chat_id}")
                    self.send_telegram("🤖 <b>PERFECT SHAPE MATCHING Solver v3.4 Started!</b>")
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
        """Send screenshot to Telegram with enhanced error handling"""
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

    # ==================== ENHANCED BROWSER MANAGEMENT ====================
    def is_browser_alive(self):
        """ULTRA-RELIABLE browser health check"""
        try:
            if not self.driver:
                return False
            self.driver.current_url
            self.driver.title
            return True
        except Exception as e:
            self.logger.warning(f"Browser health check failed: {e}")
            return False

    def setup_firefox(self):
        """ULTIMATE Firefox setup with uBlock Origin"""
        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            
            # ULTIMATE Memory Optimization
            options.set_preference("dom.ipc.processCount", 1)
            options.set_preference("content.processLimit", 1)
            options.set_preference("browser.cache.disk.enable", False)
            options.set_preference("browser.cache.memory.enable", False)
            options.set_preference("javascript.options.mem.max", 25600)
            options.set_preference("browser.sessionhistory.max_entries", 1)
            options.set_preference("image.mem.max_decoded_image_kb", 512)
            options.set_preference("media.memory_cache_max_size", 1024)
            options.set_preference("permissions.default.image", 1)
            options.set_preference("gfx.webrender.all", True)
            options.set_preference("network.http.max-connections", 10)
            
            service = Service('/usr/local/bin/geckodriver', log_path=os.devnull)
            self.driver = webdriver.Firefox(service=service, options=options)
            
            # Install uBlock Origin for performance
            ublock_path = '/app/ublock.xpi'
            if os.path.exists(ublock_path):
                self.driver.install_addon(ublock_path, temporary=False)
                self.logger.info("uBlock Origin installed for enhanced performance")
            
            self.logger.info("ULTIMATE Firefox started successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Firefox setup failed: {e}")
            return False

    def restart_browser(self):
        """ENHANCED browser restart with PROPER login recovery"""
        try:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
            time.sleep(3)
            gc.collect()
            
            self.state['is_logged_in'] = False
            self.state['consecutive_fails'] = 0
            self.state['element_not_found_count'] = 0
            self.state['no_question_count'] = 0
            self.state['consecutive_match_fails'] = 0
            self.state['is_in_cooldown'] = False
            
            success = self.setup_firefox()
            if success:
                self.logger.info("Browser restart successful - login required")
                login_success = self.force_login()
                if login_success:
                    self.state['is_logged_in'] = True
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Browser restart failed: {e}")
            return False

    # ==================== EXACT SAME LOGIN FUNCTION ====================
    def force_login(self):
        """ULTIMATE WORKING LOGIN - EXACT COPY FROM WORKING SCRIPT"""
        try:
            self.logger.info("ULTIMATE LOGIN: Attempting login...")
            
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
            
            email_selectors = [
                "input[name='mail']",
                "input[type='email']",
                "input[placeholder*='email' i]",
                "input[id*='email' i]",
                "input[class*='email' i]"
            ]
            
            email_filled = False
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    email_field.clear()
                    email_field.send_keys(CONFIG['email'])
                    self.logger.info("Email entered successfully")
                    email_filled = True
                    break
                except:
                    continue
            
            if not email_filled:
                self.logger.error("Could not fill email field")
                return False
            
            self.smart_delay()
            
            password_selectors = [
                f"input[name='{password_field_name}']",
                "input[type='password']",
                "input[placeholder*='password' i]",
                "input[placeholder*='pass' i]"
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    password_field.clear()
                    password_field.send_keys(CONFIG['password'])
                    self.logger.info("Password entered successfully")
                    password_filled = True
                    break
                except:
                    continue
            
            if not password_filled:
                return False
            
            self.smart_delay()
            
            login_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button",
                "input[value*='Login']",
                "input[value*='Sign']",
                "button[class*='login']",
                "button[class*='submit']"
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    login_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_btn.is_displayed() and login_btn.is_enabled():
                        login_btn.click()
                        self.logger.info("Login button clicked successfully")
                        login_clicked = True
                        break
                except:
                    continue
            
            if not login_clicked:
                try:
                    form_element = self.driver.find_element(By.CSS_SELECTOR, "form[name='login']")
                    form_element.submit()
                    self.logger.info("Form submitted successfully")
                    login_clicked = True
                except:
                    pass
            
            self.smart_delay()
            time.sleep(8)
            
            self.driver.get("https://adsha.re/surf")
            self.smart_delay()
            
            current_url = self.driver.current_url
            page_state = self.detect_page_state()
            
            if page_state == "GAME_ACTIVE" or page_state == "GAME_LOADING":
                self.logger.info("ULTIMATE LOGIN: Login successful!")
                self.state['is_logged_in'] = True
                self.send_telegram("✅ <b>ULTIMATE Login Successful!</b>")
                return True
            else:
                self.logger.error(f"Login failed - current state: {page_state}")
                self.send_telegram(f"❌ Login failed - state: {page_state}")
                return False
                
        except Exception as e:
            self.logger.error(f"Login error: {e}")
            self.send_telegram(f"❌ Login error: {str(e)}")
            return False

    # ==================== PERFECT SHAPE MATCHING SYSTEM v3.4 ====================
    def smart_delay(self):
        """Randomized delay between actions for anti-detection - EXACT SAME AS USERSCRIPT"""
        if CONFIG['random_delay']:
            delay = random.uniform(CONFIG['min_delay'], CONFIG['max_delay'])
            self.logger.info(f"⏰ Smart delay: {delay:.2f}s")
        else:
            delay = CONFIG['base_delay']
        time.sleep(delay)
        return delay

    def get_smart_delay(self):
        """Get intelligent delay with human-like patterns - EXACT SAME AS USERSCRIPT"""
        if not CONFIG['random_delay']:
            return CONFIG['base_delay']
        
        base = CONFIG['base_delay']
        random_variation = random.uniform(0, CONFIG['max_delay'] - CONFIG['min_delay'])
        return base + random_variation

    def is_behavior_suspicious(self):
        """Advanced rate limiting with behavioral analysis - EXACT SAME AS USERSCRIPT"""
        now = time.time()
        time_since_last_click = now - self.state['last_click_time']
        
        clicks_per_minute = (self.state['click_count'] / ((now - self.state['session_start_time']) / 60)) if (now - self.state['session_start_time']) > 0 else 0
        
        if clicks_per_minute > CONFIG['max_clicks_per_minute']:
            return True
        
        if now - self.state['session_start_time'] > 1800:  # 30 minutes
            return True
        
        return False

    def start_cooldown(self, duration=30000):
        """Cooldown management - EXACT SAME AS USERSCRIPT"""
        self.state['is_in_cooldown'] = True
        self.logger.info(f"😴 Cooldown activated for {duration/1000}s")
        
        def end_cooldown():
            time.sleep(duration / 1000)
            self.state['is_in_cooldown'] = False
            self.logger.info("✅ Cooldown ended")
        
        threading.Thread(target=end_cooldown, daemon=True).start()

    # ==================== EXACT USERSCRIPT v3.4 SYMBOL DETECTION ====================
    def classify_symbol_type(self, element):
        """EXACT SAME AS USERSCRIPT v3.4: Classify symbol type for both SVG and background images"""
        if not element:
            return self.SYMBOL_TYPES['UNKNOWN']
        
        try:
            # Check if it's a background image element - EXACT SAME LOGIC
            div = element.find_element(By.TAG_NAME, "div") if element else None
            if div:
                bg_image = div.value_of_css_property('background-image')
                if bg_image and 'img.gif' in bg_image:
                    return self.SYMBOL_TYPES['BACKGROUND_CIRCLE']
            
            # Check if it's an SVG element - EXACT SAME LOGIC
            svg = element.find_element(By.TAG_NAME, "svg") if element else None
            if not svg:
                return self.SYMBOL_TYPES['UNKNOWN']
            
            content = svg.get_attribute('innerHTML').lower()
            
            # Circle detection (concentric circles) - EXACT SAME LOGIC
            if 'circle' in content and 'cx="50"' in content and 'cy="50"' in content:
                circles = content.count('<circle')
                if circles >= 2:
                    return self.SYMBOL_TYPES['CIRCLE']
            
            # Square detection (nested squares) - EXACT SAME LOGIC
            if 'rect x="25" y="25"' in content and 'width="50" height="50"' in content:
                rects = content.count('<rect')
                if rects >= 2:
                    return self.SYMBOL_TYPES['SQUARE']
            
            # Diamond detection (rotated squares) - EXACT SAME LOGIC
            if 'transform="matrix(0.7071' in content and '42.4"' in content:
                return self.SYMBOL_TYPES['DIAMOND']
            
            # Arrow down detection (pointing down) - EXACT SAME LOGIC
            if 'polygon' in content and '25 75' in content and '50 25' in content and '75 75' in content:
                return self.SYMBOL_TYPES['ARROW_DOWN']
            
            # Arrow left detection (pointing left) - EXACT SAME LOGIC
            if 'polygon' in content and '25 25' in content and '75 50' in content and '25 75' in content:
                return self.SYMBOL_TYPES['ARROW_LEFT']
            
            return self.SYMBOL_TYPES['UNKNOWN']
            
        except Exception as e:
            return self.SYMBOL_TYPES['UNKNOWN']

    def compare_symbols(self, question_element, answer_element):
        """EXACT SAME AS USERSCRIPT v3.4: Enhanced symbol comparison with fuzzy matching"""
        try:
            question_svg = question_element.find_element(By.TAG_NAME, "svg")
            answer_svg = answer_element.find_element(By.TAG_NAME, "svg")
            
            question_content = question_svg.get_attribute('innerHTML').replace('\s+', ' ').strip()
            answer_content = answer_svg.get_attribute('innerHTML').replace('\s+', ' ').strip()
            
            # Clean content - EXACT SAME LOGIC
            clean_question = re.sub(r'fill:#[A-F0-9]+', '', question_content, flags=re.IGNORECASE)
            clean_question = re.sub(r'stroke:#[A-F0-9]+', '', clean_question, flags=re.IGNORECASE)
            clean_question = re.sub(r'style="[^"]*"', '', clean_question)
            clean_question = re.sub(r'class="[^"]*"', '', clean_question)
            
            clean_answer = re.sub(r'fill:#[A-F0-9]+', '', answer_content, flags=re.IGNORECASE)
            clean_answer = re.sub(r'stroke:#[A-F0-9]+', '', clean_answer, flags=re.IGNORECASE)
            clean_answer = re.sub(r'style="[^"]*"', '', clean_answer)
            clean_answer = re.sub(r'class="[^"]*"', '', clean_answer)
            
            # Exact match (preferred) - EXACT SAME LOGIC
            if clean_question == clean_answer:
                return {'match': True, 'confidence': 1.0, 'exact': True}
            
            # Fuzzy matching for similar symbols - EXACT SAME LOGIC
            similarity = self.calculate_similarity(clean_question, clean_answer)
            should_match = similarity > CONFIG['minimum_confidence']
            
            return {'match': should_match, 'confidence': similarity, 'exact': False}
            
        except Exception as e:
            return {'match': False, 'confidence': 0, 'exact': False}

    def calculate_similarity(self, str1, str2):
        """EXACT SAME AS USERSCRIPT v3.4: Calculate string similarity for fuzzy matching"""
        longer = str1 if len(str1) > len(str2) else str2
        shorter = str2 if len(str1) > len(str2) else str1
        
        if len(longer) == 0:
            return 1.0
        
        edit_distance = self.get_edit_distance(longer, shorter)
        return (len(longer) - edit_distance) / float(len(longer))

    def get_edit_distance(self, a, b):
        """EXACT SAME AS USERSCRIPT v3.4: Levenshtein distance for edit distance calculation"""
        if len(a) == 0:
            return len(b)
        if len(b) == 0:
            return len(a)
        
        matrix = []
        for i in range(len(b) + 1):
            matrix.append([i])
        for j in range(len(a) + 1):
            matrix[0].append(j)
        
        for i in range(1, len(b) + 1):
            for j in range(1, len(a) + 1):
                if b[i-1] == a[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = min(
                        matrix[i-1][j-1] + 1,
                        matrix[i][j-1] + 1,
                        matrix[i-1][j] + 1
                    )
        
        return matrix[len(b)][len(a)]

    def find_best_match_v3_4(self, question_element, links):
        """EXACT SAME AS USERSCRIPT v3.4: Find the BEST possible match with high confidence"""
        best_match = None
        highest_confidence = 0
        exact_matches = []
        
        question_type = self.classify_symbol_type(question_element)
        
        for link in links:
            answer_type = self.classify_symbol_type(link)
            
            # CASE 1: Both question and answer are SVGs - use traditional matching
            try:
                question_svg = question_element.find_element(By.TAG_NAME, "svg")
                answer_svg = link.find_element(By.TAG_NAME, "svg")
                
                if question_svg and answer_svg:
                    comparison = self.compare_symbols(question_element, link)
                    if comparison['exact'] and comparison['match']:
                        exact_matches.append({
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': True,
                            'matchType': 'svg_exact'
                        })
                    elif comparison['match'] and comparison['confidence'] > highest_confidence:
                        highest_confidence = comparison['confidence']
                        best_match = {
                            'link': link,
                            'confidence': comparison['confidence'],
                            'exact': False,
                            'matchType': 'svg_fuzzy'
                        }
            except:
                pass
            
            # CASE 2: Question is SVG, Answer is Background Image
            try:
                question_svg = question_element.find_element(By.TAG_NAME, "svg")
                if question_svg and answer_type == self.SYMBOL_TYPES['BACKGROUND_CIRCLE']:
                    # Background images are always circles - match if question is also a circle
                    if question_type == self.SYMBOL_TYPES['CIRCLE']:
                        confidence = 0.98
                        if confidence > highest_confidence:
                            highest_confidence = confidence
                            best_match = {
                                'link': link,
                                'confidence': confidence,
                                'exact': True,
                                'matchType': 'svg_to_background'
                            }
            except:
                pass
            
            # CASE 3: Question is Background Image, Answer is Background Image
            if question_type == self.SYMBOL_TYPES['BACKGROUND_CIRCLE'] and answer_type == self.SYMBOL_TYPES['BACKGROUND_CIRCLE']:
                confidence = 1.0
                exact_matches.append({
                    'link': link,
                    'confidence': confidence,
                    'exact': True,
                    'matchType': 'background_to_background'
                })
            
            # CASE 4: Question is Background Image, Answer is SVG
            if question_type == self.SYMBOL_TYPES['BACKGROUND_CIRCLE']:
                try:
                    answer_svg = link.find_element(By.TAG_NAME, "svg")
                    if answer_svg and answer_type == self.SYMBOL_TYPES['CIRCLE']:
                        confidence = 0.98
                        if confidence > highest_confidence:
                            highest_confidence = confidence
                            best_match = {
                                'link': link,
                                'confidence': confidence,
                                'exact': True,
                                'matchType': 'background_to_svg'
                            }
                except:
                    pass

        # Return exact match if available
        if exact_matches:
            return exact_matches[0]

        # Return best match if confidence is high enough
        if best_match and best_match['confidence'] >= CONFIG['minimum_confidence']:
            return best_match

        return None

    def safe_click_v3_4(self, element):
        """EXACT SAME AS USERSCRIPT v3.4: SAFE CLICK with anti-detection"""
        try:
            if self.is_behavior_suspicious() or self.state['is_in_cooldown']:
                self.logger.info("⏳ Safety cooldown active")
                return False
            
            # Add random delay before clicking (anti-detection)
            click_delay = random.uniform(0.5, 1.5)
            self.logger.info(f"⏰ Pre-click delay: {click_delay:.2f}s")
            time.sleep(click_delay)
            
            element.click()
            self.logger.info("✅ Click executed successfully!")
            
            self.state['click_count'] += 1
            self.state['last_click_time'] = time.time()
            self.state['last_action_time'] = time.time()
            
            return True
            
        except StaleElementReferenceException:
            self.logger.info("🔄 Element went stale during click - refreshing page")
            self.driver.get("https://adsha.re/surf")
            time.sleep(3)
            return False
        except Exception as e:
            self.logger.error(f"Click error: {e}")
            return False

    def find_question_element_v3_4(self):
        """EXACT SAME AS USERSCRIPT v3.4: Find question element (SVG or background image)"""
        try:
            # First try to find SVG element
            svg_elements = self.driver.find_elements(By.TAG_NAME, "svg")
            for svg in svg_elements:
                # Check if this SVG is the question (contains gray #808080)
                svg_html = svg.get_attribute('innerHTML')
                if svg_html and '#808080' in svg_html:
                    # Return the parent div or the SVG itself
                    parent = svg.find_element(By.XPATH, "./..")
                    if parent:
                        return parent
                    return svg
            
            # If no SVG found, look for background image elements
            divs = self.driver.find_elements(By.TAG_NAME, "div")
            for div in divs:
                bg_image = div.value_of_css_property('background-image')
                if bg_image and 'img.gif' in bg_image:
                    return div
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding question element: {e}")
            return None

    def solve_symbol_game_v3_4(self):
        """EXACT SAME AS USERSCRIPT v3.4: Main game solving with PERFECT accuracy"""
        if not self.state['is_running'] or self.state['is_in_cooldown']:
            return False
        
        try:
            # Occasionally take breaks - EXACT SAME LOGIC
            if self.state['consecutive_rounds'] > 15 and random.random() < 0.3:
                self.logger.info("💤 Taking a short break...")
                self.start_cooldown(10000 + random.randint(0, 20000))
                self.state['consecutive_rounds'] = 0
                return False
            
            # Find the question element (could be SVG or background image)
            question_element = self.find_question_element_v3_4()
            
            if not question_element:
                self.state['no_question_count'] += 1
                self.logger.info(f"❌ No question element found (SVG or background) - Count: {self.state['no_question_count']}")
                
                # Refresh page if no question found 3 times in a row
                if self.state['no_question_count'] >= 3:
                    self.logger.info("🔄 No question found 3 times - refreshing page...")
                    self.driver.get("https://adsha.re/surf")
                    WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    self.smart_delay()
                    self.state['no_question_count'] = 0
                return False
            
            # Reset counter when question is found
            self.state['no_question_count'] = 0
            
            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='adsha.re'], a[href*='symbol-matching-game']")
            
            # Find the best possible match with high confidence
            best_match = self.find_best_match_v3_4(question_element, links)
            
            if best_match:
                question_type = self.classify_symbol_type(question_element)
                self.logger.info(f"🎯 Question detected! Type: {question_type}")
                
                if self.safe_click_v3_4(best_match['link']):
                    self.state['total_solved'] += 1
                    self.state['consecutive_rounds'] += 1
                    self.state['consecutive_fails'] = 0
                    self.state['consecutive_match_fails'] = 0
                    
                    self.update_performance_metrics()
                    
                    match_type = "EXACT" if best_match['exact'] else "FUZZY"
                    source = best_match.get('matchType', 'UNKNOWN')
                    self.logger.info(f"✅ {match_type} Match! ({source}) Confidence: {(best_match['confidence'] * 100):.1f}% | Total: {self.state['total_solved']}")
                    
                    return True
            else:
                # No good match found - wait and retry
                self.state['consecutive_match_fails'] += 1
                question_type = self.classify_symbol_type(question_element)
                
                background_answers = sum(1 for link in links if self.classify_symbol_type(link) == self.SYMBOL_TYPES['BACKGROUND_CIRCLE'])
                svg_answers = sum(1 for link in links if self.has_svg(link))
                
                self.logger.info(f"🔍 No high-confidence match found. Question: {question_type}, SVG answers: {svg_answers}, Image answers: {background_answers}")
                
                # If multiple consecutive fails, take longer break
                if self.state['consecutive_match_fails'] > 3:
                    self.logger.info("⚠️ Multiple match fails detected, extended cooldown")
                    self.start_cooldown(15000)
                    self.state['consecutive_match_fails'] = 0
                
                return False
                
        except Exception as e:
            self.logger.error(f"Solver error: {e}")
            self.state['consecutive_fails'] += 1
            self.state['consecutive_match_fails'] += 1
            return False

    def has_svg(self, element):
        """Check if element contains SVG"""
        try:
            element.find_element(By.TAG_NAME, "svg")
            return True
        except:
            return False

    # ==================== PAGE STATE DETECTION ====================
    def detect_page_state(self):
        """ULTRA-RELIABLE page state detection"""
        try:
            if not self.is_browser_alive():
                return "BROWSER_DEAD"
            
            current_url = self.driver.current_url.lower()
            page_source = self.driver.page_source.lower()

            if "adsha.re/login" in current_url or "login" in current_url or "signin" in current_url:
                self.state['is_logged_in'] = False
                return "LOGIN_REQUIRED"
            elif "adsha.re/exchange" in current_url:
                return "WRONG_CLICK_REDIRECT"
            elif "surf" in current_url and ("svg" in page_source or "img.gif" in page_source):
                return "GAME_ACTIVE"
            elif "surf" in current_url:
                return "GAME_LOADING"
            elif "adsha.re" in current_url and "surf" not in current_url:
                return "WRONG_PAGE"
            elif "404" in page_source or "not found" in page_source:
                return "PAGE_NOT_FOUND"
            elif "maintenance" in page_source or "offline" in page_source:
                return "MAINTENANCE_MODE"
            else:
                return "UNKNOWN_PAGE"
                
        except Exception as e:
            self.logger.error(f"Page state detection error: {e}")
            return "BROWSER_DEAD"

    def ensure_correct_page(self):
        """ENHANCED page correction"""
        if not self.is_browser_alive():
            self.logger.error("Browser dead during page check")
            return False
            
        try:
            page_state = self.detect_page_state()
            
            if page_state == "BROWSER_DEAD":
                self.logger.error("Browser confirmed dead - restarting...")
                return self.restart_browser()
            elif page_state == "LOGIN_REQUIRED":
                self.logger.info("Login required - forcing login...")
                self.state['is_logged_in'] = False
                if self.force_login():
                    self.state['is_logged_in'] = True
                    return True
                return False
            elif page_state == "GAME_ACTIVE":
                return True
            elif page_state == "GAME_LOADING":
                self.logger.info("Game loading - waiting...")
                time.sleep(5)
                return self.ensure_correct_page()
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

    # ==================== PERFORMANCE TRACKING ====================
    def update_performance_metrics(self):
        """Update performance tracking metrics"""
        current_time = time.time()
        metrics = self.state['performance_metrics']
        
        if metrics['start_time'] == 0:
            metrics['start_time'] = current_time
            metrics['last_hour_count'] = 0
        
        hours_running = (current_time - metrics['start_time']) / 3600
        if hours_running > 0:
            metrics['games_per_hour'] = self.state['total_solved'] / hours_running
        
        metrics['last_hour_count'] += 1

    # ==================== SIMPLIFIED LEADERBOARD ====================
    def parse_leaderboard(self):
        """SIMPLIFIED leaderboard - will fix later"""
        try:
            if not self.is_browser_alive() or not self.state['is_logged_in']:
                self.logger.info("Browser not ready for leaderboard")
                return None
            
            self.logger.info("⏳ Leaderboard parsing disabled for now")
            return []
            
        except Exception as e:
            self.logger.info(f"Leaderboard temporarily disabled: {e}")
            return None

    def leaderboard_monitor(self):
        """Simplified leaderboard monitoring"""
        self.logger.info("Starting leaderboard monitoring...")
        
        while self.state['is_running']:
            try:
                # Just sleep, leaderboard disabled for now
                for _ in range(CONFIG['leaderboard_check_interval']):
                    if not self.state['is_running']:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.logger.error(f"Leaderboard monitoring error: {e}")
                time.sleep(300)

    # ==================== SMART FAILURE HANDLING ====================
    def handle_consecutive_failures(self):
        """SMART failure handling"""
        current_fails = self.state['consecutive_fails']
        
        if not self.is_browser_alive():
            self.logger.error("Browser dead - restarting with login...")
            self.send_telegram("🔄 Browser dead - restarting with fresh login...")
            if self.restart_browser():
                self.state['consecutive_fails'] = 0
                self.state['element_not_found_count'] = 0
                self.state['no_question_count'] = 0
            return
        
        if current_fails >= CONFIG['restart_after_failures']:
            self.logger.warning("Multiple consecutive failures - restarting browser...")
            self.send_telegram("🔄 Multiple failures - restarting browser...")
            if self.restart_browser():
                self.state['consecutive_fails'] = 0
                self.state['element_not_found_count'] = 0
                self.state['no_question_count'] = 0
        
        elif current_fails >= CONFIG['max_consecutive_failures']:
            self.logger.error("CRITICAL: Too many failures! Stopping...")
            self.send_telegram("🚨 CRITICAL ERROR - Too many consecutive failures - Stopping solver")
            self.stop()

    # ==================== ULTIMATE SOLVER LOOP v3.4 ====================
    def solver_loop_v3_4(self):
        """PERFECT SHAPE MATCHING solving loop v3.4"""
        self.logger.info("Starting PERFECT SHAPE MATCHING solver v3.4...")
        self.state['status'] = 'running'
        self.state['performance_metrics']['start_time'] = time.time()
        self.state['session_start_time'] = time.time()
        self.state['last_action_time'] = time.time()
        
        if not self.driver:
            if not self.setup_firefox():
                self.logger.error("CRITICAL: Cannot start - Firefox failed")
                self.stop()
                return
        
        if not self.force_login():
            self.logger.error("CRITICAL: Initial login failed")
            self.stop()
            return
        
        cycle_count = 0
        
        while self.state['is_running'] and self.state['consecutive_fails'] < CONFIG['max_consecutive_failures']:
            try:
                if cycle_count % 50 == 0:
                    gc.collect()
                
                if cycle_count % 100 == 0:
                    self.logger.info(f"Performance: {self.state['total_solved']} games solved | {self.state['performance_metrics']['games_per_hour']:.1f} games/hour")
                
                if not self.ensure_correct_page():
                    self.logger.error("Cannot ensure correct page status")
                    self.state['consecutive_fails'] += 1
                    continue
                
                game_solved = self.solve_symbol_game_v3_4()
                
                if not game_solved:
                    self.handle_consecutive_failures()
                    # Random delay between attempts for anti-detection
                    retry_delay = random.uniform(2, 5)
                    time.sleep(retry_delay)
                
                cycle_count += 1
                    
            except Exception as e:
                self.logger.error(f"Loop error: {e}")
                self.state['consecutive_fails'] += 1
                time.sleep(10)
        
        if self.state['consecutive_fails'] >= CONFIG['max_consecutive_failures']:
            self.logger.error("CRITICAL: Too many failures, stopping...")
            self.stop()

    # ==================== ENHANCED CONTROL METHODS ====================
    def start(self):
        """Enhanced solver start"""
        if self.state['is_running']:
            return "❌ Solver already running"
        
        self.state['is_running'] = True
        self.state['consecutive_fails'] = 0
        self.state['element_not_found_count'] = 0
        self.state['wrong_click_count'] = 0
        self.state['no_question_count'] = 0
        self.state['click_count'] = 0
        self.state['consecutive_rounds'] = 0
        self.state['consecutive_match_fails'] = 0
        self.state['is_in_cooldown'] = False
        self.state['performance_metrics']['start_time'] = time.time()
        self.state['session_start_time'] = time.time()
        self.state['last_action_time'] = time.time()
        
        self.solver_thread = threading.Thread(target=self.solver_loop_v3_4)
        self.solver_thread.daemon = True
        self.solver_thread.start()
        
        self.monitoring_thread = threading.Thread(target=self.leaderboard_monitor)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        self.logger.info("PERFECT SHAPE MATCHING solver v3.4 started!")
        self.send_telegram("🚀 <b>PERFECT SHAPE MATCHING Solver v3.4 Started!</b>")
        return "✅ PERFECT SHAPE MATCHING Solver v3.4 started successfully!"

    def stop(self):
        """Enhanced solver stop"""
        self.state['is_running'] = False
        self.state['status'] = 'stopped'
        
        if self.state['performance_metrics']['start_time'] > 0:
            total_time = time.time() - self.state['performance_metrics']['start_time']
            games_per_hour = self.state['total_solved'] / (total_time / 3600) if total_time > 0 else 0
            self.state['performance_metrics']['games_per_hour'] = games_per_hour
        
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        self.logger.info("PERFECT SHAPE MATCHING solver stopped")
        self.send_telegram("🛑 <b>PERFECT SHAPE MATCHING Solver Stopped!</b>")
        return "✅ PERFECT SHAPE MATCHING Solver stopped successfully!"

    def status(self):
        """Enhanced status with all features"""
        status_text = f"""
📊 <b>PERFECT SHAPE MATCHING SOLVER v3.4 STATUS</b>
⏰ {self.get_ist_time()}
🔄 Status: {self.state['status']}
🎮 Games Solved: {self.state['total_solved']}
🔐 Logged In: {'✅' if self.state['is_logged_in'] else '❌'}
⚠️ Fails: {self.state['consecutive_fails']}/{CONFIG['max_consecutive_failures']}
🚨 Wrong Clicks: {self.state['wrong_click_count']}
"""
        
        # Performance metrics
        metrics = self.state['performance_metrics']
        if metrics['start_time'] > 0:
            running_time = self.format_running_time()
            hours_running = (time.time() - metrics['start_time']) / 3600
            games_per_hour = self.state['total_solved'] / hours_running if hours_running > 0 else 0
            
            status_text += f"""
📈 <b>PERFORMANCE METRICS</b>
⚡ Games/Hour: {games_per_hour:.1f}
🕒 Running Time: {running_time}
📊 Total Cycles: {self.state['total_solved']}
"""
        
        return status_text

    def format_running_time(self):
        """Format running time for display"""
        if self.state['performance_metrics']['start_time'] == 0:
            return "0h 0m"
        
        seconds = time.time() - self.state['performance_metrics']['start_time']
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

# ==================== ULTIMATE TELEGRAM BOT ====================
class UltimateTelegramBot:
    def __init__(self):
        self.solver = UltimateShapeSolver()
        self.logger = logging.getLogger(__name__)
        self.last_update_id = 0
    
    def get_telegram_updates(self):
        """Enhanced Telegram updates"""
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
        """Enhanced message processing"""
        if 'message' not in update:
            return
        
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')
        
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
                response = "🎯 Target setting disabled in v3.4"
            else:
                response = "Usage: /target disabled in v3.4"
        elif text.startswith('/compete'):
            response = "🏆 Compete mode disabled in v3.4"
        elif text.startswith('/leaderboard'):
            response = "⏳ Leaderboard temporarily disabled - focusing on v3.4 solving"
        elif text.startswith('/login'):
            response = "🔐 Attempting login..." if self.solver.force_login() else "❌ Login failed"
        elif text.startswith('/performance'):
            response = self.solver.status()
        elif text.startswith('/restart'):
            response = "🔄 Restarting browser..." if self.solver.restart_browser() else "❌ Restart failed"
        elif text.startswith('/wrongclicks'):
            response = f"🚨 Total wrong clicks: {self.solver.state['wrong_click_count']}"
        elif text.startswith('/help'):
            response = """
🤖 <b>PERFECT SHAPE MATCHING AdShare Solver v3.4</b>

<b>EXACT SAME LOGIC AS USERSCRIPT v3.4</b>
✅ Perfect accuracy with background image support
✅ All symbol types: circles, squares, diamonds, arrows
✅ Background image matching enabled
✅ Anti-detection delays and cooldowns
✅ Auto-refresh on stuck pages

<b>Basic Commands:</b>
/start - Start solver
/stop - Stop solver  
/status - Status with performance
/screenshot - Get screenshot
/login - Force login
/restart - Restart browser
/wrongclicks - Show wrong click count

<b>v3.4 FEATURES:</b>
🎯 EXACT same logic as userscript v3.4
🖼️ Background image support
🔍 Enhanced symbol classification  
⚡ Perfect accuracy mode
🛡️ Anti-detection features

<b>Note:</b> Target and compete modes disabled to focus on perfect solving
"""
        
        if response:
            self.solver.send_telegram(response)
    
    def handle_updates(self):
        """Enhanced update handling"""
        self.logger.info("Starting PERFECT SHAPE MATCHING Telegram bot v3.4...")
        
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
    bot = UltimateTelegramBot()
    bot.logger.info("PERFECT SHAPE MATCHING AdShare Solver v3.4 - EXACT SAME LOGIC AS USERSCRIPT started!")
    bot.handle_updates()
